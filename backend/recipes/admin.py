from django.contrib import admin
from .models import Ingredient, Recipe, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_display_links = ('name',)
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_display_links = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'author')
    list_display_links = ('title',)
    search_fields = ('title',)
    list_filter = ('author', 'tags')
    autocomplete_fields = ('author', 'tags')
    readonly_fields = ('favorited_count',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('author').prefetch_related('tags', 'ingredients')

    def favorited_count(self, obj):
        return getattr(obj, 'favorited_by', []).count()
    favorited_count.short_description = 'В избранном'
