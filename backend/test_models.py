#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test des 2 modèles YOLO - Vérifier les classes
"""

from ultralytics import YOLO
from pathlib import Path

# Chemins
MODEL_PERSON = Path("data/models/best_person.pt")
MODEL_GENERAL = Path("data/models/best_objects.pt")

print("=" * 80)
print("VÉRIFICATION DES CLASSES YOLO")
print("=" * 80)

# Modèle 1 : Employés
if MODEL_PERSON.exists():
    print(f"\n📦 Modèle Employés : {MODEL_PERSON}")
    model_person = YOLO(str(MODEL_PERSON))
    print(f"   Nombre de classes : {len(model_person.names)}")
    print(f"   Classes :")
    for idx, name in model_person.names.items():
        print(f"      {idx}: {name}")
else:
    print(f"\n❌ Modèle introuvable : {MODEL_PERSON}")

# Modèle 2 : Objets
print("\n" + "-" * 80)
if MODEL_GENERAL.exists():
    print(f"\n📦 Modèle Objets : {MODEL_GENERAL}")
    model_general = YOLO(str(MODEL_GENERAL))
    print(f"   Nombre de classes : {len(model_general.names)}")
    print(f"   Classes :")
    for idx, name in model_general.names.items():
        print(f"      {idx}: {name}")
else:
    print(f"\n❌ Modèle introuvable : {MODEL_GENERAL}")

print("\n" + "=" * 80)