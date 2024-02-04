from rest_framework import routers
from django.urls import include, path

from .views import (
    CustomUsersViewSet,
    TagsViewSet,
    RecipesViewSet,
    IngredientsViewSet,
)

app_name = 'api'

router = routers.DefaultRouter()

router.register('tags', TagsViewSet, basename='tags')
router.register('ingredients', IngredientsViewSet, basename='ingredients')
router.register('users', CustomUsersViewSet, basename='users')
router.register('recipes', RecipesViewSet, basename='recipes')


urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
