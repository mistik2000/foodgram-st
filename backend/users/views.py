from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from api.pagination import CustomPagination

from .models import User, Subscription
from .serializers import (
    CustomUserCreateSerializer,
    UserSerializer,
    SubscriptionListSerializer,
    PasswordChangeSerializer,
    AvatarSerializer,
    SubscriptionSerializer,  
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
        return Response(serializer.to_representation(user), status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        user = request.user
        authors = User.objects.filter(subscribers__user=user)
        page = self.paginate_queryset(authors)
        serializer = self.get_serializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], permission_classes=(IsAuthenticated,))
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, id=pk)

        if request.method == 'POST':
            if author == request.user:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if Subscription.objects.filter(user=request.user, author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            data = {'user': request.user.id, 'author': author.id}
            serializer = SubscriptionSerializer(data=data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            subscription = serializer.save()
            response_serializer = SubscriptionListSerializer(author, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        deleted_count, _ = Subscription.objects.filter(user=request.user, author=author).delete()
        if deleted_count == 0:
            return Response(
                {'errors': 'Вы не были подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'], permission_classes=(IsAuthenticated,), name='me_patch')
    def me_patch(self, request):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
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
