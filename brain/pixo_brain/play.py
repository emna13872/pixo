"""Play a session in the terminal: you are the child.

Usage (from the brain/ folder):
    uv run pixo-play 1.1 --name Sara
    uv run pixo-play 1.1 --name Sara --seed 7     # same random phrase choices every time
"""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
from datetime import datetime
from pathlib import Path

from .channels import ConsoleChannel, LoggingChannel
from .engine import SessionReport, SessionRunner
from .validate import DEFAULT_CONTENT, validate

DEFAULT_LOGS = Path(__file__).resolve().parents[2] / "logs"


def print_report(report: SessionReport, log_path: Path) -> None:
    print("\n--- Session report ---")
    for r in report.results:
        status = "right" if r.success else "missed"
        print(f"  step {r.step:>2}  {r.type:<9} {r.word:<8} {status:<6} in {r.attempts} tries")
    total = len(report.results)
    print(f"  {report.successes}/{total} right, nickname said {report.nickname_count} times")
    print(f"  log: {log_path}")


async def play(session_id: str, nickname: str, content_root: Path, logs: Path, seed: int | None):
    content, issues = validate(content_root)
    if issues:
        for issue in issues:
            print(issue)
        print("\nThe content has problems: fix them first (uv run pixo-validate).")
        return 1
    if session_id not in content.sessions:
        print(f'Unknown session "{session_id}". Available: {", ".join(sorted(content.sessions))}')
        return 1

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    console = ConsoleChannel({w.id: w.text for w in content.words.values()})
    channel = LoggingChannel(console, logs / f"{stamp}_session-{session_id}.jsonl")
    channel.log("start", session=session_id, nickname=nickname, seed=seed, mode="text")
    try:
        runner = SessionRunner(
            content, content.sessions[session_id], nickname, channel, random.Random(seed)
        )
        print(f"=== Session {session_id}: {content.sessions[session_id].title} ===\n")
        report = await runner.run()
        channel.log(
            "end",
            successes=report.successes,
            asks=len(report.results),
            nickname_count=report.nickname_count,
        )
    finally:
        channel.close()
    print_report(report, channel.path)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Play a Pixo session in the terminal.")
    parser.add_argument("session", help='session id, e.g. "1.1"')
    parser.add_argument("--name", default="Sara", help="the child's nickname")
    parser.add_argument("--seed", type=int, default=None, help="fix the random phrase choices")
    parser.add_argument("--content", type=Path, default=DEFAULT_CONTENT)
    parser.add_argument("--logs", type=Path, default=DEFAULT_LOGS)
    args = parser.parse_args(argv)
    try:
        return asyncio.run(play(args.session, args.name, args.content, args.logs, args.seed))
    except (KeyboardInterrupt, EOFError):
        print("\nStopped.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
