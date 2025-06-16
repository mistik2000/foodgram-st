from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientSearchFilter, RecipeFilter
from .models import Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart
from .permissions import IsOwnerOrReadOnly
from .serializers import IngredientSerializer, RecipeReadSerializer, RecipeWriteSerializer, ShortRecipeSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [IngredientSearchFilter]
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'recipe_ingredients__ingredient'
    ).order_by('id')
    permission_classes = (IsOwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        if self.action in ('favorite', 'shopping_cart'):
            return ShortRecipeSerializer
        return RecipeWriteSerializer

    def _manage_relation(self, model, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        relation_exists = model.objects.filter(user=request.user, recipe=recipe).exists()

        if request.method == 'POST':
            if relation_exists:
                return Response(
                    {'errors': f'Рецепт уже в {model._meta.model_name}.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(user=request.user, recipe=recipe)
            serializer = self.get_serializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if not relation_exists:
            return Response(
                {'errors': f'Рецепта нет в {model._meta.model_name}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        model.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def get_link(self, request, pk=None):
        return Response({'short-link': request.build_absolute_uri()})

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        return self._manage_relation(Favorite, request, pk)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        return self._manage_relation(ShoppingCart, request, pk)

    def _generate_shopping_list_text(self, user):
        ingredients = RecipeIngredient.objects.filter(
            recipe__in_shopping_cart__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        shopping_list = 'Список покупок:\n\n'
        for item in ingredients:
            shopping_list += (
                f'{item["ingredient__name"]} '
                f'({item["ingredient__measurement_unit"]})'
                f' - {item["total_amount"]}\n'
            )
        return shopping_list

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        shopping_list = self._generate_shopping_list_text(request.user)

        response = HttpResponse(
            shopping_list, content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response
