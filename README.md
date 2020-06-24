# Netflix Activity

## Installation

Assignation des variables d'environnement :
```bash
export NETFLIX_EMAIL="<my-netflix-email>"
export NETFLIX_PASSWORD="<my-netflix-password>"
```

Installation de `selenium` :
```bash
python3 -m pip install selenium
```

## Usage

Téléchargement des titres vus au format CSV (date/titre) :
```bash
python3 netflix_selenium.py
```
