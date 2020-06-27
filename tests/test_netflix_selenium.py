import click.testing
import pytest

from netflix_activity import netflix_selenium


PROFILES = ["dominique.vincent10", "vincent", "nicolas"]


@pytest.fixture
def runner():
    return click.testing.CliRunner()


@pytest.mark.e2e
def test_main_succeeds_in_production_env(runner):
    result = runner.invoke(netflix_selenium.main)
    assert result.exit_code == 0


@pytest.mark.e2e
def test_main_succeeds_in_headless_mode(runner):
    result = runner.invoke(netflix_selenium.main, ["--headless=False"])
    assert result.exit_code == 0


def test_switch_profiles():
    """Changement de profil

    Require global PROFILES
    """

    headless = True
    with netflix_selenium.Netflix(headless) as netflix:
        netflix.login()
        netflix.view_activity()

        current_profile = netflix.get_current_profile()
        assert current_profile == PROFILES[0]

        netflix.set_profile(PROFILES[1])
        netflix.view_activity()
        new_profile = netflix.get_current_profile()
        assert new_profile == PROFILES[1]

        netflix.set_profile(PROFILES[2])
        netflix.view_activity()
        new_profile = netflix.get_current_profile()
        assert new_profile == PROFILES[2]

        netflix.set_profile(PROFILES[0])
        netflix.view_activity()
        new_profile = netflix.get_current_profile()
        assert new_profile == PROFILES[0]
