Netflix Activity
===================

Le format JSON des titres vus ou notés est le suivant:

```bash
{
    "28/06/2020": "Assassin's Creed",
    "19/06/2020": "La Momie",
    "04/06/2020": "Green Lantern",
}
```

Après la première exécution de la fonction `main` du fichier `example/main.py`, trois fichiers seront créés:

```
src/
    netflix_activity/
        cookies.pkl
        rated_titles.json
        seen_titles.json
.env
```

Les noms des fichiers JSON suffisent à expliciter leur contenu. Le fichier `cookies.pkl` contient les cookies de votre session Firefox après que le programme vous ai identifié sur Netflix. Lors d'une prochaine exécution du `main`, la procédure de login est remplacée par le chargement des cookies dans la session Firefox.

Si vous voulez changer d'utilisateur Netflix, il faut supprimer le fichier `cookies.pkl` et éditer le `.env` avec les nouveaux identifiants de connexion.

Il est conseillé de supprimer le fichier `cookies.pkl` si vous pensez ne pas relancer le programme sous peu. Toute personne ayant accès à ce fichier pourra se connecter à votre compte Netflix.

## Installation

Installer Firefox.

Créer le fichier `.env` à la racine du projet. Il contient vos identifiants Netflix.
```bash
# .env
export NETFLIX_EMAIL=<my-netflix-email>
export NETFLIX_PASSWORD=<my-netflix-password>
```

Installer [`poetry`](https://python-poetry.org/docs/).

Installer le module:
```bash
poetry install
```

## Usage

```bash
poetry run netflix-activity --help
```

La commande `poetry run netflix-activity` lance la fonction `main` du fichier `example/main.py` sans affichage du navigateur.
N'hésitez pas à modifier cette fonction pour choisir le profil de l'utilisateur.

## Tests

La commande suivante permet de lancer les tests :
```bash
nox -rs tests-3.8
```

 - [x] Choix du profil,
 - [x] Téléchargement du fichier `.csv` contenant les films vus,
 - [x] Récupérer les films vus dans un fichier `.json`,
 - [x] Récupérer les films notés dans un fichier `.json`,
 - [x] Sauvegarde de la session,
