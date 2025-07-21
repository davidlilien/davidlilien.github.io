#!/usr/bin/env python3
"""
Script pour traiter les images ET mettre à jour le fichier CSV correspondant.
Ajoute un timestamp aux noms de fichiers pour forcer le rechargement du cache Glide.
"""

import os
import glob
import csv
import time
from PIL import Image, ImageOps, ImageStat
import numpy as np
import shutil

def replace_white_background(image, target_color=(255, 255, 221), tolerance=10):
    """
    Remplace les fonds blancs par la couleur cible FFFFDD.
    
    Args:
        image (PIL.Image): Image à traiter
        target_color (tuple): Couleur RGB de remplacement (FFFFDD par défaut)
        tolerance (int): Tolérance pour la détection du blanc
    
    Returns:
        PIL.Image: Image avec fond blanc remplacé
    """
    try:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convertir en array numpy pour un traitement efficace
        img_array = np.array(image)
        
        # Créer un masque pour les pixels blancs ou quasi-blancs
        white_mask = (
            (img_array[:, :, 0] >= 255 - tolerance) &  # Rouge proche de 255
            (img_array[:, :, 1] >= 255 - tolerance) &  # Vert proche de 255
            (img_array[:, :, 2] >= 255 - tolerance)    # Bleu proche de 255
        )
        
        # Remplacer les pixels blancs par la couleur cible
        img_array[white_mask] = target_color
        
        # Reconvertir en image PIL
        return Image.fromarray(img_array)
        
    except Exception as e:
        print(f"Erreur lors du remplacement du fond blanc: {e}")
        return image

def add_cache_buster_pixels(image):
    """
    Ajoute quelques pixels quasi-invisibles pour forcer Glide à invalider son cache.
    """
    try:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convertir en array numpy
        img_array = np.array(image)
        width, height = image.size
        
        # Ajouter quelques pixels très subtils dans les coins
        # Ces variations sont quasi-invisibles mais changent le hash de l'image
        
        # Coin supérieur gauche - variation de 1 sur le rouge
        if img_array[0, 0, 0] < 255:
            img_array[0, 0, 0] += 1
        else:
            img_array[0, 0, 0] -= 1
            
        # Coin supérieur droit - variation de 1 sur le vert  
        if img_array[0, width-1, 1] < 255:
            img_array[0, width-1, 1] += 1
        else:
            img_array[0, width-1, 1] -= 1
            
        # Coin inférieur gauche - variation de 1 sur le bleu
        if img_array[height-1, 0, 2] < 255:
            img_array[height-1, 0, 2] += 1
        else:
            img_array[height-1, 0, 2] -= 1
            
        # Coin inférieur droit - variation de 1 sur le rouge
        if img_array[height-1, width-1, 0] < 255:
            img_array[height-1, width-1, 0] += 1
        else:
            img_array[height-1, width-1, 0] -= 1
        
        # Reconvertir en image PIL
        return Image.fromarray(img_array)
        
    except Exception as e:
        print(f"Erreur lors de l'ajout du cache buster: {e}")
        return image

def add_border_pattern(image, border_width=2, pattern_color=(220, 220, 190)):
    """
    Ajoute une bordure subtile avec motif pour éviter la suppression par Glide.
    """
    try:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        width, height = image.size
        
        # Convertir en array numpy
        img_array = np.array(image)
        
        # Ajouter une bordure subtile sur les bords
        # Bordure supérieure et inférieure
        img_array[:border_width, :] = pattern_color
        img_array[-border_width:, :] = pattern_color
        
        # Bordure gauche et droite
        img_array[:, :border_width] = pattern_color
        img_array[:, -border_width:] = pattern_color
        
        # Reconvertir en image PIL
        return Image.fromarray(img_array)
        
    except Exception as e:
        print(f"Erreur lors de l'ajout de la bordure: {e}")
        return image

