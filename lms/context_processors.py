from django.conf import settings

from .models import Category


def site_globals(request):
    return {
        "nav_categories": Category.objects.all()[:8],
        "bkash_account": settings.BKASH_ACCOUNT_NUMBER,
        "bkash_name": settings.BKASH_ACCOUNT_NAME,
    }
