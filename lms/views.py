from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from .email_utils import send_platform_email
from .forms import (
    CheckoutForm,
    CouponForm,
    LoginForm,
    ReviewForm,
    RoadmapForm,
    SignupForm,
    apply_coupon,
)
from .models import (
    ActivityLog,
    Category,
    Choice,
    Course,
    Enrollment,
    Lesson,
    Module,
    Progress,
    Quiz,
    QuizAttempt,
    Review,
    Transaction,
)


def home(request):
    categories = Category.objects.annotate(course_count=Count("courses")).order_by("order")
    featured = Course.objects.filter(is_published=True, is_featured=True)[:4]
    resume = None
    stats = None
    deadlines = []
    if request.user.is_authenticated:
        enrollments = (
            Enrollment.objects.filter(user=request.user, status=Enrollment.Status.ACTIVE)
            .select_related("course", "last_lesson", "last_lesson__module")
        )
        active = list(enrollments)
        if active:
            resume_enrollment = next((e for e in active if e.last_lesson_id), active[0])
            resume = resume_enrollment
        quiz_avg = (
            QuizAttempt.objects.filter(user=request.user, submitted_at__isnull=False)
            .aggregate(avg=Avg("score"))["avg"]
            or 0
        )
        stats = {
            "in_progress": len(active),
            "avg_quiz": int(round(quiz_avg)),
            "plan": "Pro" if active else "Free",
        }
        deadlines = (
            Enrollment.objects.filter(
                user=request.user,
                deadline__isnull=False,
                deadline__gte=timezone.now(),
            )
            .select_related("course")
            .order_by("deadline")[:5]
        )
    return render(
        request,
        "lms/home.html",
        {
            "categories": categories,
            "featured": featured,
            "resume": resume,
            "stats": stats,
            "deadlines": deadlines,
            "roadmap_form": RoadmapForm(),
        },
    )


def catalog(request):
    qs = Course.objects.filter(is_published=True).select_related("category", "instructor")
    category_slug = request.GET.get("category", "")
    level = request.GET.get("level", "")
    topic = request.GET.get("topic", "")
    duration = request.GET.get("duration", "")
    q = request.GET.get("q", "").strip()

    if category_slug:
        qs = qs.filter(category__slug=category_slug)
    if level:
        qs = qs.filter(level=level)
    if topic:
        qs = qs.filter(topic__icontains=topic)
    if duration:
        qs = qs.filter(duration_band=duration)
    if q:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(short_description__icontains=q)
            | Q(topic__icontains=q)
            | Q(code__icontains=q)
        )

    topics = (
        Course.objects.filter(is_published=True)
        .exclude(topic="")
        .values_list("topic", flat=True)
        .distinct()
        .order_by("topic")
    )
    category = None
    if category_slug:
        category = Category.objects.filter(slug=category_slug).first()

    paginator = Paginator(qs, settings.COURSES_PER_PAGE)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "lms/catalog.html",
        {
            "page_obj": page,
            "categories": Category.objects.all(),
            "topics": topics,
            "selected": {
                "category": category_slug,
                "level": level,
                "topic": topic,
                "duration": duration,
                "q": q,
            },
            "category": category,
            "levels": Course.Level.choices,
            "durations": Course.DurationBand.choices,
        },
    )


def course_detail(request, slug):
    course = get_object_or_404(
        Course.objects.select_related("category", "instructor").prefetch_related(
            "modules__lessons", "reviews__user"
        ),
        slug=slug,
        is_published=True,
    )
    enrolled = False
    if request.user.is_authenticated:
        enrolled = Enrollment.objects.filter(
            user=request.user,
            course=course,
            status__in=[Enrollment.Status.ACTIVE, Enrollment.Status.COMPLETED],
        ).exists()

    review_form = ReviewForm()
    if request.method == "POST" and request.user.is_authenticated and enrolled:
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            review, _ = Review.objects.update_or_create(
                course=course,
                user=request.user,
                defaults=review_form.cleaned_data,
            )
            messages.success(request, "Thanks for your review.")
            return redirect(course.get_absolute_url())

    avg, count = course.average_rating
    return render(
        request,
        "lms/course_detail.html",
        {
            "course": course,
            "enrolled": enrolled,
            "avg_rating": avg,
            "review_count": count,
            "review_form": review_form,
            "modules": course.modules.all(),
        },
    )


