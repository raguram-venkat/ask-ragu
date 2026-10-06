"""`askragu` command line. In the stack: docker compose exec app askragu index --full"""

import argparse
import logging

from ask_ragu import db
from ask_ragu.index.full import index_full
from ask_ragu.settings import settings


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="askragu")
    commands = parser.add_subparsers(dest="command", required=True)
    index = commands.add_parser("index", help="index the vault at VAULT_PATH into Postgres")
    index.add_argument("--full", action="store_true", help="walk every note in the vault")
    args = parser.parse_args(argv)
    if not args.full:
        parser.error("only `index --full` exists so far (incremental sync: Sprint 2 Task 8)")

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    with db.connect() as conn:
        db.migrate(conn)  # no-op when the app has already migrated
        index_full(conn, settings.vault_path)
