from django.urls import path

from . import views

urlpatterns = [
    path('v1/users/register/', views.RegisterView.as_view(), name='user-register'),
    path('v1/users/login/', views.PhoneCodeLoginView.as_view(), name='user-login'),
    path('v1/users/password_login/', views.PasswordLoginView.as_view(), name='password-login'),
    path('v1/users/logout/', views.LogoutView.as_view(), name='user-logout'),
    path('v1/users/user_details/', views.UserDetailsView.as_view(), name='user-details'),
    path('v1/users/reset_password_by_phone_code/', views.SetPasswordByPhoneCodeView.as_view(),
         name='user-set-password-by-phone-code'),
    # path('v1/users/reset_password_by_phone_code_unauth/', views.SetPasswordByPhoneCodeUnauthView.as_view(),
    #      name='user-set-password-by-phone-code-unauth'),
    path('v1/users/reset_password_by_old_password/', views.SetPasswordByOldPasswordView.as_view(),
         name='user-set-password-by-old-password'),
]
