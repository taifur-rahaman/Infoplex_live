from decimal import Decimal

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Coupon, Review, Transaction


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data.get("first_name", "")
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Username or email", "autocomplete": "username"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password", "autocomplete": "current-password"})
    )


class CouponForm(forms.Form):
    code = forms.CharField(max_length=40, required=False, label="Coupon code")


class CheckoutForm(forms.Form):
    method = forms.ChoiceField(
        choices=Transaction.Method.choices,
        initial=Transaction.Method.BKASH,
        widget=forms.RadioSelect,
    )
    coupon_code = forms.CharField(max_length=40, required=False)
    bkash_trx_id = forms.CharField(max_length=64, required=False, label="bKash Transaction ID")
    bkash_sender = forms.CharField(max_length=20, required=False, label="Your bKash number")
    card_number = forms.CharField(max_length=19, required=False)
    card_expiry = forms.CharField(max_length=7, required=False)
    card_cvc = forms.CharField(max_length=4, required=False)

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get("method")
        if method == Transaction.Method.BKASH:
            if not cleaned.get("bkash_trx_id"):
                self.add_error("bkash_trx_id", "Enter the bKash transaction ID after sending payment.")
            if not cleaned.get("bkash_sender"):
                self.add_error("bkash_sender", "Enter the mobile number you paid from.")
        elif method == Transaction.Method.CARD:
            if not cleaned.get("card_number"):
                self.add_error("card_number", "Card number is required for demo card checkout.")
        return cleaned


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "comment")
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5}),
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "What did you think of this course?"}),
        }


class RoadmapForm(forms.Form):
    LEVEL_CHOICES = [
        ("secondary", "Secondary School"),
        ("hsc", "Higher Secondary"),
        ("cse", "CSE / Programming"),
        ("eee", "EEE / Circuits"),
    ]
    INTEREST_CHOICES = [
        ("math", "Math & Physics"),
        ("programming", "Programming & AI"),
        ("circuits", "Circuits & Power"),
        ("general", "Explore everything"),
    ]
    current_level = forms.ChoiceField(choices=LEVEL_CHOICES)
    interest = forms.ChoiceField(choices=INTEREST_CHOICES)


def apply_coupon(code: str, price: Decimal):
    if not code:
        return None, Decimal("0.00"), "No coupon applied."
    try:
        coupon = Coupon.objects.get(code__iexact=code.strip())
    except Coupon.DoesNotExist:
        return None, Decimal("0.00"), "Coupon not found."
    if not coupon.is_valid():
        return None, Decimal("0.00"), "Coupon is expired or inactive."
    return coupon, coupon.discount_for(price), f"Applied {coupon.code}."
