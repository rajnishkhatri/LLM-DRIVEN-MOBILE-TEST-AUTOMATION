"""`python -m ari_demo "question" --persona treasurer [--inject-timeout]`."""
from .app import main

if __name__ == "__main__":
    raise SystemExit(main())
