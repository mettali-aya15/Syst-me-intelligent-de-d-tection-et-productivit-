#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fonctions de sécurité et authentification
JWT, hashing de mots de passe
"""

from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Dict

# Configuration
SECRET_KEY = "your-secret-key-change-this-in-production"  # À changer en production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 heures

# Context pour hashing de mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ========== HASHING DE MOTS DE PASSE ==========

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifier un mot de passe contre son hash
    
    Args:
        plain_password: Mot de passe en clair
        hashed_password: Hash du mot de passe
    
    Returns:
        True si le mot de passe correspond
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hasher un mot de passe
    
    Args:
        password: Mot de passe en clair
    
    Returns:
        Hash du mot de passe
    """
    return pwd_context.hash(password)


# ========== JWT TOKENS ==========

def create_access_token(
    data: Dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Créer un token JWT
    
    Args:
        data: Données à encoder dans le token
        expires_delta: Durée de validité du token
    
    Returns:
        Token JWT encodé
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict]:
    """
    Décoder un token JWT
    
    Args:
        token: Token JWT à décoder
    
    Returns:
        Payload du token ou None si invalide
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    
    except JWTError:
        return None