#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour scraper les données d'objet magique D&D depuis aidedd.org
Extrait les données de la table avec l'id "liste", puis sauvegarde le tout en CSV
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import sys
from urllib.parse import urljoin

def filter_empty_columns(items_data):
    """
    Filtre les colonnes sans en-tête (vides) du dataset
    
    Args:
        items_data (list): Données des objets avec en-tête
        
    Returns:
        list: Données filtrées sans colonnes vides
    """
    if not items_data or len(items_data) < 1:
        return items_data

    header_row = items_data[0]

    # Identifier les indices des colonnes avec un en-tête non vide
    valid_columns = []
    for i, header in enumerate(header_row):
        if header and header.strip():  # En-tête non vide
            valid_columns.append(i)
    
    # Filtrer toutes les lignes pour ne garder que les colonnes valides
    filtered_data = []
    for row in items_data:
        filtered_row = [row[i] if i < len(row) else '' for i in valid_columns]
        filtered_data.append(filtered_row)
    
    print(f"🔧 Filtrage des colonnes: {len(header_row)} → {len(valid_columns)} colonnes conservées")
    
    return filtered_data

def extract_item_link(cell):
    """
    Extrait le lien d'un objet depuis une cellule de la table

    Args:
        cell: Cellule BeautifulSoup contenant potentiellement un lien
        
    Returns:
        str or None: URL relative de l'objet ou None si pas de lien
    """
    # Recherche d'un lien dans la cellule avec la classe "item"
    if cell.get('class') and 'item' in cell.get('class'):
        link = cell.find('a')
        if link and link.get('href'):
            return link.get('href')
    
    return None

def get_items_data(url):
    """
    Récupère les données des objets

    Args:
        url (str): URL de la page à scraper
        
    Returns:
        list: Liste des données des objets
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
        items_data = []
        item_links = []

        # Recherche des lignes de données
        rows = table.find_all('tr')
        print(f"Nombre de lignes trouvées: {len(rows)}")
        
        # Déterminer l'en-tête
        header_row = None
        data_rows = []
        item_links_data = []  # Pour stocker les liens avec les données
        
        for i, row in enumerate(rows):
            cells = row.find_all(['th', 'td'])
            if not cells:
                continue
                
            # Si c'est la première ligne avec des données ou contient des th, c'est probablement l'en-tête
            if header_row is None and (cells[0].name == 'th' or i == 0):
                header_row = [cell.get_text(strip=True) for cell in cells]
                # Ajout de la colonne lien à la fin
                header_row.append('Lien_Description')
                print(f"En-tête détecté: {header_row}")
            else:
                # Extraction des données de la ligne
                row_data = []
                item_link = None
                
                for j, cell in enumerate(cells):
                    # Récupération du texte
                    text = cell.get_text(strip=True)
                    row_data.append(text)

                    # Vérification si cette cellule contient le lien de l'objet (cellule avec classe "item")
                    if not item_link:
                        link = extract_item_link(cell)
                        if link:
                            item_link = link

                if any(row_data):  # Si la ligne contient des données
                    data_rows.append(row_data)
                    item_links_data.append(item_link)  # Associer le lien aux données

        # Si pas d'en-tête détecté, créer un en-tête générique
        if header_row is None and data_rows:
            header_row = [f"Colonne_{i+1}" for i in range(len(data_rows[0]))]
            header_row.append('Lien_Description')
            print(f"En-tête générique créé: {header_row}")
        
        # Ajout de l'en-tête aux données
        if header_row:
            items_data.append(header_row)
        
        print("⚠️  Cela peut prendre quelques minutes...")

        # Extraction du lien pour chaque objet
        base_url_for_items = "https://www.aidedd.org/magic-item/"

        for i, (row_data, item_link) in enumerate(zip(data_rows, item_links_data)):
            print(f"📜 Traitement de l'objet {i+1}/{len(data_rows)}: {row_data[1] if len(row_data) > 1 else 'N/A'}")
            
            # Ajout du lien de description complet à la fin
            if item_link:
                full_item_url = urljoin(base_url_for_items, item_link)
                row_data.append(full_item_url)
            else:
                row_data.append('')  # Lien vide si pas de lien trouvé
            
            items_data.append(row_data)

        print(f"\n✅ {len(data_rows)} objets extraits (+ en-tête)")

        # Filtrer les colonnes vides avant de retourner les données
        items_data = filter_empty_columns(items_data)

        return items_data

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
            writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
            
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
    print("=== SCRAPER AIDEDD.ORG - OBJETS D&D ===\n")
    
    # URL de base
    url = "https://www.aidedd.org/magic-item/fr/"

    # Nom du fichier de sortie
    output_file = "objets_dnd_aidedd.csv"

    # Extraction des données
    print("🔍 Extraction des données...")
    items_data = get_items_data(url)

    if not items_data:
        print("❌ Échec de l'extraction des données")
        return False
    
    # Sauvegarde
    print("\n💾 Sauvegarde des données...")
    success = save_to_csv(items_data, output_file)
    
    if success:
        print(f"\n🎉 Scraping terminé avec succès!")
        print(f"📁 Fichier créé: {output_file}")
        
        # Affichage d'un aperçu
        if items_data and len(items_data) > 1:
            print(f"\n📋 Aperçu des données (3 premières lignes):")
            for i, row in enumerate(items_data[:3]):
                if i == 0:
                    print(f"  En-tête: {row[:5]}... [+{len(row)-5} colonnes]")
                else:
                    print(f"  {i}. {row[1] if len(row) > 1 else 'N/A'}")
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