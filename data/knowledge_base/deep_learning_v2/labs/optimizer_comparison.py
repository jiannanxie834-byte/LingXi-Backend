"""Minimal runnable lab: optimizer comparison."""

from __future__ import annotations

import random


def set_seed(seed: int = 42) -> None:
    random.seed(seed)


def main() -> None:
    set_seed()
    print("LingXi Deep Learning Lab: optimizer comparison")
    print("This lightweight lab is designed for course demonstration.")
    print("Extend it with torch/torchvision in a full local environment.")


if __name__ == "__main__":
    main()
