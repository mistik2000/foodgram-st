import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from JSON file'

    def handle(self, *args, **options):
        path = os.path.join(settings.BASE_DIR, 'data', 'ingredients.json')
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            for item in data:
                Ingredient.objects.get_or_create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit'],
                )
        self.stdout.write(
            self.style.SUCCESS('Successfully loaded ingredients')
        )
