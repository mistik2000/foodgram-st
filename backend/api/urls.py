from django.urls import include, path

from recipes.views import IngredientViewSet

urlpatterns = [
    path('users/', include('users.urls')),
    path('recipes/', include('recipes.urls', namespace='recipes')),
    path('ingredients/', IngredientViewSet.as_view({'get': 'list'}), name='ingredients'),
    path('auth/', include([
        path('', include('djoser.urls')),
        path('', include('djoser.urls.authtoken')),
    ])),
]