@login_required
def checkout(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    if Enrollment.objects.filter(
        user=request.user,
        course=course,
        status__in=[Enrollment.Status.ACTIVE, Enrollment.Status.COMPLETED],
    ).exists():
        messages.info(request, "You are already enrolled.")
        return redirect("lms:player_start", course_slug=course.slug)

    price = course.price
    discount = Decimal("0.00")
    coupon = None
    coupon_message = ""

    if request.method == "POST":
        action = request.POST.get("action", "purchase")
        if action == "apply_coupon":
            form = CheckoutForm(request.POST)
            coupon_form = CouponForm(request.POST)
            if coupon_form.is_valid():
                coupon, discount, coupon_message = apply_coupon(
                    coupon_form.cleaned_data.get("code", ""), price
                )
            form = CheckoutForm(
                initial={
                    "method": request.POST.get("method", Transaction.Method.BKASH),
                    "coupon_code": request.POST.get("code", ""),
                }
            )
        else:
            form = CheckoutForm(request.POST)
            if form.is_valid():
                coupon, discount, coupon_message = apply_coupon(
                    form.cleaned_data.get("coupon_code", ""), price
                )
                total = price - discount
                method = form.cleaned_data["method"]
                if total <= 0:
                    Enrollment.objects.update_or_create(
                        user=request.user,
                        course=course,
                        defaults={"status": Enrollment.Status.ACTIVE},
                    )
                    ActivityLog.objects.create(
                        user=request.user,
                        message=f"Enrolled in '{course.title}' (free / 100% coupon)",
                    )
                    messages.success(request, f"You're enrolled in {course.title}!")
                    return redirect("lms:player_start", course_slug=course.slug)

                txn = Transaction.objects.create(
                    user=request.user,
                    course=course,
                    amount=total,
                    discount=discount,
                    coupon=coupon,
                    method=method,
                    status=Transaction.Status.PENDING,
                    bkash_trx_id=form.cleaned_data.get("bkash_trx_id", ""),
                    bkash_sender=form.cleaned_data.get("bkash_sender", ""),
                    notes="Awaiting manual verification"
                    if method == Transaction.Method.BKASH
                    else "Demo non-bKash checkout — pending admin approval",
                )
                Enrollment.objects.update_or_create(
                    user=request.user,
                    course=course,
                    defaults={"status": Enrollment.Status.PENDING},
                )
                send_platform_email(
                    request.user.email or "student@example.com",
                    f"Payment received — {course.title}",
                    f"<p>We received your payment request for <strong>{course.title}</strong> "
                    f"(৳{total}). Status: pending verification.</p>",
                    f"Payment received for {course.title}. Amount: {total}. Pending verification.",
                )
                ActivityLog.objects.create(
                    user=request.user,
                    message=f"Checkout submitted for '{course.title}' via {method}",
                )
                messages.success(
                    request,
                    "Payment submitted. Access unlocks after admin verifies your bKash transfer.",
                )
                return redirect("lms:checkout_status", txn_id=txn.pk)
            coupon, discount, coupon_message = apply_coupon(
                form.data.get("coupon_code", ""), price
            )
    else:
        form = CheckoutForm(initial={"method": Transaction.Method.BKASH})
        coupon_form = CouponForm()

    if "coupon_form" not in locals():
        coupon_form = CouponForm(initial={"code": form.initial.get("coupon_code", "")})

    return render(
        request,
        "lms/checkout.html",
        {
            "course": course,
            "form": form,
            "coupon_form": coupon_form,
            "price": price,
            "discount": discount,
            "total": price - discount,
            "coupon": coupon,
            "coupon_message": coupon_message,
        },
    )


@login_required
def checkout_status(request, txn_id):
    txn = get_object_or_404(Transaction, pk=txn_id, user=request.user)
    return render(request, "lms/checkout_status.html", {"txn": txn})


@login_required
def dashboard(request):
    enrollments = (
        Enrollment.objects.filter(user=request.user)
        .exclude(status=Enrollment.Status.CANCELLED)
        .select_related("course", "last_lesson")
    )
    active = [e for e in enrollments if e.status == Enrollment.Status.ACTIVE]
    pending = [e for e in enrollments if e.status == Enrollment.Status.PENDING]
    recommended = (
        Course.objects.filter(is_published=True)
        .exclude(enrollments__user=request.user)
        .order_by("-is_featured", "?")[:4]
    )
    activities = ActivityLog.objects.filter(user=request.user)[:8]
    attempts = QuizAttempt.objects.filter(user=request.user, submitted_at__isnull=False)[:5]
    return render(
        request,
        "lms/dashboard.html",
        {
            "enrollments": active,
            "pending": pending,
            "recommended": recommended,
            "activities": activities,
            "attempts": attempts,
        },
    )


@login_required
def player_start(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    enrollment = get_object_or_404(
        Enrollment,
        user=request.user,
        course=course,
        status__in=[Enrollment.Status.ACTIVE, Enrollment.Status.COMPLETED],
    )
    lesson = enrollment.last_lesson
    if not lesson:
        lesson = (
            Lesson.objects.filter(module__course=course)
            .order_by("module__order", "order")
            .first()
        )
    if not lesson:
        messages.warning(request, "This course has no lessons yet.")
        return redirect(course.get_absolute_url())
    return redirect("lms:player", course_slug=course.slug, lesson_id=lesson.pk)


@login_required
def player(request, course_slug, lesson_id):
    course = get_object_or_404(Course, slug=course_slug)
    enrollment = Enrollment.objects.filter(
        user=request.user,
        course=course,
        status__in=[Enrollment.Status.ACTIVE, Enrollment.Status.COMPLETED],
    ).first()
    if not enrollment:
        messages.warning(request, "Enroll to access the course player.")
        return redirect("lms:checkout", slug=course.slug)

    lesson = get_object_or_404(Lesson, pk=lesson_id, module__course=course)
    modules = course.modules.prefetch_related("lessons", "quiz").all()
    completed_ids = set(
        Progress.objects.filter(
            user=request.user, lesson__module__course=course, completed=True
        ).values_list("lesson_id", flat=True)
    )
    enrollment.last_lesson = lesson
    enrollment.save(update_fields=["last_lesson"])

    Progress.objects.get_or_create(user=request.user, lesson=lesson)

    next_lesson = (
        Lesson.objects.filter(module__course=course)
        .filter(
            Q(module__order__gt=lesson.module.order)
            | Q(module=lesson.module, order__gt=lesson.order)
        )
        .order_by("module__order", "order")
        .first()
    )
    prev_lesson = (
        Lesson.objects.filter(module__course=course)
        .filter(
            Q(module__order__lt=lesson.module.order)
            | Q(module=lesson.module, order__lt=lesson.order)
        )
        .order_by("-module__order", "-order")
        .first()
    )

    return render(
        request,
        "lms/player.html",
        {
            "course": course,
            "lesson": lesson,
            "modules": modules,
            "completed_ids": completed_ids,
            "enrollment": enrollment,
            "progress_percent": enrollment.progress_percent(),
            "next_lesson": next_lesson,
            "prev_lesson": prev_lesson,
        },
    )


@login_required
@require_POST
def mark_complete(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    enrollment = Enrollment.objects.filter(
        user=request.user,
        course=lesson.module.course,
        status__in=[Enrollment.Status.ACTIVE, Enrollment.Status.COMPLETED],
    ).first()
    if not enrollment:
        raise Http404
    progress, _ = Progress.objects.get_or_create(user=request.user, lesson=lesson)
    progress.completed = True
    progress.save(update_fields=["completed", "updated_at"])
    ActivityLog.objects.create(
        user=request.user,
        message=f"Completed lesson: {lesson.title}",
    )
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "progress": enrollment.progress_percent()})
    messages.success(request, "Lesson marked complete.")
    next_lesson = (
        Lesson.objects.filter(module__course=lesson.module.course)
        .filter(
            Q(module__order__gt=lesson.module.order)
            | Q(module=lesson.module, order__gt=lesson.order)
        )
        .order_by("module__order", "order")
        .first()
    )
    if next_lesson:
        return redirect(next_lesson.get_absolute_url())
    return redirect("lms:player", course_slug=lesson.module.course.slug, lesson_id=lesson.pk)


@login_required
def quiz_take(request, quiz_id):
    quiz = get_object_or_404(
        Quiz.objects.select_related("module__course").prefetch_related(
            "questions__choices"
        ),
        pk=quiz_id,
    )
    course = quiz.module.course
    if not Enrollment.objects.filter(
        user=request.user,
        course=course,
        status__in=[Enrollment.Status.ACTIVE, Enrollment.Status.COMPLETED],
    ).exists():
        messages.warning(request, "Enroll to take quizzes.")
        return redirect("lms:checkout", slug=course.slug)

    questions = list(quiz.questions.all())
    if request.method == "POST":
        answers = {}
        correct = 0
        total_points = 0
        for question in questions:
            total_points += question.points
            raw = request.POST.get(f"q_{question.pk}")
            answers[str(question.pk)] = raw
            if raw:
                try:
                    choice = Choice.objects.get(pk=int(raw), question=question)
                    if choice.is_correct:
                        correct += question.points
                except (Choice.DoesNotExist, ValueError):
                    pass
        score = int(round(100 * correct / total_points)) if total_points else 0
        passed = score >= quiz.pass_score
        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            score=score,
            passed=passed,
            submitted_at=timezone.now(),
            answers=answers,
        )
        ActivityLog.objects.create(
            user=request.user,
            message=f"Completed quiz '{quiz.title}' with {score}%",
        )
        return render(
            request,
            "lms/quiz_result.html",
            {"quiz": quiz, "attempt": attempt, "course": course},
        )

    attempt = QuizAttempt.objects.create(user=request.user, quiz=quiz)
    deadline = attempt.started_at + timedelta(minutes=quiz.time_limit_minutes)
    return render(
        request,
        "lms/quiz.html",
        {
            "quiz": quiz,
            "questions": questions,
            "course": course,
            "attempt": attempt,
            "deadline_iso": deadline.isoformat(),
            "time_limit_seconds": quiz.time_limit_minutes * 60,
        },
    )


