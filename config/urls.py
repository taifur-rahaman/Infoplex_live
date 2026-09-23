from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "InfoPlex Admin"
admin.site.site_title = "InfoPlex"
admin.site.index_title = "Manage courses, payments & students"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("lms.urls")),
    path("accounts/", include("accounts.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
