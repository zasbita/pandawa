"""Smoke tests: package imports and CLI entrypoint exist."""

import importlib


def test_package_imports():
    mod = importlib.import_module("pandawa_cli")
    assert callable(mod.main)


def test_cli_help_runs():
    from typer.testing import CliRunner

    from pandawa_cli import app

    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
