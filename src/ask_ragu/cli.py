"""`askragu` command line. In the stack: docker compose exec app askragu <command>

index [--full]            index the vault (default: diff since last_commit)
graph neighbors "<note>"  expand from one note and say why each neighbour is there
graph health [--top N]    dangling links, orphans, name/alias collisions, biggest hubs
"""

import argparse
import logging

from ask_ragu import db
from ask_ragu.graph.report import health_report, neighbors_report
from ask_ragu.index.sync import sync
from ask_ragu.settings import settings


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="askragu")
    commands = parser.add_subparsers(dest="command", required=True)
    index = commands.add_parser("index", help="index the vault at VAULT_PATH into Postgres")
    index.add_argument(
        "--full", action="store_true", help="index every note (default: diff since last_commit)"
    )
    graph = commands.add_parser("graph", help="inspect the note graph").add_subparsers(
        dest="graph_command", required=True
    )
    neighbors = graph.add_parser("neighbors", help="expand from one note, with the why")
    neighbors.add_argument("note", help="as you'd link it: name, path, or alias")
    health = graph.add_parser("health", help="dangling links, orphans, collisions, hubs")
    health.add_argument("--top", type=int, default=10, help="hubs to list (default 10)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    with db.connect() as conn:
        if args.command == "graph":
            if args.graph_command == "neighbors":
                print(neighbors_report(conn, args.note))
            else:
                print(health_report(conn, args.top))
            return
        db.migrate(conn)  # no-op when the app has already migrated
        sync(conn, settings.vault_path, full=args.full)
