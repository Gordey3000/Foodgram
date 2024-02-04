from rest_framework import status, viewsets, exceptions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import (SAFE_METHODS,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from django.db.models import Sum
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend

from users.models import User, Subscribe
from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart,
    IngredientRecipe,
)
from .serializers import (
    TagsSerializer,
    IngredientsSerializer,
    RecipesSerializer,
    RecipeUpdateCreateSerializer,
    RecipeSmallSerializer,
    CustomUserSerializer,
    SubscribeSerializer
)
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAdminAuthorOrReadOnly


class CustomUsersViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    @action(
        detail=False,
        methods=['GET'],
        url_path='subscriptions',
        url_name='subscriptions',
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        serializer = SubscribeSerializer(
            self.paginate_queryset(User.objects.filter(
                subscriber__user=self.request.user)),
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path='subscribe',
        url_name='subscribe',
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=self.kwargs.get('id'))
        subscription, created = Subscribe.objects.get_or_create(
            user=request.user,
            author=author
        )
        if request.method == 'POST' and not created:
            raise exceptions.ValidationError(
                detail='У вас уже есть подписка на данного пользователя.'
            )
        if request.method == 'POST':
            serializer = SubscribeSerializer(
                author,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagsSerializer
    pagination_class = None


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipesSerializer
    permission_classes = (
        IsAuthenticatedOrReadOnly,
        IsAdminAuthorOrReadOnly,
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        queryset = Recipe.objects.prefetch_related(
            'recipe_ingredients__ingredient',
            'tags',
            'author'
            ).all()
        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeUpdateCreateSerializer
        return RecipesSerializer

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path='favorite',
        url_name='favorite',
        permission_classes=(IsAuthenticated,),
    )
    def add_remove_favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        obj, created = Favorite.objects.select_related(
            'user', 'recipe'
        ).get_or_create(user=request.user, recipe=recipe)
        if request.method == 'POST' and created:
            serializer = RecipeSmallSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE' and obj:
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path='shopping_cart',
        url_name='shopping_cart',
        permission_classes=(IsAuthenticated,),
    )
    def add_remove_shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        obj, created = ShoppingCart.objects.select_related(
            'user', 'recipe'
        ).get_or_create(user=request.user, recipe=recipe)
        if request.method == 'POST' and created:
            serializer = RecipeSmallSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE' and obj:
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['GET'],
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        ingredients = (IngredientRecipe.objects.filter(
            recipe__shopping_carts__user=request.user).values(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(amount=Sum('amount')))
        pretty_ings = []
        for ingredient in ingredients:
            pretty_ings.append('{name} - {amount} {m_unit}\n'.format(
                name=ingredient.get('ingredient__name'),
                amount=ingredient.get('amount'),
                m_unit=ingredient.get('ingredient__measurement_unit')
            ))
        response = FileResponse(pretty_ings, content_type='text/plain')
        return response
