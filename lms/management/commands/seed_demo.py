from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Profile
from lms.models import (
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

# Public/demo unlisted-style educational YouTube IDs
YT = {
    "python": "rfscVS0vtbw",
    "circuits": "m4yA-gcSMik",
    "math": "WUvTyaaNkzM",
    "physics": "ZMByI4s-D-Y",
    "ds": "8hly31xKPxi",
    "ai": "aircAruvnKk",
}


class Command(BaseCommand):
    help = "Seed InfoPlex with realistic demo courses, users, and enrollments"

    def handle(self, *args, **options):
        self.stdout.write("Seeding InfoPlex…")

        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@infoplex.local",
                "is_staff": True,
                "is_superuser": True,
                "first_name": "Ada",
                "last_name": "Admin",
            },
        )
        if created or not admin_user.has_usable_password():
            admin_user.set_password("admin123")
            admin_user.save()
        Profile.objects.filter(user=admin_user).update(role=Profile.Role.ADMIN)

        instructors = {}
        for username, first, last, bio in [
            ("prof.smith", "Elena", "Smith", "CSE lecturer focusing on Python and algorithms."),
            ("prof.rahman", "Karim", "Rahman", "EEE instructor with 12 years in power systems."),
            ("prof.chen", "Mei", "Chen", "Physics educator for secondary and HSC students."),
        ]:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@infoplex.local", "first_name": first, "last_name": last},
            )
            if created:
                user.set_password("teach123")
                user.save()
            Profile.objects.filter(user=user).update(
                role=Profile.Role.INSTRUCTOR, bio=bio
            )
            instructors[username] = user

        student, created = User.objects.get_or_create(
            username="student",
            defaults={
                "email": "student@infoplex.local",
                "first_name": "Sara",
                "last_name": "Ahmed",
            },
        )
        if created or not student.has_usable_password():
            student.set_password("student123")
            student.save()
        Profile.objects.filter(user=student).update(
            role=Profile.Role.STUDENT,
            current_level="cse",
            interest="programming",
            phone="01711112222",
        )

        cats = {}
        for order, name, desc, icon in [
            (1, "Secondary School", "Math, Physics, and foundations for SSC.", "secondary"),
            (2, "Higher Secondary", "Advanced sciences for HSC & admission.", "hsc"),
            (3, "CSE Section", "Programming, AI, and software engineering.", "cse"),
            (4, "EEE Section", "Circuits, electronics, and power systems.", "eee"),
        ]:
            cat, _ = Category.objects.update_or_create(
                slug=name.lower().replace(" ", "-"),
                defaults={"name": name, "description": desc, "icon": icon, "order": order},
            )
            cats[icon] = cat

        course_specs = [
            {
                "code": "CSE 101",
                "title": "Intro to Python Programming",
                "cat": "cse",
                "instructor": "prof.smith",
                "topic": "Python",
                "level": Course.Level.BEGINNER,
                "hours": Decimal("15.0"),
                "price": Decimal("50.00"),
                "yt": YT["python"],
                "featured": True,
                "short": "Write clean Python from day one — variables to projects.",
                "desc": "A practical introduction to Python for absolute beginners. Build scripts, practice problem-solving, and prepare for data structures.",
                "outcomes": "Write Python programs with confidence\nUse loops, functions, and modules\nSolve beginner coding challenges\nBuild a small CLI project",
                "modules": [
                    ("Getting Started", ["Install & Setup", "Variables & Types", "Input / Output"]),
                    ("Control Flow", ["Conditionals", "Loops", "Comprehensions"]),
                    ("Functions & Modules", ["Defining Functions", "Arguments", "Standard Library"]),
                    ("Mini Project", ["File I/O", "Project Walkthrough", "Wrap-up"]),
                ],
                "quiz_q": (
                    "What keyword defines a function in Python?",
                    [("def", True), ("func", False), ("function", False)],
                ),
            },
            {
                "code": "CSE 201",
                "title": "Data Structures Fundamentals",
                "cat": "cse",
                "instructor": "prof.smith",
                "topic": "Algorithms",
                "level": Course.Level.INTERMEDIATE,
                "hours": Decimal("20.0"),
                "price": Decimal("65.00"),
                "yt": YT["ds"],
                "featured": True,
                "short": "Lists, trees, graphs — and when to use each.",
                "desc": "Master core data structures used in interviews and production systems.",
                "outcomes": "Implement arrays, stacks, and queues\nTraverse trees and graphs\nAnalyze time complexity\nChoose the right structure for a problem",
                "modules": [
                    ("Linear Structures", ["Arrays & Lists", "Stacks", "Queues"]),
                    ("Trees", ["Binary Trees", "BSTs", "Heaps"]),
                    ("Graphs", ["Representations", "BFS & DFS", "Shortest Paths Intro"]),
                ],
                "quiz_q": (
                    "Which structure is LIFO?",
                    [("Stack", True), ("Queue", False), ("Heap", False)],
                ),
            },
            {
                "code": "CSE 310",
                "title": "AI Foundations",
                "cat": "cse",
                "instructor": "prof.smith",
                "topic": "AI",
                "level": Course.Level.ADVANCED,
                "hours": Decimal("22.0"),
                "price": Decimal("80.00"),
                "yt": YT["ai"],
                "featured": False,
                "short": "Neural nets demystified for engineering students.",
                "desc": "From perception to neural networks — a gentle, visual path into AI.",
                "outcomes": "Explain supervised learning\nTrain a simple neural net\nRead model metrics\nDiscuss ethics in AI",
                "modules": [
                    ("ML Basics", ["What is Learning?", "Features & Labels", "Train/Test Split"]),
                    ("Neural Nets", ["Neurons", "Backprop Intuition", "Deep Learning Overview"]),
                ],
                "quiz_q": (
                    "What does a neural network learn?",
                    [("Weights", True), ("Only labels", False), ("Hardware specs", False)],
                ),
            },
            {
                "code": "EEE 201",
                "title": "Circuits I",
                "cat": "eee",
                "instructor": "prof.rahman",
                "topic": "Circuits",
                "level": Course.Level.BEGINNER,
                "hours": Decimal("18.0"),
                "price": Decimal("55.00"),
                "yt": YT["circuits"],
                "featured": True,
                "short": "Ohm's law to mesh analysis — build circuit intuition.",
                "desc": "Core circuit analysis for first-year EEE students.",
                "outcomes": "Apply Ohm's and Kirchhoff's laws\nAnalyze series/parallel networks\nUse nodal and mesh methods\nSimulate simple circuits",
                "modules": [
                    ("Fundamentals", ["Charge & Current", "Ohm's Law", "Power & Energy"]),
                    ("Network Laws", ["KCL", "KVL", "Series & Parallel"]),
                    ("Analysis Methods", ["Nodal Analysis", "Mesh Analysis", "Superposition"]),
                    ("Lab Concepts", ["Intro to Circuit Analysis", "Breadboards", "Safety"]),
                ],
                "quiz_q": (
                    "What is V if I=2A and R=5Ω?",
                    [("10 V", True), ("2.5 V", False), ("7 V", False)],
                ),
            },
            {
                "code": "EEE 305",
                "title": "Digital Logic",
                "cat": "eee",
                "instructor": "prof.rahman",
                "topic": "Digital",
                "level": Course.Level.INTERMEDIATE,
                "hours": Decimal("16.0"),
                "price": Decimal("60.00"),
                "yt": YT["circuits"],
                "featured": False,
                "short": "Gates, flip-flops, and designing digital systems.",
                "desc": "Boolean algebra through sequential circuits.",
                "outcomes": "Simplify Boolean expressions\nDesign combinational circuits\nUse flip-flops\nBuild a simple counter",
                "modules": [
                    ("Boolean Algebra", ["Gates", "Truth Tables", "Karnaugh Maps"]),
                    ("Sequential Logic", ["Latches", "Flip-Flops", "Counters"]),
                ],
                "quiz_q": (
                    "AND gate output is 1 when…",
                    [("All inputs are 1", True), ("Any input is 1", False), ("No inputs", False)],
                ),
            },
            {
                "code": "SSC MATH",
                "title": "Secondary School Math",
                "cat": "secondary",
                "instructor": "prof.chen",
                "topic": "Math",
                "level": Course.Level.BEGINNER,
                "hours": Decimal("12.0"),
                "price": Decimal("25.00"),
                "yt": YT["math"],
                "featured": True,
                "short": "Algebra and geometry foundations for SSC.",
                "desc": "Clear explanations and practice for secondary math.",
                "outcomes": "Solve linear equations\nWork with exponents\nApply geometry basics\nBuild exam confidence",
                "modules": [
                    ("Algebra Essentials", ["Linear Equations", "Inequalities", "Word Problems"]),
                    ("Geometry", ["Triangles", "Circles", "Area & Volume"]),
                ],
                "quiz_q": (
                    "Solve: 2x + 4 = 10. x = ?",
                    [("3", True), ("2", False), ("6", False)],
                ),
            },
            {
                "code": "PHY 101",
                "title": "Physics 101",
                "cat": "secondary",
                "instructor": "prof.chen",
                "topic": "Physics",
                "level": Course.Level.BEGINNER,
                "hours": Decimal("14.0"),
                "price": Decimal("30.00"),
                "yt": YT["physics"],
                "featured": False,
                "short": "Motion, forces, and energy — with intuition first.",
                "desc": "Introductory physics bridging secondary school to engineering.",
                "outcomes": "Use kinematic equations\nDraw free-body diagrams\nApply conservation of energy\nSolve exam-style problems",
                "modules": [
                    ("Motion", ["Displacement", "Velocity", "Acceleration"]),
                    ("Forces", ["Newton's Laws", "Friction", "Energy"]),
                ],
                "quiz_q": (
                    "Unit of force is…",
                    [("Newton", True), ("Joule", False), ("Watt", False)],
                ),
            },
            {
                "code": "HSC CHEM",
                "title": "Chemistry 101",
                "cat": "hsc",
                "instructor": "prof.chen",
                "topic": "Chemistry",
                "level": Course.Level.INTERMEDIATE,
                "hours": Decimal("16.0"),
                "price": Decimal("35.00"),
                "yt": YT["math"],
                "featured": False,
                "short": "Atomic structure to stoichiometry for HSC.",
                "desc": "Higher secondary chemistry with worked examples.",
                "outcomes": "Balance chemical equations\nUnderstand periodic trends\nCalculate moles\nExplain bonding basics",
                "modules": [
                    ("Atoms & Periodic Table", ["Structure", "Trends", "Isotopes"]),
                    ("Reactions", ["Stoichiometry", "Acids & Bases", "Equilibrium Intro"]),
                ],
                "quiz_q": (
                    "Avogadro's number approximates…",
                    [("6.02×10²³", True), ("3.14", False), ("9.8", False)],
                ),
            },
        ]

        courses = {}
        for spec in course_specs:
            course, _ = Course.objects.update_or_create(
                slug=spec["code"].lower().replace(" ", "-"),
                defaults={
                    "title": spec["title"],
                    "code": spec["code"],
                    "category": cats[spec["cat"]],
                    "instructor": instructors[spec["instructor"]],
                    "instructor_bio": instructors[spec["instructor"]].profile.bio,
                    "short_description": spec["short"],
                    "description": spec["desc"],
                    "learning_outcomes": spec["outcomes"],
                    "preview_youtube_id": spec["yt"],
                    "price": spec["price"],
                    "level": spec["level"],
                    "topic": spec["topic"],
                    "duration_hours": spec["hours"],
                    "is_published": True,
                    "is_featured": spec["featured"],
                },
            )
            courses[spec["code"]] = course
            Module.objects.filter(course=course).delete()
            for mi, (mod_title, lessons) in enumerate(spec["modules"], start=1):
                module = Module.objects.create(
                    course=course,
                    title=f"Module {mi}: {mod_title}",
                    description=f"Cover {mod_title.lower()} with guided video lessons.",
                    order=mi,
                )
                for li, lesson_title in enumerate(lessons, start=1):
                    Lesson.objects.create(
                        module=module,
                        title=lesson_title,
                        youtube_id=spec["yt"],
                        content=f"Lesson notes for {lesson_title}. Watch the video, then try the practice problems.",
                        duration_minutes=12 + li * 2,
                        order=li,
                        is_preview=(mi == 1 and li == 1),
                    )
                quiz = Quiz.objects.create(
                    module=module,
                    title=f"{spec['code']} — {mod_title} Quiz",
                    time_limit_minutes=15,
                    pass_score=70,
                )
                q_text, choices = spec["quiz_q"]
                question = Question.objects.create(
                    quiz=quiz, text=q_text, order=1, points=1
                )
                for ci, (ctext, correct) in enumerate(choices, start=1):
                    Choice.objects.create(
                        question=question, text=ctext, is_correct=correct, order=ci
                    )
                # Extra question per quiz
                q2 = Question.objects.create(
                    quiz=quiz,
                    text=f"Which module topic is this quiz covering?",
                    order=2,
                    points=1,
                )
                Choice.objects.create(question=q2, text=mod_title, is_correct=True, order=1)
                Choice.objects.create(question=q2, text="Unrelated topic", is_correct=False, order=2)
                Choice.objects.create(question=q2, text="Final exam only", is_correct=False, order=3)

        # Prerequisites / roadmap edges
        if "PHY 101" in courses and "SSC MATH" in courses:
            courses["PHY 101"].prerequisites.add(courses["SSC MATH"])
        if "EEE 201" in courses and "PHY 101" in courses:
            courses["EEE 201"].prerequisites.add(courses["PHY 101"])
        if "CSE 201" in courses and "CSE 101" in courses:
            courses["CSE 201"].prerequisites.add(courses["CSE 101"])
        if "CSE 310" in courses and "CSE 201" in courses:
            courses["CSE 310"].prerequisites.add(courses["CSE 201"])
        if "EEE 305" in courses and "EEE 201" in courses:
            courses["EEE 305"].prerequisites.add(courses["EEE 201"])

        Coupon.objects.update_or_create(
            code="WELCOME20",
            defaults={
                "description": "20% off any course",
                "percent_off": 20,
                "is_active": True,
                "max_uses": 500,
            },
        )
        Coupon.objects.update_or_create(
            code="BKASH100",
            defaults={
                "description": "Flat ৳10 off",
                "amount_off": Decimal("10.00"),
                "percent_off": 0,
                "is_active": True,
            },
        )
        Coupon.objects.update_or_create(
            code="FREELEARN",
            defaults={
                "description": "100% off for demos",
                "percent_off": 100,
                "is_active": True,
                "max_uses": 50,
            },
        )

        # Student enrollment progress
        py = courses["CSE 101"]
        eee = courses["EEE 201"]
        Enrollment.objects.update_or_create(
            user=student,
            course=py,
            defaults={
                "status": Enrollment.Status.ACTIVE,
                "deadline": timezone.now() + timedelta(days=1),
            },
        )
        Enrollment.objects.update_or_create(
            user=student,
            course=eee,
            defaults={
                "status": Enrollment.Status.ACTIVE,
                "deadline": timezone.now() + timedelta(days=3),
            },
        )

        py_lessons = list(
            Lesson.objects.filter(module__course=py).order_by("module__order", "order")
        )
        for lesson in py_lessons[:4]:
            Progress.objects.update_or_create(
                user=student, lesson=lesson, defaults={"completed": True}
            )
        if py_lessons:
            Enrollment.objects.filter(user=student, course=py).update(
                last_lesson=py_lessons[min(4, len(py_lessons) - 1)]
            )

        eee_lessons = list(
            Lesson.objects.filter(module__course=eee).order_by("module__order", "order")
        )
        for lesson in eee_lessons[:2]:
            Progress.objects.update_or_create(
                user=student, lesson=lesson, defaults={"completed": True}
            )
        if len(eee_lessons) > 3:
            # Resume on Module 4-ish lesson titled Intro to Circuit Analysis if present
            target = next(
                (l for l in eee_lessons if "Circuit Analysis" in l.title or "Intro" in l.title),
                eee_lessons[2],
            )
            Enrollment.objects.filter(user=student, course=eee).update(last_lesson=target)

        quiz = Quiz.objects.filter(module__course=py).first()
        if quiz:
            QuizAttempt.objects.create(
                user=student,
                quiz=quiz,
                score=85,
                passed=True,
                submitted_at=timezone.now() - timedelta(hours=5),
                answers={},
            )

        Review.objects.update_or_create(
            course=py,
            user=student,
            defaults={
                "rating": 5,
                "comment": "Clear pacing and great practice problems. Finally comfortable with functions.",
            },
        )
        other, _ = User.objects.get_or_create(
            username="jane",
            defaults={"email": "jane@example.com", "first_name": "Jane"},
        )
        if not other.has_usable_password():
            other.set_password("student123")
            other.save()
        Review.objects.update_or_create(
            course=py,
            user=other,
            defaults={
                "rating": 4,
                "comment": "Prof. Smith explains concepts without fluff. Worth it.",
            },
        )

        Transaction.objects.get_or_create(
            user=student,
            course=py,
            bkash_trx_id="DEMO8XK2PY",
            defaults={
                "amount": Decimal("50.00"),
                "method": Transaction.Method.BKASH,
                "status": Transaction.Status.APPROVED,
                "bkash_sender": "01711112222",
                "reviewed_at": timezone.now() - timedelta(days=2),
            },
        )

        ActivityLog.objects.all().delete()
        ActivityLog.objects.create(user=student, message="Completed Quiz 3 in CSE 101")
        ActivityLog.objects.create(user=student, message="Watched Video: Ohm's Law")
        ActivityLog.objects.create(user=other, message="User 'jane' enrolled in 'Intro to Python Programming'")

        self.stdout.write(self.style.SUCCESS("Seed complete."))
        self.stdout.write("  Admin:   admin / admin123")
        self.stdout.write("  Student: student / student123")
        self.stdout.write("  Coupons: WELCOME20, BKASH100, FREELEARN")
