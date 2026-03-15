from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tournaments.urls')),
    path('accounts/', include('accounts.urls')),
    path('auth/', include('allauth.urls')),  # Изменили с accounts/ на auth/
    path('teams/', include('teams.urls')),
    path('players/', include('players.urls')),
    path('ratings/', include('ratings.urls')),
        path('shop/', include('shop.urls')),  # Добавьте эту строку

    path('admin-panel/', include('admin_panel.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)