import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
import shared.config as config

load_dotenv()


class Command(BaseCommand):
    help = "Creates an admin user non-interactively if it doesn't exist"

    def handle(self, *args, **options):
        User = get_user_model()

        username = config.DJANGO_SUPERUSER_USERNAME
        password = config.DJANGO_SUPERUSER_PASSWORD
        email = config.DJANGO_SUPERUSER_EMAIL

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username, email=email, password=password
            )
