from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from djangoapp.services.subscription_service import generate_subscription_payments

class Command(BaseCommand):
    help = 'Generate subscription payment records for all users'

    def add_arguments(self, parser):
        # Optional: specify a single user
        parser.add_argument(
            '--user',
            type=str,
            help='Username to generate payments for (default: all users)',
        )

    def handle(self, *args, **options):
        username = options.get('user')

        if username: 
            try:
                users = User.objects.filter(is_active=True)
                self.stdout.write(f"Generating payments for user: {username}")

            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User '{username}' not found"))
                return
        else:
            users = User.objects.filter(is_active=True)
            self.stdout.write(f"Generating payments for {users.count()} users")
        
        total_created = 0
        for user in users:
            try:
                count = generate_subscription_payments(user)
                total_created += count
                if count > 0:
                    self.stdout.write(f"    Created {count} payments for {user.username}")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"   Error for {user.username}: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"\nTotal payments created: {total_created}")
        )
                