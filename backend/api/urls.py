from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import (
    IngredientViewSet,
    RecipeViewSet,
    UserAvatarView,
    UserViewSet,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('users/me/avatar/', UserAvatarView.as_view(), name='user-avatar'),
    path(
        'auth/',
        include([
            path('', include('djoser.urls')),
            path('', include('djoser.urls.authtoken')),
        ]),
    ),
    path('', include(router.urls)),
]
