#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitaire pour calculer le hash MD5 d'un fichier
"""

import hashlib
from pathlib import Path


def calculate_file_hash(file_path: str) -> str:
    """
    Calculer le hash MD5 d'un fichier
    
    Args:
        file_path: Chemin vers le fichier
        
    Returns:
        Hash MD5 en hexadécimal
    """
    hash_md5 = hashlib.md5()
    
    with open(file_path, "rb") as f:
        # Lire par chunks pour ne pas charger tout le fichier en mémoire
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    
    return hash_md5.hexdigest()


async def calculate_uploaded_file_hash(file) -> str:
    """
    Calculer le hash d'un fichier uploadé (UploadFile de FastAPI)
    
    Args:
        file: UploadFile object
        
    Returns:
        Hash MD5 en hexadécimal
    """
    hash_md5 = hashlib.md5()
    
    # Lire le contenu
    content = await file.read()
    hash_md5.update(content)
    
    # Remettre le curseur au début pour que le fichier puisse être relu
    await file.seek(0)
    
    return hash_md5.hexdigest()