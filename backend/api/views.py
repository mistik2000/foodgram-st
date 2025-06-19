from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, viewsets, views
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
)
from users.models import User, Subscription

from .filters import IngredientSearchFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    AvatarSerializer,
    FavoriteCartSerializer,
    IngredientSerializer,
    PasswordChangeSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShortRecipeSerializer,
    SubscriptionListSerializer,
    SubscriptionSerializer,
    CustomUserCreateSerializer,
    UserSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        if self.action == 'subscriptions':
            return SubscriptionListSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_context(self):
        return {'request': self.request}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            serializer.to_representation(user),
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False, methods=['get'], permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        user = request.user
        authors = User.objects.filter(subscribers__user=user)
        page = self.paginate_queryset(authors)
        serializer = self.get_serializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, id=pk)

        if request.method == 'POST':
            data = {'user': request.user.id, 'author': author.id}
            serializer = SubscriptionSerializer(
                data=data,
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            response_serializer = SubscriptionListSerializer(
                author, context={'request': request}
            )
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED,
            )

        deleted_count, _ = Subscription.objects.filter(
            user=request.user, author=author
        ).delete()
        if deleted_count == 0:
            return Response(
                {'errors': 'Вы не были подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['get'], permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['patch'],
        permission_classes=(IsAuthenticated,),
        name='me_patch',
    )
    def me_patch(self, request):
        serializer = self.get_serializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(
        detail=False, methods=['post'], permission_classes=(IsAuthenticated,)
    )
    def set_password(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserAvatarView(views.APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def put(self, request, *args, **kwargs):
        serializer = AvatarSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


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
        user = request.user
        relation = model.objects.filter(user=user, recipe=recipe)

        if request.method == 'POST':
            if relation.exists():
                return Response(
                    {'errors': f'Рецепт уже в {model._meta.verbose_name}.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = FavoriteCartSerializer(
                data={'recipe': recipe.id},
                context={'request': request},
                model_class=model,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            short_serializer = self.get_serializer(recipe)
            return Response(
                short_serializer.data,
                status=status.HTTP_201_CREATED,
            )

        deleted_count, _ = relation.delete()
        if deleted_count == 0:
            return Response(
                {'errors': f'Рецепта нет в {model._meta.verbose_name}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        return Response({'short-link': request.build_absolute_uri()})

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        return self._manage_relation(Favorite, request, pk)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        return self._manage_relation(ShoppingCart, request, pk)

    def _generate_shopping_list_text(self, user):
        ingredients = RecipeIngredient.objects.filter(
            recipe__in_shopping_cart__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit',
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

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        shopping_list = self._generate_shopping_list_text(request.user)

        response = HttpResponse(
            shopping_list,
            content_type='text/plain; charset=utf-8',
        )
        response['Content-Disposition'] = (
            'attachment; '
            'filename="shopping_list.txt"'
        )
        return response
