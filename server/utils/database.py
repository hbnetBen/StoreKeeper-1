#!../flask/bin/python
import argparse
import os.path
import sys

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(basedir)

from app.server import db, config
from app.models import User
from app.modules.database_maintenance import DatabaseMaintenance


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Database maintenance")
    command = parser.add_mutually_exclusive_group()

    command.add_argument("--create", action="store_true", help="create empty database from model")
    command.add_argument("--migrate", action="store_true", help="migrate database to schema from model")
    command.add_argument("--downgrade", action="store_true", help="downgrade database to previous version")
    command.add_argument("--upgrade", action="store_true", help="upgrade database to next version")
    command.add_argument("-v", "--version", action="store_true", help="get version of current database")

    return parser.parse_args()


def check_repo(have_to_be_created: bool) -> bool:
    exist = os.path.isdir(config.App.MIGRATE_REPO_PATH)
    if have_to_be_created == exist:
        return True

    if have_to_be_created:
        print('\nERROR: Database have to created with --create', file=sys.stderr)
    else:
        print('\nERROR: Database is already created', file=sys.stderr)
    return False


def main() -> int:
    args = parse_arguments()
    if not check_repo(have_to_be_created=not args.create):
        return 1

    if args.create:
        DatabaseMaintenance.create()

        user = User(username="admin", email="admin@localhost", admin=True)
        user.set_password("admin")

        db.session.add(user)
        db.session.commit()
        print("Done")

    elif args.migrate:
        migration = DatabaseMaintenance.migrate()
        print('New migration saved as {!s}'.format(migration))

    elif args.downgrade:
        DatabaseMaintenance.downgrade()

    elif args.upgrade:
        DatabaseMaintenance.upgrade()

    elif args.version:
        pass

    print('Current database version: {:d}'.format(DatabaseMaintenance.get_version()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
