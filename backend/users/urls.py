from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserAvatarView, LoginView, LogoutView

app_name = 'users'

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('users/me/avatar/', UserAvatarView.as_view(), name='user-avatar'),
    path('auth/token/login/', LoginView.as_view(), name='login'),
    path('auth/token/logout/', LogoutView.as_view(), name='logout'),
    # path('users/set_password/', change_password, name='set-password'),
] 