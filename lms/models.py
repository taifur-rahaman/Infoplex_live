from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=40, blank=True, help_text="CSS icon class or emoji-free label")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Course(models.Model):
    class Level(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    class DurationBand(models.TextChoices):
        SHORT = "short", "<5h"
        MEDIUM = "medium", "5-20h"
        LONG = "long", ">20h"

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    code = models.CharField(max_length=20, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="courses"
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="courses_taught",
    )
    instructor_bio = models.TextField(blank=True)
    short_description = models.CharField(max_length=300)
    description = models.TextField()
    learning_outcomes = models.TextField(
        blank=True, help_text="One outcome per line"
    )
    preview_youtube_id = models.CharField(
        max_length=32, blank=True, help_text="Unlisted YouTube video ID"
    )
    thumbnail_url = models.URLField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.BEGINNER)
    topic = models.CharField(max_length=80, blank=True)
    duration_hours = models.DecimalField(max_digits=6, decimal_places=1, default=Decimal("5.0"))
    duration_band = models.CharField(
        max_length=20, choices=DurationBand.choices, default=DurationBand.MEDIUM
    )
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    prerequisites = models.ManyToManyField(
        "self", blank=True, symmetrical=False, related_name="unlocks"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_featured", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.code or self.title)
            self.slug = base
        hours = float(self.duration_hours or 0)
        if hours < 5:
            self.duration_band = self.DurationBand.SHORT
        elif hours <= 20:
            self.duration_band = self.DurationBand.MEDIUM
        else:
            self.duration_band = self.DurationBand.LONG
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("lms:course_detail", kwargs={"slug": self.slug})

    @property
    def outcomes_list(self):
        return [line.strip() for line in self.learning_outcomes.splitlines() if line.strip()]

    @property
    def average_rating(self):
        agg = self.reviews.aggregate(avg=models.Avg("rating"), count=models.Count("id"))
        return agg["avg"] or 0, agg["count"] or 0

    @property
    def lesson_count(self):
        return Lesson.objects.filter(module__course=self).count()


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("course", "order")]

    def __str__(self):
        return f"{self.course.code or self.course.title}: {self.title}"


class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    youtube_id = models.CharField(max_length=32, blank=True)
    content = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=10)
    order = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "lms:player",
            kwargs={"course_slug": self.module.course.slug, "lesson_id": self.pk},
        )


class Quiz(models.Model):
    module = models.OneToOneField(Module, on_delete=models.CASCADE, related_name="quiz")
    title = models.CharField(max_length=200)
    time_limit_minutes = models.PositiveIntegerField(default=15)
    pass_score = models.PositiveIntegerField(
        default=70, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.text[:60]


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.text[:60]


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        PENDING = "pending", "Pending Payment"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    last_lesson = models.ForeignKey(
        Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        unique_together = [("user", "course")]
        ordering = ["-enrolled_at"]

    def __str__(self):
        return f"{self.user} → {self.course}"

    def progress_percent(self):
        total = Lesson.objects.filter(module__course=self.course).count()
        if not total:
            return 0
        done = Progress.objects.filter(
            user=self.user, lesson__module__course=self.course, completed=True
        ).count()
        return int(round(100 * done / total))


class Progress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="progress"
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress")
    completed = models.BooleanField(default=False)
    watched_seconds = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("user", "lesson")]
        verbose_name_plural = "progress"

    def __str__(self):
        status = "done" if self.completed else "in progress"
        return f"{self.user} / {self.lesson} ({status})"


class QuizAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts"
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    score = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    answers = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.user} / {self.quiz} = {self.score}%"


class Coupon(models.Model):
    code = models.CharField(max_length=40, unique=True)
    description = models.CharField(max_length=200, blank=True)
    percent_off = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    amount_off = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return False
        return True

    def discount_for(self, price: Decimal) -> Decimal:
        price = Decimal(price)
        discount = Decimal("0.00")
        if self.percent_off:
            discount += price * Decimal(self.percent_off) / Decimal("100")
        if self.amount_off:
            discount += Decimal(self.amount_off)
        return min(discount, price)


class Transaction(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending Verification"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class Method(models.TextChoices):
        BKASH = "bkash", "bKash"
        CARD = "card", "Credit Card"
        PAYPAL = "paypal", "PayPal"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions"
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    coupon = models.ForeignKey(
        Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions"
    )
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.BKASH)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    bkash_trx_id = models.CharField(max_length=64, blank=True)
    bkash_sender = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} / {self.course} / {self.amount} ({self.status})"


class Review(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("course", "user")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rating}★ {self.course} by {self.user}"


class ActivityLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
    )
    message = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.message
