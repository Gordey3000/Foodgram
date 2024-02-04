import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers, validators

from users.models import User, Subscribe
from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    IngredientRecipe,
    Favorite,
    ShoppingCart,
)


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )
        model = User

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            subscribes = Subscribe.objects.filter(
                user=request.user,
                author=obj
            ).exists()
            return subscribes
        else:
            return False


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'measurement_unit',)
        model = Ingredient


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'color', 'slug',)
        model = Tag


class IngredientRecipeSerializer(serializers.ModelSerializer):
    name = serializers.StringRelatedField(
        source='ingredient.name'
    )
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit'
    )
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient.id',
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = IngredientRecipe
        fields = ('amount', 'name', 'measurement_unit', 'id')


class IngredientCreateRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(write_only=True)
    amount = serializers.IntegerField(write_only=True, min_value=1)

    class Meta:
        fields = ('id', 'amount',)
        model = IngredientRecipe


class RecipesSerializer(serializers.ModelSerializer):
    tags = TagsSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(
        many=True, source='recipe_ingredients'
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = ('is_favorited', 'is_in_shopping_cart',)
        model = Recipe

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        else:
            shopping = ShoppingCart.objects.filter(user=user,
                                                   recipe=obj).exists()
            return shopping

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        else:
            favorite = Favorite.objects.filter(user=user,
                                               recipe=obj).exists()
            return favorite


class RecipeUpdateCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientCreateRecipeSerializer(many=True, required=True)
    image = Base64ImageField(max_length=None, use_url=True)
    cooking_time = serializers.IntegerField(write_only=True)

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        model = Recipe

    def update(self, instance, validated_data):
        instance.tags.clear()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        IngredientRecipe.objects.filter(recipe=instance).delete()
        ingredient_create = [
            IngredientRecipe(
                recipe=instance,
                ingredient=Ingredient.objects.get(id=ingredient.get("id")),
                amount=ingredient.get("amount"),
            )
            for ingredient in ingredients
        ]
        IngredientRecipe.objects.bulk_create(ingredient_create)
        instance.tags.set(tags)
        super().update(instance, validated_data)
        return instance

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(**validated_data, author=author)
        ingredient_create = [
            IngredientRecipe(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=ingredient.get("id")),
                amount=ingredient.get("amount"),
            )
            for ingredient in ingredients
        ]
        IngredientRecipe.objects.bulk_create(ingredient_create)
        recipe.tags.set(tags)
        return recipe


class RecipeSmallSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time',)
        model = Recipe


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        fields = (
            'username',
            'id',
            'password',
            'email',
            'first_name',
            'last_name',
        )
        model = User


class SubscribeSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        model = User

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes_limit = None
        if request:
            recipes_limit = request.query_params.get("recipes_limit")
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = obj.recipes.all()[: int(recipes_limit)]
        return RecipeSmallSerializer(
            recipes, many=True, context={"request": request}
        ).data

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        subscribes = Subscribe.objects.filter(
            user=request.user.is_authenticated,
            author=obj
        ).exists()
        return subscribes

    def get_recipes_count(self, obj):
        return obj.recipes.count()
