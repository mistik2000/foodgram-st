from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .serializers import (
    UserCreateSerializer,
    UserSerializer,
    UserProfileSerializer,
    AvatarSerializer,
    PasswordChangeSerializer,
    SubscriptionSerializer,
)
from .models import User, Subscription
from  api.pagination import CustomPagination


class UserViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для пользователей.
    Создание и получение списка доступны всем.
    Остальные действия — только аутентифицированным.
    """

    queryset = User.objects.all()
    pagination_class = CustomPagination
    http_method_names = ['get', 'post']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['create', 'list']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_context(self):
        return {'request': self.request}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Возвращаем ожидаемую структуру (без лишних полей)
        return Response(serializer.to_representation(user), status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def set_password(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        subscriptions = Subscription.objects.filter(user=request.user)
        page = self.paginate_queryset(subscriptions)
        serializer = SubscriptionSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        author = self.get_object()
        user = request.user

        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data={'user': user.id, 'author': author.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            deleted_count, _ = Subscription.objects.filter(user=user, author=author).delete()
            if deleted_count == 0:
                return Response({'errors': 'Вы не подписаны на этого автора.'}, status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)


class UserProfileView(generics.RetrieveAPIView):
    """
    Просмотр профиля пользователя по id.
    Доступно всем.
    """
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [AllowAny]


class UserAvatarView(generics.UpdateAPIView):
    """
    Обновление/удаление аватара пользователя.
    """

    serializer_class = AvatarSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # В твоей модели User есть поле avatar, возвращаем пользователя напрямую
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        if user.avatar:
            user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
