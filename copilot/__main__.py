import argparse
import logging
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="copilot",
        description="Oracle Integration Copilot — plain-English requirement → OIC design spec",
    )
    parser.add_argument("requirement", help="Plain-English integration requirement")
    parser.add_argument("--output", "-o", metavar="FILE", help="Write Markdown output to FILE instead of stdout")
    parser.add_argument("--no-critic", action="store_true", help="Skip the critic review pass")
    parser.add_argument("--k", type=int, default=6, metavar="N", help="Number of docs to retrieve (default: 6)")
    parser.add_argument("--model", metavar="MODEL", help="Override the Claude model ID")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )

    if args.model:
        import copilot.config as _config
        _config.CLAUDE_MODEL = args.model

    from copilot.parser import parse_requirement
    from copilot.designer import design
    from copilot.renderers.markdown import render

    logging.getLogger(__name__).info("Parsing requirement …")
    intent = parse_requirement(args.requirement)

    logging.getLogger(__name__).info(
        "Pattern: %s | %s → %s", intent.pattern, intent.source_system, intent.target_system
    )

    spec = design(intent, k=args.k, use_critic=not args.no_critic)
    output = render(spec)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Spec written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
