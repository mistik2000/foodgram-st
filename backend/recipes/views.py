from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse

from .models import Ingredient, Recipe, Favorite, ShoppingCart
from .serializers import (
    IngredientSerializer,
    RecipeSerializer,
    RecipeShortSerializer
)
from .filters import RecipeFilter


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        return self._handle_custom_action(Favorite, request, pk)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        return self._handle_custom_action(ShoppingCart, request, pk)

    def _handle_custom_action(self, model, request, pk):
        recipe = Recipe.objects.filter(pk=pk).first()
        if not recipe:
            return Response({'detail': 'Рецепт не найден'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'POST':
            obj, created = model.objects.get_or_create(user=request.user, recipe=recipe)
            if not created:
                return Response({'detail': 'Рецепт уже добавлен'}, status=status.HTTP_400_BAD_REQUEST)
            serializer = RecipeShortSerializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = model.objects.filter(user=request.user, recipe=recipe).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Рецепт не найден в списке'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients = {}
        recipes = Recipe.objects.filter(in_shopping_cart__user=request.user)
        for recipe in recipes:
            for ri in recipe.recipe_ingredients.all():
                name = ri.ingredient.name
                unit = ri.ingredient.measurement_unit
                amount = ri.amount
                if name not in ingredients:
                    ingredients[name] = {'amount': amount, 'unit': unit}
                else:
                    ingredients[name]['amount'] += amount

        lines = [
            f"{name} — {data['amount']} {data['unit']}" for name, data in ingredients.items()
        ]
        content = '\n'.join(lines)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response