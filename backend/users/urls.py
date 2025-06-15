from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserAvatarView

app_name = 'users'

router = DefaultRouter()
router.register(r'', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('me/avatar/', UserAvatarView.as_view(), name='user-avatar'),
]
