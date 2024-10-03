from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps

class Command(BaseCommand):
    help = 'Resets the entire database except for the User model and related tables'

    def handle(self, *args, **kwargs):
        # List of tables you don't want to delete
        keep_tables = [
            'auth_user',               # User model
            'auth_group',              # Groups for permissions
            'auth_permission',         # Permissions
            'django_content_type',     # Content types
            'auth_user_groups',        # User-Group relationships
            'auth_user_user_permissions',  # User-Permission relationships
        ]

        # Get the list of all table names from the database
        with connection.cursor() as cursor:
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
            tables = cursor.fetchall()

        # Filter out the tables you want to keep
        tables_to_delete = [table[0] for table in tables if table[0] not in keep_tables]

        # Disable foreign key checks to avoid constraint errors during deletion
        with connection.cursor() as cursor:
            cursor.execute('SET session_replication_role = replica;')
            self.stdout.write(self.style.WARNING('Foreign key constraints disabled.'))

            # Truncate all other tables
            for table in tables_to_delete:
                cursor.execute(f'TRUNCATE TABLE "{table}" CASCADE;')
                self.stdout.write(self.style.SUCCESS(f'Truncated {table}'))

            # Re-enable foreign key checks
            cursor.execute('SET session_replication_role = DEFAULT;')
            self.stdout.write(self.style.WARNING('Foreign key constraints re-enabled.'))

        self.stdout.write(self.style.SUCCESS('Database reset except for User model and related tables.'))
