"""`askragu` command line. In the stack: docker compose exec app askragu index [--full]"""

import argparse
import logging

from ask_ragu import db
from ask_ragu.index.sync import sync
from ask_ragu.settings import settings


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="askragu")
    commands = parser.add_subparsers(dest="command", required=True)
    index = commands.add_parser("index", help="index the vault at VAULT_PATH into Postgres")
    index.add_argument(
        "--full", action="store_true", help="index every note (default: diff since last_commit)"
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    with db.connect() as conn:
        db.migrate(conn)  # no-op when the app has already migrated
        sync(conn, settings.vault_path, full=args.full)
