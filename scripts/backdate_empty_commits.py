#!/usr/bin/env python3
"""Create empty Git commits with randomized backdated timestamps.

This script is intentionally local-first: it operates on the current working
repository, verifies that the current directory is inside a Git work tree, and
then creates ``--allow-empty`` commits with randomized author/committer dates.

Example:
    python scripts/backdate_empty_commits.py --count 50 \
        --start-date 2026-05-07 --end-date 2026-06-02 \
        --message "Docs: update documentation"
"""

from __future__ import annotations

import argparse
import os
import random
import subprocess
import sys
from datetime import date, datetime, time, timedelta, timezone


DEFAULT_COUNT = 50
DEFAULT_START_DATE = "2026-05-07"
DEFAULT_END_DATE = "2026-06-02"
DEFAULT_COMMIT_MESSAGE = "Docs: update documentation"


def parse_date(value: str) -> date:
    """Parse a YYYY-MM-DD date string for CLI arguments."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a valid date; expected YYYY-MM-DD"
        ) from exc


def ensure_git_repository() -> None:
    """Fail fast unless the script is being run inside a Git work tree."""
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0 or result.stdout.strip() != "true":
        message = result.stderr.strip() or "current directory is not inside a Git repository"
        raise RuntimeError(message)


def random_datetime_between(start: date, end: date) -> datetime:
    """Return a random timezone-aware UTC datetime between two inclusive dates."""
    if end < start:
        raise ValueError("end date must be on or after start date")

    start_dt = datetime.combine(start, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(end, time.max, tzinfo=timezone.utc)
    span_seconds = int((end_dt - start_dt).total_seconds())
    return start_dt + timedelta(seconds=random.randint(0, span_seconds))


def git_commit_with_date(commit_message: str, commit_dt: datetime) -> None:
    """Create one empty commit using the supplied author and committer date."""
    env = os.environ.copy()
    # Git accepts ISO-8601 style timestamps with timezone offsets.
    git_date = commit_dt.isoformat(timespec="seconds")
    env["GIT_AUTHOR_DATE"] = git_date
    env["GIT_COMMITTER_DATE"] = git_date

    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", commit_message],
        env=env,
        check=True,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface for the commit generator."""
    parser = argparse.ArgumentParser(
        description="Create empty Git commits with random dates in the current repository."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_COUNT,
        help=f"number of empty commits to create (default: {DEFAULT_COUNT})",
    )
    parser.add_argument(
        "--start-date",
        type=parse_date,
        default=parse_date(DEFAULT_START_DATE),
        help=f"earliest commit date as YYYY-MM-DD (default: {DEFAULT_START_DATE})",
    )
    parser.add_argument(
        "--end-date",
        type=parse_date,
        default=parse_date(DEFAULT_END_DATE),
        help=f"latest commit date as YYYY-MM-DD (default: {DEFAULT_END_DATE})",
    )
    parser.add_argument(
        "--message",
        default=DEFAULT_COMMIT_MESSAGE,
        help=f"commit message to use (default: {DEFAULT_COMMIT_MESSAGE!r})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="optional random seed for reproducible generated dates",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the empty-commit generation workflow."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.count < 1:
        parser.error("--count must be at least 1")
    if args.end_date < args.start_date:
        parser.error("--end-date must be on or after --start-date")
    if args.seed is not None:
        random.seed(args.seed)

    try:
        ensure_git_repository()
        for index in range(1, args.count + 1):
            commit_dt = random_datetime_between(args.start_date, args.end_date)
            git_commit_with_date(args.message, commit_dt)
            print(f"Created empty commit {index}/{args.count} dated {commit_dt.isoformat(timespec='seconds')}")
    except (RuntimeError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
