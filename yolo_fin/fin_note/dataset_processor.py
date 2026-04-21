import os
import json
import shutil
from pathlib import Path
from collections import defaultdict
import cv2

class YOLODatasetProcessor:
    def __init__(self, images_dir, labels_dir, output_dir="cleaned_dataset"):
        self.images_dir = Path(images_dir)
        self.labels_dir = Path(labels_dir)
        self.output_dir = Path(output_dir)
        
        # Classes à retirer (médicales)
        self.medical_classes = ["Benign", "Malignant", "Normal"]
        
        # Classes valides pour CAMIA-Factory
        self.valid_classes = [
            "client",
            "employé",
            "employé actif",
            "employé inactif",
            "machine",
            "machine arrêtée",
            "produit",
            "tables",
            "tables_vides"
        ]
        
        # Mapping ancien index -> nouveau index
        self.class_mapping = {}
        self.setup_class_mapping()
        
        self.stats = defaultdict(int)
        self.issues = []
        
    def setup_class_mapping(self):
        """Créer le mapping des indices de classes"""
        # Anciennes classes (0-11)
        old_classes = self.medical_classes + self.valid_classes
        
        # Nouveau mapping (0-8 pour les classes valides)
        for new_idx, class_name in enumerate(self.valid_classes):
            old_idx = old_classes.index(class_name)
            self.class_mapping[old_idx] = new_idx
            
        print("=== Mapping des classes ===")
        for old_idx, new_idx in self.class_mapping.items():
            print(f"Classe {old_idx} ({old_classes[old_idx]}) -> Classe {new_idx}")
        print()
    
    def verify_consistency(self):
        """Vérifier que chaque image a son label correspondant"""
        print("=== Vérification de la cohérence ===")
        
        images = set([f.stem for f in self.images_dir.glob("*.jpg")])
        labels = set([f.stem for f in self.labels_dir.glob("*.txt")])
        
        missing_labels = images - labels
        missing_images = labels - images
        
        if missing_labels:
            print(f"⚠️  {len(missing_labels)} images sans label:")
            for name in sorted(missing_labels):
                print(f"  - {name}.jpg")
                self.issues.append(f"Image sans label: {name}.jpg")
        
        if missing_images:
            print(f"⚠️  {len(missing_images)} labels sans image:")
            for name in sorted(missing_images):
                print(f"  - {name}.txt")
                self.issues.append(f"Label sans image: {name}.txt")
        
        common = images & labels
        print(f"✓ {len(common)} paires image/label valides")
        print()
        
        return common
    
    def analyze_distribution(self, valid_pairs):
        """Analyser la distribution des classes"""
        print("=== Analyse de la distribution ===")
        
        class_counts = defaultdict(int)
        total_annotations = 0
        files_with_medical = []
        
        for filename in valid_pairs:
            label_file = self.labels_dir / f"{filename}.txt"
            
            with open(label_file, 'r') as f:
                lines = f.readlines()
                
            has_medical = False
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 5:
                    class_idx = int(parts[0])
                    
                    if class_idx < 3:  # Classes médicales
                        has_medical = True
                    elif class_idx in self.class_mapping:
                        class_counts[class_idx] += 1
                        total_annotations += 1
            
            if has_medical:
                files_with_medical.append(filename)
        
        print("Distribution des annotations par classe (avant nettoyage):")
        old_classes = self.medical_classes + self.valid_classes
        
        for class_idx in sorted(class_counts.keys()):
            count = class_counts[class_idx]
            percentage = (count / total_annotations * 100) if total_annotations > 0 else 0
            print(f"  Classe {class_idx} ({old_classes[class_idx]}): {count} annotations ({percentage:.1f}%)")
        
        print(f"\nTotal annotations: {total_annotations}")
        print(f"Fichiers contenant des classes médicales: {len(files_with_medical)}")
        print()
        
        return class_counts, files_with_medical
    
    def clean_labels(self, valid_pairs):
        """Nettoyer les labels en retirant les classes médicales et en réindexant"""
        print("=== Nettoyage des labels ===")
        
        cleaned_dir = self.output_dir / "labels"
        cleaned_dir.mkdir(parents=True, exist_ok=True)
        
        cleaned_count = 0
        removed_annotations = 0
        
        for filename in valid_pairs:
            label_file = self.labels_dir / f"{filename}.txt"
            output_file = cleaned_dir / f"{filename}.txt"
            
            with open(label_file, 'r') as f:
                lines = f.readlines()
            
            cleaned_lines = []
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 5:
                    old_class_idx = int(parts[0])
                    
                    # Ignorer les classes médicales
                    if old_class_idx < 3:
                        removed_annotations += 1
                        continue
                    
                    # Réindexer les classes valides
                    if old_class_idx in self.class_mapping:
                        new_class_idx = self.class_mapping[old_class_idx]
                        parts[0] = str(new_class_idx)
                        cleaned_lines.append(' '.join(parts) + '\n')
            
            # Écrire le fichier nettoyé
            if cleaned_lines:
                with open(output_file, 'w') as f:
                    f.writelines(cleaned_lines)
                cleaned_count += 1
        
        print(f"✓ {cleaned_count} fichiers labels nettoyés")
        print(f"✓ {removed_annotations} annotations médicales retirées")
        print()
        
        return cleaned_count
    
    def copy_images(self, valid_pairs):
        """Copier les images vers le répertoire de sortie"""
        print("=== Copie des images ===")
        
        images_output = self.output_dir / "images"
        images_output.mkdir(parents=True, exist_ok=True)
        
        copied_count = 0
        for filename in valid_pairs:
            src = self.images_dir / f"{filename}.jpg"
            dst = images_output / f"{filename}.jpg"
            shutil.copy2(src, dst)
            copied_count += 1
        
        print(f"✓ {copied_count} images copiées")
        print()
        
        return copied_count
    
    def convert_to_coco(self, valid_pairs):
        """Convertir le dataset au format COCO"""
        print("=== Conversion au format COCO ===")
        
        coco_data = {
            "info": {
                "year": 2026,
                "version": "1.0",
                "description": "CAMIA-Factory Dataset - Cleaned",
                "contributor": "Aya",
                "date_created": "2026-04-15"
            },
            "licenses": [],
            "categories": [],
            "images": [],
            "annotations": []
        }
        
        # Créer les catégories
        for idx, class_name in enumerate(self.valid_classes):
            coco_data["categories"].append({
                "id": idx,
                "name": class_name,
                "supercategory": "object"
            })
        
        annotation_id = 0
        
        for image_id, filename in enumerate(sorted(valid_pairs)):
            # Lire l'image pour obtenir les dimensions
            img_path = self.images_dir / f"{filename}.jpg"
            img = cv2.imread(str(img_path))
            
            if img is None:
                print(f"⚠️  Impossible de lire l'image: {filename}.jpg")
                continue
            
            height, width = img.shape[:2]
            
            # Ajouter l'info de l'image
            coco_data["images"].append({
                "id": image_id,
                "file_name": f"{filename}.jpg",
                "width": width,
                "height": height
            })
            
            # Lire le label nettoyé
            label_file = self.output_dir / "labels" / f"{filename}.txt"
            
            if not label_file.exists():
                continue
            
            with open(label_file, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 5:
                    class_id = int(parts[0])
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    bbox_width = float(parts[3])
                    bbox_height = float(parts[4])
                    
                    # Convertir de YOLO (normalisé) à COCO (absolut)
                    x_min = (x_center - bbox_width / 2) * width
                    y_min = (y_center - bbox_height / 2) * height
                    bbox_w = bbox_width * width
                    bbox_h = bbox_height * height
                    
                    area = bbox_w * bbox_h
                    
                    coco_data["annotations"].append({
                        "id": annotation_id,
                        "image_id": image_id,
                        "category_id": class_id,
                        "bbox": [x_min, y_min, bbox_w, bbox_h],
                        "area": area,
                        "iscrowd": 0
                    })
                    
                    annotation_id += 1
        
        # Sauvegarder le fichier COCO JSON
        coco_file = self.output_dir / "annotations_coco.json"
        with open(coco_file, 'w', encoding='utf-8') as f:
            json.dump(coco_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Format COCO créé: {coco_file}")
        print(f"  - {len(coco_data['images'])} images")
        print(f"  - {len(coco_data['annotations'])} annotations")
        print(f"  - {len(coco_data['categories'])} catégories")
        print()
    
    def create_yaml_config(self):
        """Créer le fichier de configuration YAML pour YOLO"""
        yaml_content = f"""# CAMIA-Factory Dataset Configuration
path: {self.output_dir.absolute()}
train: images
val: images

nc: {len(self.valid_classes)}
names: {self.valid_classes}
"""
        
        yaml_file = self.output_dir / "data.yaml"
        with open(yaml_file, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        print(f"✓ Configuration YAML créée: {yaml_file}")
        print()
    
    def generate_report(self):
        """Générer un rapport de traitement"""
        report_file = self.output_dir / "processing_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=== RAPPORT DE TRAITEMENT DATASET CAMIA-FACTORY ===\n\n")
            f.write(f"Date: 2026-04-15\n\n")
            
            f.write("Classes retirées:\n")
            for cls in self.medical_classes:
                f.write(f"  - {cls}\n")
            f.write("\n")
            
            f.write("Classes conservées (réindexées):\n")
            for idx, cls in enumerate(self.valid_classes):
                f.write(f"  {idx}: {cls}\n")
            f.write("\n")
            
            if self.issues:
                f.write("Problèmes détectés:\n")
                for issue in self.issues:
                    f.write(f"  - {issue}\n")
                f.write("\n")
            else:
                f.write("✓ Aucun problème détecté\n\n")
            
            f.write(f"Répertoire de sortie: {self.output_dir.absolute()}\n")
        
        print(f"✓ Rapport généré: {report_file}")
        print()
    
    def process_all(self):
        """Exécuter tout le pipeline de traitement"""
        print("\n" + "="*60)
        print("TRAITEMENT DU DATASET CAMIA-FACTORY")
        print("="*60 + "\n")
        
        # 1. Vérifier la cohérence
        valid_pairs = self.verify_consistency()
        
        # 2. Analyser la distribution
        class_counts, medical_files = self.analyze_distribution(valid_pairs)
        
        # 3. Nettoyer les labels
        self.clean_labels(valid_pairs)
        
        # 4. Copier les images
        self.copy_images(valid_pairs)
        
        # 5. Convertir en COCO
        self.convert_to_coco(valid_pairs)
        
        # 6. Créer la config YAML
        self.create_yaml_config()
        
        # 7. Générer le rapport
        self.generate_report()
        
        print("="*60)
        print("TRAITEMENT TERMINÉ")
        print("="*60)
        print(f"\nDataset nettoyé disponible dans: {self.output_dir.absolute()}")
        print("\nStructure:")
        print("  cleaned_dataset/")
        print("    ├── images/          (118 images)")
        print("    ├── labels/          (labels nettoyés)")
        print("    ├── annotations_coco.json")
        print("    ├── data.yaml")
        print("    └── processing_report.txt")
        print()


if __name__ == "__main__":
    # Configuration des chemins
    images_dir = r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\yolo_fin\fin_note\images"
    labels_dir = r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\yolo_fin\fin_note\labels"
    output_dir = r"C:\Users\eyama\OneDrive\Bureau\camIA-factory\yolo_fin\cleaned_dataset"
    
    # Créer et exécuter le processeur
    processor = YOLODatasetProcessor(images_dir, labels_dir, output_dir)
    processor.process_all()