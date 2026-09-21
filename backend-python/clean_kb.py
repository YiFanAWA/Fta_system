"""Backward-compatible CLI entrypoint for :mod:`workflows.clean_kb`."""

from workflows.clean_kb import *  # noqa: F401,F403


if __name__ == "__main__":
    from workflows.clean_kb import main

    main()
