from django.db import transaction
from rest_framework import serializers
from recipes.models import Ingredient, Recipe, RecipeIngredient, Favorite, ShoppingCart
from django.contrib.auth import get_user_model
from .fields import Base64ImageField
from users.models import Subscription


User = get_user_model()


class CustomUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password'
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and Subscription.objects.filter(user=user, author=obj).exists()


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class SubscriptionListSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True, default=0)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    def get_recipes(self, obj):

        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')

        recipes = obj.recipes.all()
        if recipes_limit and isinstance(recipes_limit, str) and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]

        return ShortRecipeSerializer(recipes, many=True, context={'request': request}).data


class PasswordChangeSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    def validate_current_password(self, value):
        user = self.context.get('request').user
        if not user.check_password(value):
            raise serializers.ValidationError('Неверный текущий пароль.')
        return value

    def save(self, **kwargs):
        user = self.context.get('request').user
        user.set_password(self.validated_data['new_password'])
        user.save()


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        user = data['user']
        author = data['author']
        if user == author:
            raise serializers.ValidationError('Нельзя подписаться на самого себя.')
        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError('Вы уже подписаны на этого пользователя.')
        return data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = fields


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True, read_only=True, source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return (user.is_authenticated
                and Favorite.objects.filter(user=user, recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return (user.is_authenticated
                and ShoppingCart.objects.filter(user=user, recipe=obj).exists())
        

class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', 'name', 'image', 'text', 'cooking_time'
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Нужно добавить хотя бы один ингредиент.'
            )
        ingredient_ids = [item['id'] for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError('Ингредиенты не должны повторяться.')
        return value

    def validate(self, data):
        request = self.context.get('request')
        if request and request.method in ('PUT', 'PATCH'):
            if 'ingredients' not in data or not data['ingredients']:
                raise serializers.ValidationError({
                    'ingredients': 'Это поле обязательно при обновлении рецепта.'
                })
        return data

    def _add_ingredients(self, recipe, ingredients):
        recipe.ingredients.clear()
        ingredients_to_create = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
            ) for ingredient_data in ingredients
        ]
        RecipeIngredient.objects.bulk_create(ingredients_to_create)

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        self._add_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        self._add_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data
        

class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class FavoriteCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = None  # Будет устанавливаться динамически
        fields = ('recipe',)

    def __init__(self, *args, **kwargs):
        # Устанавливаем модель в зависимости от контекста
        model_class = kwargs.pop('model_class', None)
        if model_class:
            self.Meta.model = model_class
        super().__init__(*args, **kwargs)

    def validate_recipe(self, value):
        user = self.context['request'].user
        model = self.Meta.model
        if model.objects.filter(user=user, recipe=value).exists():
            raise serializers.ValidationError('Рецепт уже добавлен.')
        return value

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return self.Meta.model.objects.create(**validated_data)
