#!/usr/bin/env python3


"""
netflix_selenium.py : Login sur Netflix pour aller voir son activité
"""


from contextlib import contextmanager
import os
import sys
import time

import click
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.webdriver.support.ui import WebDriverWait

from . import __version__


load_dotenv(verbose=True)

EMAIL = os.environ.get("NETFLIX_EMAIL")
PASSWORD = os.environ.get("NETFLIX_PASSWORD")


@contextmanager
def wait_for_page_load(driver, timeout=30):
    """Attente du chargement de la page, utile avant d'effectuer des opérations sur la page"""
    old_page = driver.find_element_by_tag_name("html")
    yield
    WebDriverWait(driver, timeout).until(staleness_of(old_page))


@contextmanager
def handle_NoSuchElementException(element):
    """Gestion de l'exception NoSuchElementException lors de la recherche d'element dans le DOM"""
    try:
        yield
    except NoSuchElementException as err:
        print(f"L'élément {element} n'a pas été trouvé:", err)
        sys.exit(1)


def login(driver):
    """Identification de l'utilisateur sur netflix.

    Requires globals EMAIL and PASSWORD
    """
    email_id = "id_userLoginId"
    password_id = "id_password"

    with handle_NoSuchElementException(email_id):
        driver.find_element_by_id(email_id).send_keys(EMAIL)

    with handle_NoSuchElementException(password_id):
        entry = driver.find_element_by_id(password_id)

    entry.send_keys(PASSWORD)
    entry.submit()  # wait for the next page to load


def view_activity(driver):
    """Déplacement sur la page de visualisation de l'activité de l'utilisateur"""
    # On change de page
    with wait_for_page_load(driver):
        pass
    driver.get("https://www.netflix.com/fr/viewingactivity")


def download_seen(driver):
    """Téléchargement de l'historique d'activité au format csv"""

    download_id = "viewing-activity-footer-download"
    with handle_NoSuchElementException(download_id):
        driver.find_element_by_class_name(download_id).click()


def get_rated(driver):
    """Récupération des titres évalués au format csv titre/date"""
    pass


def get_seen(driver):
    """Récupération des titres vus au format csv titre/date"""
    pass


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

    download_dir = os.path.dirname(os.path.abspath(__file__))
    file_name = "NetflixViewingHistory.csv"

    options = Options()
    options.headless = headless
    # To prevent download dialog
    options.set_preference("browser.download.folderList", 2)  # custom location
    options.set_preference("browser.download.dir", download_dir)
    options.set_preference(
        "browser.helperApps.neverAsk.saveToDisk",
        "text/plain,text/x-csv,text/csv,application/csv,text/comma-separated-values,text/x-comma-separated-values,text/tab-separated-values",
    )

    driver = webdriver.Firefox(options=options)
    driver.get(
        "https://www.netflix.com/SwitchProfile?tkn=7J6GIXWIFFA45FGWEV7JRBD7MY"
    )  # nicolas profile token
    # L'URL https://www.netflix.com/fr/viewingactivity renvoie directement sur l'historique du premier profil créé

    login(driver)
    view_activity(driver)
    download_seen(driver)

    # On attend la fin du téléchargement pour fermer le driver
    # Si le fichier est déjà présent, il n'a pas le temps d'être téléchargé
    while not os.path.exists(download_dir + "/" + file_name):
        print(f"Fichier téléchargé: {download_dir}/{file_name}")
        time.sleep(1)
    driver.quit()
