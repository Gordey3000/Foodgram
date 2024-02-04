from django.contrib import admin
from .models import (
    Ingredient,
    Tag,
    Recipe,
    IngredientRecipe,
    Favorite,
    ShoppingCart
)

admin.site.register(Recipe)
admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(IngredientRecipe)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
