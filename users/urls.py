from django.urls import path
from users.api import auth, dashboard

urlpatterns = [
    path('v1/register', auth.RegisterView.as_view(), name='register'),
    path('v1/userinfo', auth.UserInfoView.as_view(), name='userinfo'),
    path('v1/users', auth.UsersView.as_view(), name='users'),
    path('v1/usernames', auth.UsernamesView.as_view(), name='usernames'),
    path('v1/refresh', auth.RefreshTokenView.as_view(), name='refresh'),
    path('v1/login', auth.LoginView.as_view(), name='login'),
    path('v1/logout', auth.LogoutView.as_view(), name='logout'),
    path('v1/dashboard', dashboard.DashboardView.as_view(), name='dash'),
    path('v1/btn-check', auth.BtnCheckView.as_view(), name='btn-check'),
]
