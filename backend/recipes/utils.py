from rest_framework import serializers
from .models import Recipe

class ShortRecipeSerializer(serializers.ModelSerializer):
    """Serializer for brief recipe representation."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields 