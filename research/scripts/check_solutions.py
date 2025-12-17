#!/usr/bin/env python3
"""
Check solution coverage: Expected (models × problems × variants) vs Actual (solutions/).

Usage:
    python check_solutions.py
    python check_solutions.py --no-color
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from frontier_cs.models import get_model_prefix, sanitize_problem_name


class Colors:
    """ANSI color codes."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"

    _enabled = True

    @classmethod
    def disable(cls):
        cls._enabled = False

    @classmethod
    def c(cls, text: str, color: str) -> str:
        if not cls._enabled:
            return text
        return f"{color}{text}{cls.RESET}"


def bold(text: str) -> str:
    return Colors.c(text, Colors.BOLD)

def dim(text: str) -> str:
    return Colors.c(text, Colors.DIM)

def red(text: str) -> str:
    return Colors.c(text, Colors.RED)

def green(text: str) -> str:
    return Colors.c(text, Colors.GREEN)

def yellow(text: str) -> str:
    return Colors.c(text, Colors.YELLOW)

def blue(text: str) -> str:
    return Colors.c(text, Colors.BLUE)

def cyan(text: str) -> str:
    return Colors.c(text, Colors.CYAN)

def warning(text: str) -> str:
    return Colors.c(f"⚠ {text}", Colors.YELLOW)

def error(text: str) -> str:
    return Colors.c(f"✗ {text}", Colors.RED)

def success(text: str) -> str:
    return Colors.c(f"✓ {text}", Colors.GREEN)

def info(text: str) -> str:
    return Colors.c(f"ℹ {text}", Colors.CYAN)


def read_problem_list(path: Path) -> List[str]:
    """Read problems from problems.txt."""
    problems: List[str] = []
    if not path.exists():
        return problems
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Normalize: remove 'research/problems/' prefix
        for prefix in ("research/problems/", "problems/"):
            if line.startswith(prefix):
                line = line[len(prefix):]
                break
        problems.append(line)
    return problems


def read_models_list(path: Path) -> List[str]:
    """Read models from models.txt."""
    models: List[str] = []
    if not path.exists():
        return models
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        models.append(line)
    return models


def read_variant_indices(path: Path) -> List[int]:
    """Read variant indices from num_solutions.txt."""
    if not path.exists():
        return [0]
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    if not lines:
        return [0]
    # Single number = count
    if len(lines) == 1:
        try:
            count = int(lines[0])
            return list(range(count)) if count > 0 else [0]
        except ValueError:
            pass
    # Multiple lines = explicit indices
    indices = []
    for line in lines:
        try:
            indices.append(int(line))
        except ValueError:
            pass
    return indices if indices else [0]


