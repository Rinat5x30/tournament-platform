# accounts/urls.py

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.register, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # ВАЖНО: Специфичные URL ПЕРЕД общими!
    # Эти URL должны идти ДО profile/<str:username>/
    path('profile/edit/', views.profile_edit, name='profile_edit'),  # ← ПЕРЕМЕСТИЛИ СЮДА
    path('password/change/', views.change_password, name='change_password'),  # ← ПЕРЕМЕСТИЛИ СЮДА
    
    # Общий URL profile/<username>/ идет ПОСЛЕ специфичных
    path('profile/<str:username>/', views.profile, name='profile'),
]