from django.urls import path

from . import views

app_name = "lms"

urlpatterns = [
    path("", views.home, name="home"),
    path("courses/", views.catalog, name="catalog"),
    path("courses/<slug:slug>/", views.course_detail, name="course_detail"),
    path("courses/<slug:slug>/checkout/", views.checkout, name="checkout"),
    path("checkout/status/<int:txn_id>/", views.checkout_status, name="checkout_status"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("learn/<slug:course_slug>/", views.player_start, name="player_start"),
    path("learn/<slug:course_slug>/<int:lesson_id>/", views.player, name="player"),
    path("learn/complete/<int:lesson_id>/", views.mark_complete, name="mark_complete"),
    path("quizzes/", views.quizzes_list, name="quizzes"),
    path("quizzes/<int:quiz_id>/", views.quiz_take, name="quiz_take"),
    path("roadmap/", views.roadmap, name="roadmap"),
    path("billing/", views.billing, name="billing"),
]