def read_solution_config(solution_dir: Path) -> Optional[str]:
    """Read problem from solution's config.yaml."""
    config_file = solution_dir / "config.yaml"
    if not config_file.exists():
        return None
    try:
        content = config_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("problem:"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return None


def compute_expected(
    problems: List[str],
    models: List[str],
    variants: List[int],
) -> Dict[str, str]:
    """Compute expected solution names -> problem mapping."""
    expected: Dict[str, str] = {}
    for problem in problems:
        problem_name = sanitize_problem_name(problem)
        for model in models:
            model_prefix = get_model_prefix(model)
            for variant_idx in variants:
                suffix = "" if variant_idx == 0 else f"_{variant_idx}"
                solution_name = f"{model_prefix}_{problem_name}{suffix}"
                expected[solution_name] = problem
    return expected


def collect_actual(solutions_dir: Path) -> Dict[str, Optional[str]]:
    """Collect actual solutions from directory."""
    actual: Dict[str, Optional[str]] = {}
    if not solutions_dir.is_dir():
        return actual
    for sol_dir in solutions_dir.iterdir():
        if sol_dir.is_dir() and not sol_dir.name.startswith("."):
            problem = read_solution_config(sol_dir)
            actual[sol_dir.name] = problem
    return actual


def main():
    base_dir = Path(__file__).parent  # research/scripts/
    research_dir = base_dir.parent  # research/
    repo_root = research_dir.parent  # Root of repository

    parser = argparse.ArgumentParser(
        description="Check solution coverage (Expected vs Actual)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--problems-file",
        type=Path,
        default=base_dir / "problems.txt",
        help="Problems file (default: research/scripts/problems.txt)",
    )
    parser.add_argument(
        "--models-file",
        type=Path,
        default=base_dir / "models.txt",
        help="Models file (default: research/scripts/models.txt)",
    )
    parser.add_argument(
        "--variants-file",
        type=Path,
        default=base_dir / "num_solutions.txt",
        help="Variants file (default: research/scripts/num_solutions.txt)",
    )
    parser.add_argument(
        "--solutions-dir",
        type=Path,
        default=repo_root / "solutions",
        help="Solutions directory (default: solutions/)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    args = parser.parse_args()

    if args.no_color:
        Colors.disable()

    # Read config files
    problems = read_problem_list(args.problems_file) if args.problems_file.exists() else []
    models = read_models_list(args.models_file) if args.models_file.exists() else []
    variants = read_variant_indices(args.variants_file) if args.variants_file.exists() else [0]

    if not problems:
        print(warning(f"No problems found in {args.problems_file}"))
    if not models:
        print(warning(f"No models found in {args.models_file}"))

    # Compute expected and actual
    expected = compute_expected(problems, models, variants) if problems and models else {}
    actual = collect_actual(args.solutions_dir)

    # Analyze
    expected_set = set(expected.keys())
    actual_set = set(actual.keys())

    generated = expected_set & actual_set  # Expected and exists
    missing = expected_set - actual_set  # Expected but not generated
    extra = actual_set - expected_set  # Exists but not expected

    # Solutions without config.yaml
    no_config = {name for name, problem in actual.items() if problem is None}

    # Print report
    print()
    line = "=" * 60
    print(cyan(line))
    print(cyan(bold("Solution Coverage Report")))
    print(cyan(line))
    print()

    total_expected = len(expected)
    total_generated = len(generated)
    total_missing = len(missing)
    total_extra = len(extra)

    print(f"  Expected (models × problems × variants): {bold(str(total_expected))}")
    print(f"  Generated (expected & exists): {green(bold(str(total_generated)))}")
    print(f"  Missing (expected but not generated): {yellow(bold(str(total_missing)))}")
    print(f"  Extra (exists but not expected): {blue(bold(str(total_extra)))}")
    print()

    # Coverage bar
    if total_expected > 0:
        coverage = total_generated / total_expected
        bar_width = 40
        filled = int(bar_width * coverage)
        bar = "█" * filled + "░" * (bar_width - filled)
        pct = f"{coverage * 100:.1f}%"
        color = green if coverage > 0.8 else yellow if coverage > 0.3 else red
        print(f"  Coverage: [{color(bar)}] {color(pct)}")
        print()

    # Missing by model
    if missing:
        print(warning(f"{total_missing} solutions not yet generated:"))
        by_model: Dict[str, int] = defaultdict(int)
        for name in missing:
            prefix = name.split("_", 1)[0]
            by_model[prefix] += 1
        for prefix in sorted(by_model.keys()):
            print(f"    {prefix}: {by_model[prefix]} missing")
        print()

    # Extra solutions
    if extra:
        print(info(f"{total_extra} extra solutions (not in expected set):"))
        for name in sorted(extra)[:10]:
            problem = actual.get(name, "???")
            print(f"    {dim(name)}: {problem or dim('no config.yaml')}")
        if len(extra) > 10:
            print(f"    {dim(f'... and {len(extra) - 10} more')}")
        print()

    # Solutions without config.yaml
    if no_config:
        print(error(f"{len(no_config)} solutions missing config.yaml:"))
        for name in sorted(no_config)[:10]:
            print(f"    {red(name)}")
        if len(no_config) > 10:
            print(f"    {dim(f'... and {len(no_config) - 10} more')}")
        print()

    # Summary
    print(dim("─" * 40))
    if total_missing == 0 and len(no_config) == 0:
        print(success("All expected solutions are generated with valid config.yaml"))
    else:
        if total_missing > 0:
            print(f"  Run {bold('generate_solutions.py')} to generate missing solutions")
        if no_config:
            print(f"  Fix solutions missing {bold('config.yaml')}")
    print(dim("─" * 40))

    # Exit code
    return 1 if (no_config or total_missing > 0) else 0


if __name__ == "__main__":
    sys.exit(main())
