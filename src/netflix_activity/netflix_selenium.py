#!/usr/bin/env python3


"""
netflix_selenium.py : Login sur Netflix pour télécharger son activité
"""


from collections import defaultdict
from contextlib import contextmanager
import json
import os
import sys
import time

import click
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.expected_conditions import (
    element_to_be_clickable,
    staleness_of,
)
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


class Netflix:
    download_dir = os.path.dirname(os.path.abspath(__file__))

    email_id = "id_userLoginId"
    password_id = "id_password"

    download_file_name = "NetflixViewingHistory.csv"
    download_id = "viewing-activity-footer-download"

    page_toggle_class_name = "pageToggle"
    li_class_name = "retableRow"
    current_profile_class_name = "current-profile"
    profiles_class_name = "profile-selector"

    load_next_entries_button_css = "button[class='btn btn-blue btn-small']"
    dates_css = "div[class='col date nowrap']"
    titles_css = "a[href^='/title/']"

    viewingactivity_url = "https://www.netflix.com/fr/viewingactivity"

    def __init__(self, headless):
        self.driver = self.__get_driver_firefox(headless)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.driver.quit()

    @staticmethod
    def __get_driver_firefox(headless):
        """Renvoie le driver Firefox avec dossier de téléchargement personnalisé"""

        options = Options()
        options.headless = headless
        # To prevent download dialog
        options.set_preference("browser.download.folderList", 2)  # custom location
        options.set_preference("browser.download.dir", Netflix.download_dir)
        options.set_preference(
            "browser.helperApps.neverAsk.saveToDisk",
            "text/plain,text/x-csv,text/csv,application/csv,text/comma-separated-values,text/x-comma-separated-values,text/tab-separated-values",
        )

        driver = webdriver.Firefox(options=options)
        driver.get(
            "https://www.netflix.com/SwitchProfile?tkn=7J6GIXWIFFA45FGWEV7JRBD7MY"
        )  # nicolas token

        return driver

    def login(self):
        """Identification de l'utilisateur sur Netflix.

        Requires globals EMAIL and PASSWORD
        """

        with handle_NoSuchElementException(Netflix.email_id):
            self.driver.find_element_by_id(Netflix.email_id).send_keys(EMAIL)

        with handle_NoSuchElementException(Netflix.password_id):
            entry = self.driver.find_element_by_id(Netflix.password_id)

        entry.send_keys(PASSWORD)
        with wait_for_page_load(self.driver):
            entry.submit()

    def view_activity(self):
        """Déplacement sur la page de visualisation de l'activité de l'utilisateur"""

        with wait_for_page_load(self.driver):
            self.driver.get(Netflix.viewingactivity_url)

    def download_seen(self):
        """Téléchargement de l'historique d'activité au format csv

        Requires a previous call to view_activity()
        """

        with handle_NoSuchElementException(Netflix.download_id):
            self.driver.find_element_by_class_name(Netflix.download_id).click()

        # On attend la fin du téléchargement pour fermer le driver
        # Si le fichier est déjà présent, il n'a pas le temps d'être téléchargé
        while not os.path.exists(
            Netflix.download_dir + "/" + Netflix.download_file_name
        ):
            print(
                f"Fichier téléchargé: {Netflix.download_dir}/{Netflix.download_file_name}"
            )
            time.sleep(1)

    def get_rated(self):
        """Récupération des titres évalués au format csv titre/date

        Requires a previous call to view_activity()
        """

        # Vérification qu'on est sur la page des titres évalués
        if Netflix.download_id in self.driver.page_source:
            self.__page_toggle()

        return self.__get_titles()

    def get_seen(self):
        """Récupération des titres vus au format csv titre/date

        Requires a previous call to view_activity()
        """

        # Vérification qu'on est sur la page des titres vus
        if Netflix.download_id not in self.driver.page_source:
            self.__page_toggle()

        return self.__get_titles()

    def __page_toggle(self):
        """Changement de page bidirectionnel entre les titres vus/évalués"""

        page_toggle = self.driver.find_element_by_class_name(
            Netflix.page_toggle_class_name
        )
        page_toggle.find_element_by_tag_name("a").click()

    def __get_titles(self):
        """Récupération des titres au format csv titre/date"""

        titles_dict = defaultdict(list)

        while True:
            try:
                WebDriverWait(self.driver, 1).until(
                    element_to_be_clickable(
                        (By.CSS_SELECTOR, Netflix.load_next_entries_button_css)
                    )
                ).click()
            except TimeoutException:
                break

        # titles = self.driver.find_elements_by_class_name(Netflix.li_class_name)
        # for title in titles:
        #     # Le premier tag div contient la date de visionnage
        #     titles_dict["dates"].append(title.find_element_by_tag_name("div").text)
        #     titles_dict["titles"].append(title.find_element_by_tag_name("a").text)

        titles_dict["dates"] = [
            div.text
            for div in self.driver.find_elements_by_css_selector(Netflix.dates_css)
        ]
        titles_dict["titles"] = [
            div.text
            for div in self.driver.find_elements_by_css_selector(Netflix.titles_css)
        ]

        return titles_dict

    def get_current_profile(self):
        """Récupération du profile actuel"""

        with handle_NoSuchElementException(Netflix.profiles_class_name):
            return (
                self.driver.find_element_by_class_name(
                    Netflix.current_profile_class_name
                )
                .find_element_by_tag_name("img")
                .get_attribute("alt")
            )

    def set_profile(self, new_profile):
        """Changement de profile"""

        with handle_NoSuchElementException(Netflix.profiles_class_name):
            profiles = self.driver.find_element_by_class_name(
                Netflix.profiles_class_name
            )
        ActionChains(self.driver).move_to_element(profiles).perform()

        WebDriverWait(self.driver, 5).until(
            element_to_be_clickable((By.CSS_SELECTOR, f"img[alt='{new_profile}']"))
        ).click()

    def save_to_json(self, titles_dict, filename):
        """Sauvegarde de titles_dict dans le fichier .json filename"""

        with open(
            Netflix.download_dir + "/" + filename, "w", encoding="utf-8"
        ) as json_file:
            json.dump(titles_dict, json_file, ensure_ascii=False, indent=4)


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

    with Netflix(headless) as netflix:
        netflix.login()
        netflix.view_activity()

        current_profile = netflix.get_current_profile()
        print(current_profile)
        netflix.set_profile("vincent")
        netflix.view_activity()
        new_profile = netflix.get_current_profile()
        print(new_profile)

        # # On peut ne pas noter des films/séries...
        # rated_titles_dict = netflix.get_rated()
        # netflix.save_to_json(rated_titles_dict, "rated_titles.json")
        # # ...mais considère que l'utilisateur a visionné au moins un(e) film/série
        # seen_titles_dict = netflix.get_seen()
        # assert seen_titles_dict
        # netflix.save_to_json(seen_titles_dict, "seen_titles.json")

        # netflix.download_seen(download_dir)
