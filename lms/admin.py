from django.contrib import admin
from django.utils import timezone

from .models import (
    ActivityLog,
    Category,
    Choice,
    Coupon,
    Course,
    Enrollment,
    Lesson,
    Module,
    Progress,
    Question,
    Quiz,
    QuizAttempt,
    Review,
    Transaction,
)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    show_change_link = True


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    show_change_link = True


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "code",
        "category",
        "level",
        "price",
        "is_published",
        "is_featured",
    )
    list_filter = ("category", "level", "duration_band", "is_published", "is_featured")
    search_fields = ("title", "code", "topic", "short_description")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("prerequisites",)
    inlines = [ModuleInline]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)
    search_fields = ("title", "course__title")
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "order", "duration_minutes", "is_preview")
    list_filter = ("module__course", "is_preview")
    search_fields = ("title",)


class QuizQuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "time_limit_minutes", "pass_score")
    search_fields = ("title", "module__title")
    inlines = [QuizQuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz", "order", "points")
    list_filter = ("quiz",)
    search_fields = ("text",)
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ("text", "question", "is_correct", "order")
    list_filter = ("is_correct",)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "status", "enrolled_at", "deadline")
    list_filter = ("status", "course")
    search_fields = ("user__username", "user__email", "course__title")
    raw_id_fields = ("user", "course", "last_lesson")


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "completed", "watched_seconds", "updated_at")
    list_filter = ("completed",)
    search_fields = ("user__username", "lesson__title")


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "quiz", "score", "passed", "started_at", "submitted_at")
    list_filter = ("passed", "quiz")
    search_fields = ("user__username",)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "percent_off",
        "amount_off",
        "is_active",
        "used_count",
        "max_uses",
        "valid_until",
    )
    list_filter = ("is_active",)
    search_fields = ("code", "description")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "course",
        "amount",
        "method",
        "status",
        "bkash_trx_id",
        "created_at",
    )
    list_filter = ("status", "method")
    search_fields = ("user__username", "bkash_trx_id", "bkash_sender", "course__title")
    actions = ["approve_transactions", "reject_transactions"]

    @admin.action(description="Approve selected (enroll students)")
    def approve_transactions(self, request, queryset):
        for txn in queryset.filter(status=Transaction.Status.PENDING):
            txn.status = Transaction.Status.APPROVED
            txn.reviewed_at = timezone.now()
            txn.save(update_fields=["status", "reviewed_at"])
            Enrollment.objects.update_or_create(
                user=txn.user,
                course=txn.course,
                defaults={"status": Enrollment.Status.ACTIVE},
            )
            if txn.coupon_id:
                c = txn.coupon
                c.used_count += 1
                c.save(update_fields=["used_count"])
            ActivityLog.objects.create(
                user=txn.user,
                message=f"Payment approved for '{txn.course.title}'",
            )

    @admin.action(description="Reject selected transactions")
    def reject_transactions(self, request, queryset):
        queryset.filter(status=Transaction.Status.PENDING).update(
            status=Transaction.Status.REJECTED, reviewed_at=timezone.now()
        )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("course", "user", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("comment", "user__username", "course__title")


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("message", "user", "created_at")
    search_fields = ("message", "user__username")
