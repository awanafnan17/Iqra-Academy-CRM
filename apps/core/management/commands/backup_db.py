import os
import subprocess
import shutil
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

class Command(BaseCommand):
    help = "Safely backs up the configured database (MySQL or SQLite) to a secure local folder."

    def handle(self, *args, **options):
        # 1. Get default database connection parameters
        db_config = settings.DATABASES.get("default")
        if not db_config:
            raise CommandError("No 'default' database configuration found in Django settings.")

        engine = db_config.get("ENGINE")
        db_name = db_config.get("NAME")
        db_user = db_config.get("USER")
        db_password = db_config.get("PASSWORD")
        db_host = db_config.get("HOST", "localhost")
        db_port = db_config.get("PORT", "3306")

        # 2. Setup backup directory inside the project root
        backup_dir = os.path.join(settings.BASE_DIR, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if "mysql" in engine:
            filename = f"backup_{db_name}_{timestamp}.sql"
            filepath = os.path.join(backup_dir, filename)

            # Command arguments for mysqldump
            cmd = [
                "mysqldump",
                f"--host={db_host}",
                f"--port={db_port}",
                f"--user={db_user}",
                db_name,
            ]

            # Pass MySQL password securely using environment variable
            env = os.environ.copy()
            if db_password:
                env["MYSQL_PWD"] = db_password

            self.stdout.write(f"Initiating MySQL dump for database '{db_name}'...")
            try:
                # Run mysqldump and pipe stdout directly to the destination file
                with open(filepath, "w", encoding="utf-8") as out_file:
                    result = subprocess.run(
                        cmd,
                        env=env,
                        stdout=out_file,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True
                    )
                self.stdout.write(self.style.SUCCESS(f"Database backup successfully created: {filepath}"))
            except subprocess.CalledProcessError as e:
                # Clean up empty/corrupt file on failure
                if os.path.exists(filepath):
                    os.remove(filepath)
                raise CommandError(f"mysqldump failed with error: {e.stderr}")
            except FileNotFoundError:
                # Fallback check or friendly error if mysqldump is not in PATH
                if os.path.exists(filepath):
                    os.remove(filepath)
                raise CommandError("mysqldump utility not found. Ensure MySQL client tools are installed and added to PATH.")

        elif "sqlite" in engine:
            filename = f"backup_{os.path.basename(db_name)}_{timestamp}.sqlite3"
            filepath = os.path.join(backup_dir, filename)

            self.stdout.write(f"Initiating SQLite copy for database file '{db_name}'...")
            if not os.path.exists(db_name):
                raise CommandError(f"SQLite file does not exist at path: {db_name}")
            try:
                shutil.copy2(db_name, filepath)
                self.stdout.write(self.style.SUCCESS(f"SQLite database backup successfully created: {filepath}"))
            except Exception as e:
                raise CommandError(f"SQLite backup failed: {str(e)}")
        else:
            raise CommandError(f"Database engine '{engine}' is not supported by this backup tool.")
