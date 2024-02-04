from django.core.management import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        data = [
            {'name': 'Обед', 'color': '#05F210', 'slug': 'dinner'},
            {'name': 'Завтрак', 'color': '#DA15E8', 'slug': 'breakfast'},
            {'name': 'Ужин', 'color': '#D64A27', 'slug': 'supper'}]
        Tag.objects.bulk_create(Tag(**tag) for tag in data)
        print('Тэги загружены')
