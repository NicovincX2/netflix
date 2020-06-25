import click.testing
import pytest

from netflix_activity import netflix_selenium


@pytest.fixture
def runner():
    return click.testing.CliRunner()


@pytest.mark.e2e
def test_main_succeeds_in_production_env(runner):
    result = runner.invoke(netflix_selenium.main)
    assert result.exit_code == 0


def test_main_succeeds_in_headless_mode(runner):
    result = runner.invoke(netflix_selenium.main, ["--headless=False"])
    assert result.exit_code == 0
