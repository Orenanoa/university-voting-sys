from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create (or reset) the superuser: username admin, password admin123'

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(username='admin')
        user.set_password('admin123')
        user.is_staff = True
        user.is_superuser = True
        user.save()
        self.stdout.write(self.style.SUCCESS('Superuser "admin" is ready.'))
