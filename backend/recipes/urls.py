from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet

app_name = 'recipes'

router = DefaultRouter()
router.register('', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('<int:pk>/get-link/', RecipeViewSet.as_view({'get': 'get_link'}), name='recipe-get-link'),
    path('', include(router.urls)),
]
