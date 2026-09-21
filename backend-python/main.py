"""Backward-compatible CLI entrypoint for :mod:`app.main`."""

from app.main import *  # noqa: F401,F403


if __name__ == "__main__":
    from app.main import main

    main()
