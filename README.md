# Netflix Activity

## Installation

Assignation des variables d'environnement avec `python-dotenv`:
```bash
# .env
export NETFLIX_EMAIL=<my-netflix-email>
export NETFLIX_PASSWORD=<my-netflix-password>
```

## Usage

Téléchargement des titres vus au format CSV (date/titre) :
```bash
poetry install
poetry run netflix-activity --help
```

 - [ ] Choisir le profil,
 - [x] Téléchargement du fichier `.csv` contenant les films vus,
 - [x] Récupérer les films vus,
 - [x] Récupérer les films notés,
 - [ ] Afficher les films vus et notés,
