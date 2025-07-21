#!/usr/bin/env python3
"""
Script pour rendre toutes les images du dossier courrant carrées sans les déformer.
Ajoute du padding blanc autour de chaque image, puis ajoute de l'espace supplémentaire
en haut/bas ou gauche/droite selon les besoins pour créer un carré parfait.
Les images restent centrées et sont redimensionnées à 256x256 pixels.
"""

import os
import glob
from PIL import Image, ImageOps, ImageStat

def make_image_square(image_path, output_path=None, background_color=(255, 255, 255), padding=20, final_size=256):
    """
    Rend une image carrée en ajoutant du padding sans déformation, puis la redimensionne.
    
    Args:
        image_path (str): Chemin vers l'image source
        output_path (str): Chemin de sortie (optionnel, écrase l'original si None)
        background_color (tuple): Couleur de fond RGB pour le padding (blanc par défaut)
        padding (int): Nombre de pixels de padding à ajouter autour de l'image
        final_size (int): Taille finale en pixels (carré final_size x final_size)
    
    Returns:
        bool: True si succès, False sinon
    """
    try:
        # Ouvrir l'image
        with Image.open(image_path) as img:
            # Convertir en RGB si nécessaire (pour gérer les images avec transparence)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Créer un fond blanc et coller l'image dessus
                background = Image.new('RGB', img.size, background_color)
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Ajouter du padding autour de l'image
            width, height = img.size
            
            # Créer une nouvelle image avec padding
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
            
            # Obtenir les dimensions actuelles (après padding)
            # width, height = img.size
            
            # Calculer la taille du carré (la plus grande dimension)
            max_size = max(width, height)
            
            # Si l'image est déjà carrée, pas besoin de modification pour la forme
            if width == height:
                square_img = img
            else:
                # Créer une nouvelle image carrée avec le fond blanc
                square_img = Image.new('RGB', (max_size, max_size), background_color)
                
                # Calculer la position pour centrer l'image originale
                paste_x = (max_size - width) // 2
                paste_y = (max_size - height) // 2
                
                # Coller l'image originale au centre
                square_img.paste(img, (paste_x, paste_y))
            
            # Redimensionner l'image carrée à la taille finale souhaitée
            if square_img.size != (final_size, final_size):
                square_img = square_img.resize((final_size, final_size), Image.Resampling.LANCZOS)
            
            # Sauvegarder
            output_file = output_path if output_path else image_path
            square_img.save(output_file, 'JPEG', quality=95)
            
            original_size = f"{width - 2*padding}x{height - 2*padding}"
            print(f"✓ Traité: {os.path.basename(image_path)} ({original_size} → {final_size}x{final_size}, padding: {padding}px)")
            return True
            
    except Exception as e:
        print(f"✗ Erreur avec {os.path.basename(image_path)}: {e}")
        return False

def process_folder(folder_path=".", image_extensions=None, create_backup=False, padding=20, final_size=256):
    """
    Traite toutes les images d'un dossier.
    
    Args:
        folder_path (str): Chemin du dossier à traiter
        image_extensions (list): Extensions d'images à traiter
        create_backup (bool): Créer une sauvegarde avant modification
        padding (int): Nombre de pixels de padding à ajouter autour de chaque image
        final_size (int): Taille finale en pixels (carré final_size x final_size)
    """
    if image_extensions is None:
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.webp']
    
    # Obtenir la liste des fichiers image
    image_files = []
    for extension in image_extensions:
        pattern = os.path.join(folder_path, extension)
        image_files.extend(glob.glob(pattern, recursive=False))
        # Aussi chercher en majuscules
        pattern_upper = os.path.join(folder_path, extension.upper())
        image_files.extend(glob.glob(pattern_upper, recursive=False))
    
    # Supprimer les doublons
    image_files = list(set(image_files))
    image_files.sort()
    
    if not image_files:
        print("Aucune image trouvée dans le dossier.")
        return
    
    print(f"Trouvé {len(image_files)} image(s) à traiter...")
    print("-" * 50)
    
    # Créer un dossier de sauvegarde si demandé
    if create_backup:
        backup_folder = os.path.join(folder_path, "backup_original")
        os.makedirs(backup_folder, exist_ok=True)
        print(f"Sauvegarde créée dans: {backup_folder}")
    
    # Traiter chaque image
    success_count = 0
    for image_file in image_files:
        # Créer une sauvegarde si demandé
        if create_backup:
            backup_path = os.path.join(backup_folder, os.path.basename(image_file))
            try:
                with Image.open(image_file) as img:
                    img.save(backup_path, quality=95)
            except Exception as e:
                print(f"⚠ Impossible de sauvegarder {os.path.basename(image_file)}: {e}")
        
        # Traiter l'image
        if make_image_square(image_file, padding=padding, final_size=final_size):
            success_count += 1
    
    print("-" * 50)
    print(f"Traitement terminé: {success_count}/{len(image_files)} images traitées avec succès.")
    
    if create_backup:
        print(f"Les images originales ont été sauvegardées dans '{backup_folder}'")

def main():
    """Fonction principale du script."""
    print("=" * 60)
    print("SCRIPT DE TRANSFORMATION D'IMAGES EN CARRÉ")
    print("=" * 60)
    print("Ce script va transformer toutes les images du dossier courant")
    print("en images carrées de 256x256 pixels avec du padding blanc sans déformation.")
    print("Un padding blanc sera ajouté autour de chaque image avant redimensionnement.")
    print()
    
    # Demander la taille du padding
    while True:
        try:
            padding_input = input("Taille du padding en pixels (défaut: 20): ").strip()
            if padding_input == "":
                padding = 20
                break
            padding = int(padding_input)
            if padding >= 0:
                break
            else:
                print("⚠ Le padding doit être un nombre positif ou zéro.")
        except ValueError:
            print("⚠ Veuillez entrer un nombre valide.")
    
    print(f"Padding sélectionné: {padding} pixels")
    print("Taille finale: 256x256 pixels")
    print()
    
    # Demander confirmation
    response = input("Voulez-vous créer une sauvegarde des originaux? (o/N): ").strip().lower()
    create_backup = response in ['o', 'oui', 'y', 'yes']
    
    print()
    response = input("Continuer le traitement? (O/n): ").strip().lower()
    if response in ['n', 'non', 'no']:
        print("Traitement annulé.")
        return
    
    print()
    
    # Traiter le dossier courant
    current_dir = os.path.dirname(os.path.abspath(__file__))
    process_folder(current_dir, create_backup=create_backup, padding=padding, final_size=256)

if __name__ == "__main__":
    main()
