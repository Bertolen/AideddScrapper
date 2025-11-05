#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour scraper les données de sorts D&D depuis aidedd.org
Extrait les données de la table avec l'id "liste" et les informations de classe
pour chaque sort, puis sauvegarde le tout en CSV
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import sys
from urllib.parse import urljoin
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_spell_classes(spell_url, headers, base_url):
    """
    Récupère les classes disponibles pour un sort spécifique
    
    Args:
        spell_url (str): URL relative du sort
        headers (dict): Headers HTTP
        base_url (str): URL de base du site
        
    Returns:
        dict: Dictionnaire avec les classes disponibles (True/False)
    """
    classes = {
        'Barbare': False,
        'Barde': False,
        'Clerc': False,
        'Druide': False,
        'Ensorceleur': False,
        'Guerrier': False,
        'Magicien': False,
        'Moine': False,
        'Occultiste': False,
        'Paladin': False,
        'Rôdeur': False,
        'Roublard': False
    }
    
    try:
        # Construction de l'URL complète
        full_url = urljoin(base_url, spell_url)
        
        # Requête avec timeout plus court pour ne pas ralentir
        response = requests.get(full_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Recherche dans tout le contenu de la page
        page_text = soup.get_text()
        
        # Recherche des lignes contenant des informations utiles
        lines = [line.strip() for line in page_text.split('\n') if line.strip()]
        
        # Recherche des classes dans les premières lignes (où se trouvent les infos du sort)
        for line in lines[:10]:  # Généralement dans les 10 premières lignes
            for class_name in classes.keys():
                if class_name in line:
                    classes[class_name] = True
        
        # Petit délai pour être respectueux du serveur
        time.sleep(0.3)
        
    except Exception as e:
        print(f"⚠️  Erreur lors de la récupération des classes pour {spell_url}: {e}")
        # En cas d'erreur, on retourne le dictionnaire avec des False
    
    return classes

def filter_empty_columns(spells_data):
    """
    Filtre les colonnes sans en-tête (vides) du dataset
    
    Args:
        spells_data (list): Données des sorts avec en-tête
        
    Returns:
        list: Données filtrées sans colonnes vides
    """
    if not spells_data or len(spells_data) < 1:
        return spells_data
    
    header_row = spells_data[0]
    
    # Identifier les indices des colonnes avec un en-tête non vide
    valid_columns = []
    for i, header in enumerate(header_row):
        if header and header.strip():  # En-tête non vide
            valid_columns.append(i)
    
    # Filtrer toutes les lignes pour ne garder que les colonnes valides
    filtered_data = []
    for row in spells_data:
        filtered_row = [row[i] if i < len(row) else '' for i in valid_columns]
        filtered_data.append(filtered_row)
    
    print(f"🔧 Filtrage des colonnes: {len(header_row)} → {len(valid_columns)} colonnes conservées")
    
    return filtered_data

def extract_spell_link(cell):
    """
    Extrait le lien d'un sort depuis une cellule de la table
    
    Args:
        cell: Cellule BeautifulSoup contenant potentiellement un lien
        
    Returns:
        str or None: URL relative du sort ou None si pas de lien
    """
    # Recherche d'un lien dans la cellule avec la classe "item"
    if cell.get('class') and 'item' in cell.get('class'):
        link = cell.find('a')
        if link and link.get('href'):
            return link.get('href')
    
    return None
    """
    Extrait le lien d'un sort depuis une cellule de la table
    
    Args:
        cell: Cellule BeautifulSoup contenant potentiellement un lien
        
    Returns:
        str or None: URL relative du sort ou None si pas de lien
    """
    # Recherche d'un lien dans la cellule avec la classe "item"
    if cell.get('class') and 'item' in cell.get('class'):
        link = cell.find('a')
        if link and link.get('href'):
            return link.get('href')
    
    return None

def get_spells_data_with_classes(url):
    """
    Récupère les données des sorts avec les informations de classe
    
    Args:
        url (str): URL de la page à scraper
        
    Returns:
        list: Liste des données des sorts avec colonnes de classe
    """
    print(f"Connexion à {url}...")
    
    # Headers pour éviter d'être bloqué
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Envoi de la requête
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        print("Page récupérée avec succès!")
        print(f"Taille de la réponse: {len(response.content)} bytes")
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Recherche de la table avec l'id "liste"
        table = soup.find('table', {'id': 'liste'})
        
        if not table:
            print("❌ Erreur: Table avec id 'liste' non trouvée!")
            return []
        
        print("✅ Table 'liste' trouvée!")
        
        # Extraction des données
        spells_data = []
        spell_links = []
        
        # Recherche des lignes de données
        rows = table.find_all('tr')
        print(f"Nombre de lignes trouvées: {len(rows)}")
        
        # Classes disponibles
        class_names = ['Barde', 'Clerc', 'Druide', 'Paladin', 'Rôdeur', 'Ensorceleur', 'Occultiste', 'Magicien']
        
        # Déterminer l'en-tête
        header_row = None
        data_rows = []
        spell_links_data = []  # Pour stocker les liens avec les données
        
        for i, row in enumerate(rows):
            cells = row.find_all(['th', 'td'])
            if not cells:
                continue
                
            # Si c'est la première ligne avec des données ou contient des th, c'est probablement l'en-tête
            if header_row is None and (cells[0].name == 'th' or i == 0):
                header_row = [cell.get_text(strip=True) for cell in cells]
                # Ajout des colonnes de classe à l'en-tête
                header_row.extend(class_names)
                # Ajout de la colonne lien à la fin
                header_row.append('Lien_Description')
                print(f"En-tête détecté: {header_row}")
            else:
                # Extraction des données de la ligne
                row_data = []
                spell_link = None
                
                for j, cell in enumerate(cells):
                    # Récupération du texte
                    text = cell.get_text(strip=True)
                    row_data.append(text)
                    
                    # Vérification si cette cellule contient le lien du sort (cellule avec classe "item")
                    if not spell_link:
                        link = extract_spell_link(cell)
                        if link:
                            spell_link = link
                
                if any(row_data):  # Si la ligne contient des données
                    data_rows.append(row_data)
                    spell_links_data.append(spell_link)  # Associer le lien aux données
        
        # Si pas d'en-tête détecté, créer un en-tête générique
        if header_row is None and data_rows:
            header_row = [f"Colonne_{i+1}" for i in range(len(data_rows[0]))]
            header_row.extend(class_names)
            header_row.append('Lien_Description')
            print(f"En-tête générique créé: {header_row}")
        
        # Ajout de l'en-tête aux données
        if header_row:
            spells_data.append(header_row)
        
        print(f"\n🔗 Extraction des informations de classe pour {len(data_rows)} sorts...")
        print("⚠️  Cela peut prendre quelques minutes...")
        
        # Extraction des informations de classe pour chaque sort
        base_url_for_spells = "https://www.aidedd.org/spell/"
        
        for i, (row_data, spell_link) in enumerate(zip(data_rows, spell_links_data)):
            print(f"📜 Traitement du sort {i+1}/{len(data_rows)}: {row_data[1] if len(row_data) > 1 else 'N/A'}")
            
            # Initialisation des colonnes de classe
            class_availability = {class_name: False for class_name in class_names}
            
            if spell_link:
                # Récupération des informations de classe
                class_availability = get_spell_classes(spell_link, headers, base_url_for_spells)
            
            # Ajout des informations de classe aux données de la ligne
            for class_name in class_names:
                row_data.append('Oui' if class_availability[class_name] else 'Non')
            
            # Ajout du lien de description complet à la fin
            if spell_link:
                full_spell_url = urljoin(base_url_for_spells, spell_link)
                row_data.append(full_spell_url)
            else:
                row_data.append('')  # Lien vide si pas de lien trouvé
            
            spells_data.append(row_data)
        
        print(f"\n✅ {len(data_rows)} sorts extraits avec informations de classe (+ en-tête)")
        
        # Filtrer les colonnes vides avant de retourner les données
        spells_data = filter_empty_columns(spells_data)
        
        return spells_data
        
    except requests.RequestException as e:
        print(f"❌ Erreur lors de la requête: {e}")
        return []
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return []

def save_to_csv(data, filename):
    """
    Sauvegarde les données dans un fichier CSV
    
    Args:
        data (list): Données à sauvegarder
        filename (str): Nom du fichier CSV
    """
    if not data:
        print("❌ Aucune donnée à sauvegarder!")
        return False
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            for row in data:
                writer.writerow(row)
        
        print(f"✅ Données sauvegardées dans '{filename}'")
        print(f"   {len(data)} lignes écrites")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return False

def main():
    """Fonction principale"""
    print("=== SCRAPER AIDEDD.ORG - SORTS D&D AVEC CLASSES ===\n")
    
    # URL de base
    url = "https://www.aidedd.org/spell/fr/"
    
    # Nom du fichier de sortie
    output_file = "sorts_dnd_aidedd_avec_classes.csv"
    
    # Extraction des données
    print("🔍 Extraction des données avec informations de classe...")
    spells_data = get_spells_data_with_classes(url)
    
    if not spells_data:
        print("❌ Échec de l'extraction des données")
        return False
    
    # Sauvegarde
    print("\n💾 Sauvegarde des données...")
    success = save_to_csv(spells_data, output_file)
    
    if success:
        print(f"\n🎉 Scraping terminé avec succès!")
        print(f"📁 Fichier créé: {output_file}")
        
        # Affichage d'un aperçu
        if len(spells_data) > 1:
            print(f"\n📋 Aperçu des données (3 premières lignes):")
            for i, row in enumerate(spells_data[:3]):
                if i == 0:
                    print(f"  En-tête: {row[:5]}... [+{len(row)-5} colonnes]")
                else:
                    print(f"  {i}. {row[1] if len(row) > 1 else 'N/A'} - Classes: {row[-8:] if len(row) >= 8 else 'N/A'}")
    else:
        print("\n❌ Échec du scraping")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Arrêt du script par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        sys.exit(1)