def make_image_square(image_path, output_path, background_color=(255, 255, 221), padding=20, final_size=256, add_border=True, add_cache_buster=True):
    """
    Rend une image carrée en ajoutant du padding sans déformation, puis la redimensionne.
    """
    try:
        # Ouvrir l'image
        with Image.open(image_path) as img:
            # Convertir en RGB si nécessaire (pour gérer les images avec transparence)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Créer un fond FFFFDD et coller l'image dessus
                background = Image.new('RGB', img.size, background_color)
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Remplacer les fonds blancs existants par FFFFDD
            img = replace_white_background(img, background_color)
            
            # Ajouter du padding autour de l'image
            width, height = img.size
            
            # Créer une nouvelle image avec padding FFFFDD
            padded_width = width + (2 * padding)
            padded_height = height + (2 * padding)
            padded_img = Image.new('RGB', (padded_width, padded_height), background_color)
            
            # Coller l'image originale au centre de l'image avec padding
            paste_x = padding
            paste_y = padding
            padded_img.paste(img, (paste_x, paste_y))
            
            # Utiliser l'image avec padding pour la suite
            img = padded_img
            width, height = padded_width, padded_height
            
            # Calculer la taille du carré (la plus grande dimension)
            max_size = max(width, height)
            
            # Si l'image est déjà carrée, pas besoin de modification pour la forme
            if width == height:
                square_img = img
            else:
                # Créer une nouvelle image carrée avec le fond FFFFDD
                square_img = Image.new('RGB', (max_size, max_size), background_color)
                
                # Calculer la position pour centrer l'image originale
                paste_x = (max_size - width) // 2
                paste_y = (max_size - height) // 2
                
                # Coller l'image originale au centre
                square_img.paste(img, (paste_x, paste_y))
            
            # Redimensionner l'image carrée à la taille finale souhaitée
            if square_img.size != (final_size, final_size):
                square_img = square_img.resize((final_size, final_size), Image.Resampling.LANCZOS)
            
            # Ajouter une bordure anti-suppression pour Glide si demandé
            if add_border:
                square_img = add_border_pattern(square_img)
            
            # Ajouter des pixels cache-buster pour forcer le rechargement
            if add_cache_buster:
                square_img = add_cache_buster_pixels(square_img)
            
            # Sauvegarder
            square_img.save(output_path, 'JPEG', quality=95)
            
            return True
            
    except Exception as e:
        print(f"✗ Erreur avec {os.path.basename(image_path)}: {e}")
        return False

def generate_new_filename(original_filename):
    """
    Génère un nouveau nom de fichier avec timestamp pour éviter le cache.
    
    Args:
        original_filename (str): Nom de fichier original
    
    Returns:
        str: Nouveau nom avec timestamp
    """
    # Extraire le nom et l'extension
    name, ext = os.path.splitext(original_filename)
    
    # Ajouter un timestamp
    timestamp = int(time.time())
    
    # Nouveau nom: image-001-000_1642345678.jpg
    new_filename = f"{name}_{timestamp}{ext}"
    
    return new_filename

