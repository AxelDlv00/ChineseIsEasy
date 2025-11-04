#!/usr/bin/env python3
"""
sample_lines.py

Display N consecutive random lines from a large text file without loading it into memory.

Usage:
    python sample_lines.py --file path/to/file.txt --n 5

Example:
    python sample_lines.py --file data/fr.txt --n 10
"""

import os
import random
import argparse


def print_random_lines(filepath: str, n: int):
    """
    Print N consecutive random lines from a text file.

    Parameters
    ----------
    filepath : str
        Path to the text file.
    n : int
        Number of consecutive lines to display.
    """

    # Ensure file exists
    if not os.path.exists(filepath):
        print(f"[Error] File not found: {filepath}")
        return

    # First pass: count total number of lines efficiently
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        total_lines = sum(1 for _ in f)

    if total_lines == 0:
        print("[Error] File is empty.")
        return

    if total_lines < n:
        print(f"[Warning] File only contains {total_lines} lines (less than requested {n}).")
        n = total_lines

    # Pick a random start index
    start_index = random.randint(0, total_lines - n)

    # Second pass: jump to that index and print N lines
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for current_line, line in enumerate(f):
            if current_line == start_index:
                print(f"\n--- Random snippet starting at line {start_index:,} ---\n")
                print(line.strip())
                for _ in range(n - 1):
                    try:
                        print(next(f).strip())
                    except StopIteration:
                        break
                print(f"\n--- End of snippet ---\n")
                break


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Display N consecutive random lines from a large text file."
    )
    parser.add_argument("--file", "-f", default="data/fr.txt", help="Path to the input text file")
    parser.add_argument("--n", "-n", type=int, default=10, help="Number of lines to display (default: 5)")
    args = parser.parse_args()

    print_random_lines(args.file, args.n)


if __name__ == "__main__":
    main()
