"""Explicitly authorized alternate sandbox route; original DNS evidence is immutable."""

from pathlib import Path

import fetch_once

if __name__ == "__main__":
    target = Path(__file__).resolve().parent / "authorized-route"
    target.mkdir(exist_ok=False)
    fetch_once.HERE = target
    fetch_once.main()
