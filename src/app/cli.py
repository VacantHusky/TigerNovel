from __future__ import annotations

import argparse
from pathlib import Path

from app.core.orchestrator import Orchestrator


def main() -> None:
    parser = argparse.ArgumentParser(prog="tigernovel")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_create = sub.add_parser("create-book", help="Create a new novel project")
    p_create.add_argument("--slug", required=True)
    p_create.add_argument("--title")
    p_create.add_argument("--synopsis")
    p_create.add_argument("--characters")
    p_create.add_argument("--worldbuilding")

    p_write = sub.add_parser("write-chapter", help="Write one chapter with review loop")
    p_write.add_argument("--slug", required=True)
    p_write.add_argument("--chapter", required=True, type=int)
    p_write.add_argument("--brief")
    p_write.add_argument("--max-rounds", type=int, default=5)

    args = parser.parse_args()

    root = Path.cwd()
    orch = Orchestrator(root)

    if args.cmd == "create-book":
        path = orch.create_book(
            slug=args.slug,
            title=args.title,
            synopsis=args.synopsis,
            characters=args.characters,
            worldbuilding=args.worldbuilding,
        )
        print(f"Book created: {path}")
        return

    if args.cmd == "write-chapter":
        path = orch.write_chapter(
            slug=args.slug,
            chapter_no=args.chapter,
            brief=args.brief,
            max_rounds=args.max_rounds,
        )
        print(f"Chapter finalized: {path}")
        return


if __name__ == "__main__":
    main()
