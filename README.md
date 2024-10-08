# Jira-Tempo Activity Report Generator

## Description
Ce projet est une application Streamlit qui génère des rapports d'activité basés sur les données de Jira et Tempo. Il permet de visualiser et d'analyser le temps passé sur les projets, les temps facturables et non facturables, ainsi que d'autres métriques importantes pour la gestion de projet et la facturation.

## Fonctionnalités
- Génération de rapports d'activité pour le département et les utilisateurs individuels
- Calcul et affichage des métriques clés (temps total enregistré, temps facturable, ratio de facturation, etc.)
- Visualisation des données sous forme de graphiques et de tableaux
- Filtrage des données par période et par utilisateur

## Prérequis
- Python 3.10
- Compte Jira avec accès API
- Compte Tempo avec accès API

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
   ```

## Utilisation
Pour lancer l'application Streamlit, exécutez :
```
streamlit run app/main.py
```

L'application sera accessible dans votre navigateur à l'adresse indiquée dans la console.

## Structure du projet
```
jira-tempo-report/
│
├── app/
│   ├── main.py
│   └── pages/
│       └── ...
│
├── reports/
│   ├── jira_reports.py
│   ├── tempo_reports.py
│   └── combined_reports.py
│
├── tests/
│   └── ...
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

## Contribution
Les contributions à ce projet sont les bienvenues. Veuillez suivre ces étapes pour contribuer :
1. Forkez le projet
2. Créez votre branche de fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Poussez vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## Licence
Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## Contact
Eric Ferole - [eferole@activis.cacom](mailto:eferole@activis.ca)

Lien du projet : [https://github.com/votre-nom/jira-tempo-report](https://github.com/votre-nom/jira-tempo-report)
