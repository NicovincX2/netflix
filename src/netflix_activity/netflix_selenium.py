#!/usr/bin/env python3


"""
netflix_selenium.py : Login sur Netflix pour télécharger son activité
"""


from collections import defaultdict
from contextlib import contextmanager
import json
import os
import pickle
import time

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
        raise NoSuchElementException


class Netflix:
    download_dir = os.path.dirname(os.path.abspath(__file__))

    #  La suite des variables est propre à Netflix, à changer au besoin
    email_id = "id_userLoginId"
    password_id = "id_password"

    download_file_name = "NetflixViewingHistory.csv"
    download_id = "viewing-activity-footer-download"

    page_toggle_class_name = "pageToggle"
    li_class_name = "retableRow"
    current_profile_class_name = "current-profile"
    profiles_class_name = "profile-selector"

    load_next_entries_button_css = "button[class='btn btn-blue btn-small']"
    # dates_css = "div[class='col date nowrap']"
    # titles_css = "a[href^='/title/']"

    viewingactivity_url = "https://www.netflix.com/fr/viewingactivity"
    login_url = "https://www.netflix.com/fr/login"

    def __init__(self, headless, email, password):
        self.__driver = self.__get_driver_firefox(headless)

        # Chargement des informations de login
        #  Penser à supprimer le fichier cookies.pkl lorsque vous changez les identifiants
        #  dans le .env.
        if os.path.exists(Netflix.download_dir + "/cookies.pkl"):
            cookies = pickle.load(open(Netflix.download_dir + "/cookies.pkl", "rb"))
            for cookie in cookies:
                self.__driver.add_cookie(cookie)
        else:
            self.__login(email, password)

            pickle.dump(
                self.__driver.get_cookies(),
                open(Netflix.download_dir + "/cookies.pkl", "wb"),
            )

        self.view_activity()
        # Initialisation du profil sur celui par défaut
        self.current_profile = self.__get_current_profile()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.__driver.quit()

    @staticmethod
    def __get_driver_firefox(headless):
        """Renvoie le driver Firefox avec dossier de téléchargement personnalisé

        Uses class attributes
            download_dir
        """

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
        #  On se place sur le site de netflix pour charger les cookies
        driver.get("https://www.netflix.com")

        return driver

    def __login(self, email, password):
        """Identification de l'utilisateur sur Netflix.

        Uses class attributes
            login_url
            email_id
            password_id

        Requires parameters email and password
        """
        self.__driver.get(
            Netflix.login_url
        )  # some user token "/SwitchProfile?tkn=<profile_token>"

        with handle_NoSuchElementException(Netflix.email_id):
            self.__driver.find_element_by_id(Netflix.email_id).send_keys(email)

        with handle_NoSuchElementException(Netflix.password_id):
            entry = self.__driver.find_element_by_id(Netflix.password_id)

        entry.send_keys(password)
        with wait_for_page_load(self.__driver):
            entry.submit()

    def view_activity(self):
        """Déplacement sur la page de visualisation de l'activité de l'utilisateur

        Uses class attributes
            viewingactivity_url
        """

        with wait_for_page_load(self.__driver):
            self.__driver.get(Netflix.viewingactivity_url)

    def download_seen(self):
        """Téléchargement du fichier CSV fournit par Netflix

        Uses class attributes
            download_file_name
            download_id
            download_dir

        Requires a previous call to view_activity()
        """

        with handle_NoSuchElementException(Netflix.download_id):
            self.__driver.find_element_by_class_name(Netflix.download_id).click()

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
        """Récupération des titres évalués

        Uses class attributes
            download_id

        Requires a previous call to view_activity()
        """

        # Vérification qu'on est sur la page des titres évalués
        if Netflix.download_id in self.__driver.page_source:
            self.__page_toggle()

        return self.__get_titles()

    def get_seen(self):
        """Récupération des titres vus

        Uses class attributes
            download_id

        Requires a previous call to view_activity()
        """

        # Vérification qu'on est sur la page des titres vus
        if Netflix.download_id not in self.__driver.page_source:
            self.__page_toggle()

        return self.__get_titles()

    def __page_toggle(self):
        """Changement de page bidirectionnel entre les titres vus/évalués

        Uses class attributes
            page_toggle_class_name
        """

        page_toggle = self.__driver.find_element_by_class_name(
            Netflix.page_toggle_class_name
        )
        page_toggle.find_element_by_tag_name("a").click()

    def __get_titles(self):
        """Récupération des titres au format csv titre/date

        Uses class attributes
            load_next_entries_button_css
            dates_css
            titles_css
        """

        titles_dict = defaultdict(str)

        while True:
            try:
                WebDriverWait(self.__driver, 1).until(
                    element_to_be_clickable(
                        (By.CSS_SELECTOR, Netflix.load_next_entries_button_css)
                    )
                ).click()
            except TimeoutException:
                break

        titles = self.__driver.find_elements_by_class_name(Netflix.li_class_name)
        for title in titles:
            # Le premier tag div contient la date de visionnage
            titles_dict[
                title.find_element_by_tag_name("div").text
            ] = title.find_element_by_tag_name("a").text

        # titles_dict["dates"] = [
        #     div.text
        #     for div in self.__driver.find_elements_by_css_selector(Netflix.dates_css)
        # ]
        # titles_dict["titles"] = [
        #     div.text
        #     for div in self.__driver.find_elements_by_css_selector(Netflix.titles_css)
        # ]

        return titles_dict

    def __get_current_profile(self):
        """Récupération du profil actuel

        Uses class attributes
            profiles_class_name
            current_profile_class_name
        """

        with handle_NoSuchElementException(Netflix.profiles_class_name):
            return (
                self.__driver.find_element_by_class_name(
                    Netflix.current_profile_class_name
                )
                .find_element_by_tag_name("img")
                .get_attribute("alt")
            )

    def get_current_profile(self):
        return self.current_profile

    def set_profile(self, new_profile):
        """Changement de profil

        Uses class attributes
            profiles_class_name
        """

        with handle_NoSuchElementException(Netflix.profiles_class_name):
            profiles = self.__driver.find_element_by_class_name(
                Netflix.profiles_class_name
            )

        mouse_hoover = ActionChains(self.__driver)
        mouse_hoover.move_to_element(profiles).perform()
        # reset the action
        mouse_hoover.reset_actions()

        new_profile_css = f"img[alt='{new_profile}']"
        try:
            WebDriverWait(self.__driver, 5).until(
                element_to_be_clickable((By.CSS_SELECTOR, new_profile_css))
            ).click()
        except TimeoutException:
            print("The new profile can't be found")
            raise TimeoutException

        self.current_profile = new_profile

    def save_to_json(self, titles_dict, filename):
        """Sauvegarde de titles_dict dans le fichier .json filename

        Uses class attributes
            download_dir
        """

        with open(
            Netflix.download_dir + "/" + filename, "w", encoding="utf-8"
        ) as json_file:
            json.dump(titles_dict, json_file, ensure_ascii=False, indent=4)
