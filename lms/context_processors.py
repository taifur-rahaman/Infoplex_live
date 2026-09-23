from django.conf import settings

from .models import Category


def site_globals(request):
    site_name = getattr(settings, "SITE_NAME", "InfoPlex")
    brand_mark = getattr(settings, "BRAND_MARK", site_name[:1].upper())
    return {
        "site_name": site_name,
        "brand_mark": brand_mark,
        "nav_categories": Category.objects.all()[:8],
        "bkash_account": settings.BKASH_ACCOUNT_NUMBER,
        "bkash_name": settings.BKASH_ACCOUNT_NAME,
    }
