from django.urls import include, path
from rest_framework.routers import DefaultRouter

from recipes.views import IngredientViewSet
from users.views import UserAvatarView

router = DefaultRouter()
router.register(r'ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('users/me/avatar/', UserAvatarView.as_view(), name='user-avatar'),
    path('users/', include('users.urls')),
    path('recipes/', include('recipes.urls', namespace='recipes')),
    path('auth/', include([
        path('', include('djoser.urls')),
        path('', include('djoser.urls.authtoken')),
    ])),
    path('', include(router.urls)),
]