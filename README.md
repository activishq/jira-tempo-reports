# Jira-Tempo Activity Report Generator

## Description
Ce projet est une application Streamlit qui génère des rapports d'activité basés sur les données de Jira et Tempo. Il permet de visualiser et d'analyser le temps passé sur les projets, les temps facturables et non facturables, ainsi que d'autres métriques importantes pour la gestion de projet et la facturation.

## Fonctionnalités
- Génération de rapports d'activité pour le département et les utilisateurs individuels
- Calcul et affichage des métriques clés (temps total enregistré, temps facturable, ratio de facturation, etc.)
- Visualisation des données sous forme de graphiques et de tableaux
- Filtrage des données par période et par utilisateur
- Stockage des données dans une base de données PostgreSQL
- Traitement flexible des données pour des périodes spécifiques
- test

## Prérequis
- Python 3.10
- Compte Jira avec accès API
- Compte Tempo avec accès API
- PostgreSQL

## Installation
1. Clonez le dépôt :
   ```
   git clone https://github.com/votre-nom/jira-tempo-report.git
   cd jira-tempo-report
   ```

2. Créez un environnement virtuel et activez-le :
   ```
   python -m venv venv
   source venv/bin/activate  # Sur Windows, utilisez `venv\Scripts\activate`
   ```

3. Installez les dépendances :
   ```
   pip install -r requirements.txt
   ```

4. Créez un fichier `.env` à la racine du projet et ajoutez vos identifiants :
   ```
   JIRA_USERNAME=votre_nom_utilisateur_jira
   JIRA_API_KEY=votre_clé_api_jira
   TEMPO_ACCESS_TOKEN=votre_token_accès_tempo
   DB_NAME=votre_nom_de_base_de_données
   DB_USER=votre_utilisateur_db
   DB_PASSWORD=votre_mot_de_passe_db
   DB_HOST=votre_hôte_db
   DB_PORT=votre_port_db
   ```

## Utilisation
1. Pour traiter les données et les stocker dans la base de données :
   ```
   python scripts/data_processor.py [--start YYYY-MM-DD] [--end YYYY-MM-DD]
   ```
   Si aucune date n'est spécifiée, le script traitera par défaut la semaine précédente.

2. Pour lancer l'application Streamlit :
   ```
   streamlit run app/main.py
   ```
   L'application sera accessible dans votre navigateur à l'adresse indiquée dans la console.

## Structure du projet
```
jira-tempo-report/
├── .gitlab-ci.yml
├── Dockerfile
├── Dockerfile.prod
├── README.md
├── app
│   ├── .DS_Store
│   ├── main.py
│   └── pages
├── certs
│   └── ca-certificate.crt
├── config
│   ├── .env.development
│   ├── .env.exemple
│   ├── .env.production
│   └── .env.test
├── docker-compose.yml
├── migrations
│   ├── 001_add_availability_table.sql
│   └── 002_add_target_table.sql
├── reports
│   ├── .DS_Store
│   ├── __init__.py
│   ├── __pycache__
│   ├── combined_reports.py
│   ├── jira_reports.py
│   ├── reports.py
│   └── tempo_reports.py
├── requirements.txt
├── scripts
│   ├── __pycache__
│   ├── clear_database.py
│   ├── data_processor.py
│   ├── db_operations.py
│   ├── db_setup.py
│   ├── populate_weekly_reports.py
│   └── wait_for_db.py
├── tests
│   ├── __pycache__
│   ├── test_jira_reports.py
│   └── test_tempo_reports.py
└── utils

```

psql "sslmode=require host=tempo-jira-cluster-do-user-14565660-0.i.db.ondigitalocean.com port=25060 dbname=defaultdb user=doadmin password=AVNS_7R_s77uZf--fmO7JckS sslrootcert=./certs/ca-certificate.crt"


## Contribution
Les contributions à ce projet sont les bienvenues. Veuillez suivre ces étapes pour contribuer :
1. Forkez le projet
2. Créez votre branche de fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Poussez vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## Contact
Eric Ferole - [eferole@activis.ca](mailto:eferole@activis.ca)

Lien du projet : [https://github.com/votre-nom/jira-tempo-report](https://github.com/activishq/jira-tempo-reports)
