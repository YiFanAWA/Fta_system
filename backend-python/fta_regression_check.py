"""Backward-compatible CLI entrypoint for :mod:`fta.fta_regression_check`."""

from fta.fta_regression_check import *  # noqa: F401,F403


if __name__ == "__main__":
    from fta.fta_regression_check import run_regression

    raise SystemExit(run_regression())
