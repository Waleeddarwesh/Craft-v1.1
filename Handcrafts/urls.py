from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="CraftEG API",
        default_version='v1',
        description="API documentation for Craft application",
        terms_of_service="https://www.example.com/policies/terms/",
        contact=openapi.Contact(email="Waleeddarwesh2002@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('course/', include('course.urls')),
    path('orders/', include('orders.urls')),
    path('payment/', include('payment.urls')),
    path('review/', include('reviews.urls')),
    path('notifications/', include('notifications.urls')),
    path('chat/', include('chatapp.urls')),
    path('return/', include('returnrequest.urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Serve static and media files in production via Django
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]