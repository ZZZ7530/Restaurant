import argparse
import getpass
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from werkzeug.security import generate_password_hash

from app import create_app
from app.repositories.db import get_cursor


def main():
    parser = argparse.ArgumentParser(description="Create or update an admin user.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--display-name", default="系統管理員")
    parser.add_argument("--role", choices=("owner", "staff"), default="owner")
    args = parser.parse_args()

    password = getpass.getpass("Admin password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if not password:
        raise SystemExit("Password cannot be empty.")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    password_hash = generate_password_hash(password)
    app = create_app()
    with app.app_context():
        with get_cursor(commit=True) as cursor:
            cursor.execute(
                """
                INSERT INTO admin_users (
                    username, password_hash, display_name, role, is_active
                )
                VALUES (%s, %s, %s, %s, 1)
                ON DUPLICATE KEY UPDATE
                    password_hash = VALUES(password_hash),
                    display_name = VALUES(display_name),
                    role = VALUES(role),
                    is_active = 1
                """,
                (args.username, password_hash, args.display_name, args.role),
            )

    print("Admin user has been created or updated.")


if __name__ == "__main__":
    main()