def update_csv_file(csv_path, filename_mapping):
    """
    Met à jour le fichier CSV avec les nouveaux noms de fichiers.
    
    Args:
        csv_path (str): Chemin vers le fichier CSV
        filename_mapping (dict): Mapping ancien_nom -> nouveau_nom
    """
    try:
        # Lire le fichier CSV
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
        
        # Identifier la colonne contenant les URLs (probablement "BrickLink URL")
        header = rows[0] if rows else []
        url_column_index = None
        
        for i, column_name in enumerate(header):
            if 'url' in column_name.lower() or 'bricklink' in column_name.lower():
                url_column_index = i
                break
        
        if url_column_index is None:
            print("⚠ Impossible de trouver la colonne URL dans le CSV")
            return False
        
        print(f"✓ Colonne URL trouvée: {header[url_column_index]} (index {url_column_index})")
        
        # Mettre à jour les URLs
        updates_count = 0
        for row in rows[1:]:  # Skip header
            if len(row) > url_column_index:
                old_url = row[url_column_index]
                
                # Extraire le nom de fichier de l'URL
                if 'images_giant_booster/' in old_url:
                    old_filename = old_url.split('images_giant_booster/')[-1]
                    
                    if old_filename in filename_mapping:
                        new_filename = filename_mapping[old_filename]
                        new_url = old_url.replace(old_filename, new_filename)
                        row[url_column_index] = new_url
                        updates_count += 1
                        print(f"  📝 {old_filename} → {new_filename}")
        
        # Sauvegarder le CSV mis à jour
        backup_path = csv_path.replace('.csv', '_backup.csv')
        shutil.copy2(csv_path, backup_path)
        print(f"✓ Sauvegarde du CSV original: {os.path.basename(backup_path)}")
        
        with open(csv_path, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
        
        print(f"✓ CSV mis à jour: {updates_count} URLs modifiées")
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors de la mise à jour du CSV: {e}")
        return False

def main():
    """Fonction principale du script."""
    print("=" * 70)
    print("SCRIPT DE TRAITEMENT D'IMAGES ET MISE À JOUR CSV")
    print("=" * 70)
    print("Ce script va:")
    print("1. Traiter toutes les images (carrées 256x256, fond FFFFDD)")
    print("2. Les renommer avec un timestamp pour éviter le cache Glide")
    print("3. Mettre à jour les URLs dans le fichier CSV correspondant")
    print()
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Vérifier la présence du CSV
    csv_path = os.path.join(current_dir, 'lego_parts2.csv')
    if not os.path.exists(csv_path):
        print(f"✗ Fichier CSV non trouvé: {csv_path}")
        return
    
    print(f"✓ Fichier CSV trouvé: {os.path.basename(csv_path)}")
    
    # Paramètres
    response = input("Taille du padding en pixels (défaut: 20): ").strip()
    padding = int(response) if response else 20
    
    response = input("Ajouter bordure anti-Glide? (O/n): ").strip().lower()
    add_border = response not in ['n', 'non', 'no']
    
    response = input("Ajouter cache-buster? (O/n): ").strip().lower()
    add_cache_buster = response not in ['n', 'non', 'no']
    
    print(f"\n✓ Padding: {padding}px")
    print(f"✓ Bordure anti-Glide: {'Activée' if add_border else 'Désactivée'}")
    print(f"✓ Cache-buster: {'Activé' if add_cache_buster else 'Désactivé'}")
    
    response = input("\nContinuer le traitement? (O/n): ").strip().lower()
    if response in ['n', 'non', 'no']:
        print("Traitement annulé.")
        return
    
    print("\n" + "-" * 70)
    
    # Obtenir la liste des fichiers image
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.webp']
    image_files = []
    for extension in image_extensions:
        pattern = os.path.join(current_dir, extension)
        image_files.extend(glob.glob(pattern, recursive=False))
        # Aussi chercher en majuscules
        pattern_upper = os.path.join(current_dir, extension.upper())
        image_files.extend(glob.glob(pattern_upper, recursive=False))
    
    # Supprimer les doublons et trier
    image_files = list(set(image_files))
    image_files.sort()
    
    if not image_files:
        print("✗ Aucune image trouvée dans le dossier.")
        return
    
    print(f"✓ Trouvé {len(image_files)} image(s) à traiter")
    
    # Mapping des noms de fichiers
    filename_mapping = {}
    
    # Traiter chaque image
    success_count = 0
    for image_file in image_files:
        old_filename = os.path.basename(image_file)
        new_filename = generate_new_filename(old_filename)
        new_filepath = os.path.join(current_dir, new_filename)
        
        print(f"\n📷 Traitement: {old_filename}")
        
        # Traiter l'image
        if make_image_square(image_file, new_filepath, padding=padding, add_border=add_border, add_cache_buster=add_cache_buster):
            # Supprimer l'ancien fichier
            os.remove(image_file)
            
            # Ajouter au mapping
            filename_mapping[old_filename] = new_filename
            
            print(f"✓ Renommé: {old_filename} → {new_filename}")
            success_count += 1
        else:
            print(f"✗ Échec du traitement: {old_filename}")
    
    print("\n" + "-" * 70)
    print(f"✓ Images traitées: {success_count}/{len(image_files)}")
    
    if filename_mapping:
        print(f"📝 Mise à jour du CSV...")
        update_csv_file(csv_path, filename_mapping)
    
    print("\n" + "=" * 70)
    print("🎉 TRAITEMENT TERMINÉ!")
    print("✓ Images transformées et renommées")
    print("✓ CSV mis à jour avec les nouveaux noms")
    print("✓ Cache Glide forcé à se recharger")
    print("=" * 70)

if __name__ == "__main__":
    main()
