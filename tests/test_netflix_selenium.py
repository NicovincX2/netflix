import os

import click.testing
import pytest

from netflix_activity import netflix_selenium


#  Liste des profils à modifier
PROFILES = ["dominique.vincent10", "vincent", "nicolas"]


@pytest.fixture
def runner():
    return click.testing.CliRunner()


@pytest.yield_fixture
def netflix_headless(tmp_path):
    headless = True
    netflix_selenium.Netflix.download_dir = str(tmp_path)
    with netflix_selenium.Netflix(headless) as netflix:
        yield netflix


@pytest.mark.e2e
def test_main_succeeds_in_production_env(runner):
    result = runner.invoke(netflix_selenium.main)
    assert result.exit_code == 0


@pytest.mark.e2e
def test_main_succeeds_in_headless_mode(runner):
    result = runner.invoke(netflix_selenium.main, ["--headless=False"])
    assert result.exit_code == 0


def test_switch_profiles(netflix_headless):
    """Changement de profil

    Require global PROFILES
    """

    netflix_headless.view_activity()
    current_profile = netflix_headless.get_current_profile()
    assert current_profile == PROFILES[0]

    netflix_headless.set_profile(PROFILES[1])
    netflix_headless.view_activity()
    new_profile = netflix_headless.get_current_profile()
    assert new_profile == PROFILES[1]

    netflix_headless.set_profile(PROFILES[2])
    netflix_headless.view_activity()
    new_profile = netflix_headless.get_current_profile()
    assert new_profile == PROFILES[2]

    netflix_headless.set_profile(PROFILES[0])
    netflix_headless.view_activity()
    new_profile = netflix_headless.get_current_profile()
    assert new_profile == PROFILES[0]


def test_download_seen(netflix_headless):
    """Téléchargement des titres vus"""

    netflix_headless.download_seen()
    assert os.path.exists(
        netflix_selenium.Netflix.download_dir
        + "/"
        + netflix_selenium.Netflix.download_file_name
    )


def test_get_json(netflix_headless):
    """Téléchargement des titres vus/notés au format json"""

    # On peut ne pas noter des films/séries...
    rated_titles_dict = netflix_headless.get_rated()
    netflix_headless.save_to_json(rated_titles_dict, "rated_titles.json")
    assert os.path.exists(netflix_selenium.Netflix.download_dir + "/rated_titles.json")
    # ...mais on considère que l'utilisateur a visionné au moins un(e) film/série
    seen_titles_dict = netflix_headless.get_seen()
    assert seen_titles_dict
    netflix_headless.save_to_json(seen_titles_dict, "seen_titles.json")
    assert os.path.exists(netflix_selenium.Netflix.download_dir + "/seen_titles.json")
