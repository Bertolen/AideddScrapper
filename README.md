# Scraper AideDD - Sorts D&D

Ce script Python permet d'extraire automatiquement les données des sorts de Dungeons & Dragons depuis le site [aidedd.org](https://www.aidedd.org/spell/fr/) et de les sauvegarder dans un fichier CSV.

## Fonctionnalités

- 🔍 Extraction automatique des données de la table des sorts
- 📊 Export en format CSV avec délimiteur `;`
- 🛡️ Gestion des erreurs et timeout
- 📝 Headers HTTP pour éviter les blocages
- 🎯 Ciblage précis de la table avec l'id "liste"

## Installation

1. Assurez-vous d'avoir Python 3.6+ installé
2. Installez les dépendances :

```bash
pip install -r requirements.txt
```

## Utilisation

Exécutez simplement le script :

```bash
python scraper_aidedd.py
```

Le script va :
1. Se connecter au site aidedd.org
2. Extraire les données de la table des sorts
3. Créer un fichier `sorts_dnd_aidedd.csv` avec toutes les données

## Structure des données extraites

Le fichier CSV contiendra toutes les colonnes présentes dans la table du site, typiquement :
- Nom du sort
- Langue (EN/ES)
- Niveau
- École de magie
- Temps d'incantation
- Portée
- Durée
- Composantes
- Concentration
- Rituel

## Fichier de sortie

- **Nom** : `sorts_dnd_aidedd.csv`
- **Encodage** : UTF-8
- **Délimiteur** : `;` (point-virgule)
- **Format** : CSV standard avec en-têtes

## Gestion des erreurs

Le script gère automatiquement :
- Erreurs de connexion réseau
- Timeouts
- Pages non trouvées
- Problèmes d'encodage
- Structures HTML inattendues

## Remarques

- Le script respecte une utilisation raisonnable du site (pas de requêtes excessives)
- Les données sont extraites telles qu'affichées sur le site
- Le script s'adapte automatiquement aux changements mineurs de structure

## Licence

Ce script est fourni à des fins éducatives et de référence. Respectez les conditions d'utilisation du site aidedd.org.