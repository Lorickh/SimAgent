import argparse
import sys
from simagent.agent import Agent


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SimAgent local agentic AI")
    parser.add_argument("--repo", required=True, help="Path to target repo")
    parser.add_argument("--index", default=None, help="Path to index cache (optional)")
    parser.add_argument("--max-turns", type=int, default=8, help="Max tool/LLM turns per query")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    agent = Agent(repo_path=args.repo, index_path=args.index, max_turns=args.max_turns)
    agent.run_repl()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