@login_required
def quizzes_list(request):
    enrollments = Enrollment.objects.filter(
        user=request.user,
        status__in=[Enrollment.Status.ACTIVE, Enrollment.Status.COMPLETED],
    ).values_list("course_id", flat=True)
    quizzes = (
        Quiz.objects.filter(module__course_id__in=enrollments)
        .select_related("module__course")
        .order_by("module__course__title", "module__order")
    )
    return render(request, "lms/quizzes.html", {"quizzes": quizzes})


def roadmap(request):
    form = RoadmapForm(request.GET or None)
    path = []
    if form.is_valid():
        level = form.cleaned_data["current_level"]
        interest = form.cleaned_data["interest"]
        level_map = {
            "secondary": "Secondary School",
            "hsc": "Higher Secondary",
            "cse": "CSE",
            "eee": "EEE",
        }
        cat_name = level_map.get(level, "")
        qs = Course.objects.filter(is_published=True)
        if cat_name:
            qs = qs.filter(category__name__icontains=cat_name.split()[0])
        if interest == "programming":
            qs = Course.objects.filter(is_published=True).filter(
                Q(topic__icontains="Python")
                | Q(topic__icontains="AI")
                | Q(category__name__icontains="CSE")
            )
        elif interest == "circuits":
            qs = Course.objects.filter(is_published=True, category__name__icontains="EEE")
        elif interest == "math":
            qs = Course.objects.filter(is_published=True).filter(
                Q(topic__icontains="Math") | Q(topic__icontains="Physics")
            )
        path = list(qs.distinct().select_related("category")[:8])

        if request.user.is_authenticated:
            profile = getattr(request.user, "profile", None)
            if profile:
                profile.current_level = level
                profile.interest = interest
                profile.save(update_fields=["current_level", "interest"])

    enrolled_ids = set()
    completed_ids = set()
    if request.user.is_authenticated:
        for e in Enrollment.objects.filter(user=request.user).select_related("course"):
            enrolled_ids.add(e.course_id)
            if e.status == Enrollment.Status.COMPLETED or e.progress_percent() >= 100:
                completed_ids.add(e.course_id)

    all_courses = Course.objects.filter(is_published=True).select_related("category")[:12]
    return render(
        request,
        "lms/roadmap.html",
        {
            "form": form or RoadmapForm(),
            "path": path,
            "all_courses": all_courses,
            "enrolled_ids": enrolled_ids,
            "completed_ids": completed_ids,
        },
    )


class StudentLoginView(LoginView):
    template_name = "accounts/auth.html"
    authentication_form = LoginForm
    extra_context = {"auth_mode": "login"}

    def get_success_url(self):
        return self.get_redirect_url() or reverse_lazy("lms:dashboard")


class StudentLogoutView(LogoutView):
    next_page = reverse_lazy("lms:home")

    def get(self, request, *args, **kwargs):
        """Allow simple link logout for demo UX."""
        return self.post(request, *args, **kwargs)


def signup(request):
    if request.user.is_authenticated:
        return redirect("lms:dashboard")
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            send_platform_email(
                user.email,
                "Welcome to EduPlatform",
                f"<p>Hi {user.first_name or user.username}, welcome aboard. "
                "Start with your learning roadmap or browse the catalog.</p>",
            )
            ActivityLog.objects.create(user=user, message="Joined EduPlatform")
            messages.success(request, "Account created — welcome to EduPlatform!")
            return redirect("lms:dashboard")
    else:
        form = SignupForm()
    return render(request, "accounts/auth.html", {"form": form, "auth_mode": "signup"})


def billing(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    txns = Transaction.objects.filter(user=request.user).select_related("course")
    return render(request, "lms/billing.html", {"transactions": txns})
