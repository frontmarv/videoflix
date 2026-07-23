from django.urls import path
from django.conf import settings
from .views import RegisterView, ActivateAccountView, LoginView, LogoutView, CookieTokenRefreshView, PasswordResetRequestView, PasswordResetConfirmView, preview_activation_email, preview_password_reset_email

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('password_reset/', PasswordResetRequestView.as_view(),
         name='password_reset'),
    path('password_confirm/<str:uidb64>/<str:token>/',
         PasswordResetConfirmView.as_view(), name='password_confirm'),
    path('activate/<str:uidb64>/<str:token>/',
         ActivateAccountView.as_view(), name='activate'),
]

if settings.DEBUG:
    urlpatterns += [
        path('_preview/email/activation/', preview_activation_email,
             name='preview_activation_email'),
        path('_preview/email/password-reset/', preview_password_reset_email,
             name='preview_password_reset_email'),
    ]
