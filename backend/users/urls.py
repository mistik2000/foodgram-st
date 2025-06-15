from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (SubscriptionViewSet, UserAvatarView, UserProfileView,
                    UserViewSet)

app_name = 'users'

router = DefaultRouter()
router.register('', UserViewSet, basename='users')


urlpatterns = [
    path('subscriptions/', SubscriptionViewSet.as_view({'get': 'list'})),
    path(
        '<int:user_id>/subscribe/',
        SubscriptionViewSet.as_view({'post': 'create', 'delete': 'destroy'})
    ),
    path('me/avatar/', UserAvatarView.as_view()),
    path('<int:pk>/', UserProfileView.as_view()),
    path('', include(router.urls)),
]
