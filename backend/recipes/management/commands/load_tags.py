from django.core.management.base import BaseCommand
from recipes.models import Tag

class Command(BaseCommand):
    help = 'Load initial tags'

    def handle(self, *args, **options):
        tags = [
            {'name': 'Завтрак', 'color': '#E26C2D', 'slug': 'breakfast'},
            {'name': 'Обед', 'color': '#49B64F', 'slug': 'lunch'},
            {'name': 'Ужин', 'color': '#8775D2', 'slug': 'dinner'},
        ]

        for tag_data in tags:
            Tag.objects.get_or_create(**tag_data)

        self.stdout.write(self.style.SUCCESS('Successfully loaded tags')) 