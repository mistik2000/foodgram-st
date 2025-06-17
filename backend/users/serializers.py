from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.fields import Base64ImageField
from .models import Subscription


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
        from recipes.serializers import ShortRecipeSerializer

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