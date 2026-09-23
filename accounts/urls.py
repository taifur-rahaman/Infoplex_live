from django.urls import path

from lms.views import StudentLoginView, StudentLogoutView, signup

app_name = "accounts"

urlpatterns = [
    path("login/", StudentLoginView.as_view(), name="login"),
    path("logout/", StudentLogoutView.as_view(), name="logout"),
    path("signup/", signup, name="signup"),
]
