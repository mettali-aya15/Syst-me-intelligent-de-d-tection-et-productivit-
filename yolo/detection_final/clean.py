from pathlib import Path
import shutil

print("=" * 70)
print("CORRECTION DES NOMS DE FICHIERS LABELS")
print("=" * 70)

base_dir = Path(r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\yolo\detection_final")

# Traiter train et val
for split in ['train', 'val']:
    labels_dir = base_dir / split / 'labels'
    images_dir = base_dir / split / 'images'
    
    print(f"\n📂 Traitement: {split}")
    print(f"   Labels: {labels_dir}")
    print(f"   Images: {images_dir}")
    
    # Lister les images disponibles
    images = {img.stem: img for img in images_dir.glob("*.jpg")}
    print(f"   Images trouvées: {len(images)}")
    
    # Traiter chaque label
    renamed_count = 0
    deleted_count = 0
    
    for label_file in list(labels_dir.glob("*.txt")):
        # Extraire le nom sans le hash
        # Format: hash__source_frame_00000.txt → source_frame_00000
        filename = label_file.stem
        
        if '__' in filename:
            image_name = filename.split('__', 1)[1]
        else:
            image_name = filename
        
        # Vérifier si l'image correspondante existe
        if image_name in images:
            # Renommer le label pour correspondre à l'image
            new_label_name = image_name + '.txt'
            new_label_path = labels_dir / new_label_name
            
            # Éviter d'écraser un fichier existant
            if new_label_path.exists() and new_label_path != label_file:
                print(f"   ⚠️  Doublon: {new_label_name}")
                label_file.unlink()
                deleted_count += 1
            else:
                label_file.rename(new_label_path)
                renamed_count += 1
        else:
            # Pas d'image correspondante, supprimer le label
            print(f"   🗑️  Supprimé (pas d'image): {label_file.name}")
            label_file.unlink()
            deleted_count += 1
    
    print(f"   ✅ Renommés: {renamed_count}")
    print(f"   🗑️  Supprimés: {deleted_count}")
    
    # Vérifier la correspondance finale
    final_labels = set(l.stem for l in labels_dir.glob("*.txt"))
    final_images = set(i.stem for i in images_dir.glob("*.jpg"))
    
    matching = final_labels & final_images
    labels_only = final_labels - final_images
    images_only = final_images - final_labels
    
    print(f"\n   📊 Vérification finale:")
    print(f"      Paires correctes: {len(matching)}")
    print(f"      Labels sans image: {len(labels_only)}")
    print(f"      Images sans label: {len(images_only)}")
    
    if images_only:
        print(f"\n   ⚠️  Images sans labels:")
        for img in sorted(images_only):
            print(f"      - {img}.jpg")

print(f"\n" + "=" * 70)
print("✅ CORRECTION TERMINÉE")
print("=" * 70)

print(f"\n🚀 Vous pouvez maintenant relancer l'entraînement:")
print(f"   yolo train model=yolov8n.pt data=data.yaml epochs=200 patience=0")