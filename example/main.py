import os

import click
from dotenv import load_dotenv

from netflix_activity import __version__
from netflix_activity.netflix_selenium import Netflix


load_dotenv(verbose=True)

EMAIL = os.environ.get("NETFLIX_EMAIL")
PASSWORD = os.environ.get("NETFLIX_PASSWORD")


@click.command()
@click.option(
    "--headless",
    "-h",
    default=True,
    type=bool,
    help="Désactive l'affichage du navigateur",
    show_default=True,
)
@click.version_option(version=__version__)
def main(headless):
    """Netflix Activity CLI"""

    with Netflix(headless, EMAIL, PASSWORD) as netflix:
        current_profile = netflix.get_current_profile()
        print(current_profile)

        # netflix.set_profile("vincent")
        # netflix.view_activity()
        # new_profile = netflix.get_current_profile()
        # print(new_profile)
        netflix.set_profile("nicolas")
        netflix.view_activity()
        new_profile = netflix.get_current_profile()
        print(new_profile)

        # On peut ne pas noter des films/séries...
        rated_titles_dict = netflix.get_rated()
        netflix.save_to_json(rated_titles_dict, "rated_titles.json")

        netflix.download_seen()

        # ...mais on considère que l'utilisateur a visionné au moins un(e) film/série
        seen_titles_dict = netflix.get_seen()
        assert seen_titles_dict
        netflix.save_to_json(seen_titles_dict, "seen_titles.json")
