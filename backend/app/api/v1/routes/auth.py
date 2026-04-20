#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes d'authentification
Login, Register, Token Management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Optional

from app.core.security import (
    create_access_token, 
    decode_access_token, 
    verify_password, 
    get_password_hash
)
from app.core.database import Database

import logging
logger = logging.getLogger(__name__)

# Créer le router
router = APIRouter()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ========== DEPENDENCY: GET CURRENT USER ==========

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dépendance pour obtenir l'utilisateur connecté
    
    Args:
        token: Token JWT
    
    Returns:
        Payload du token (user info)
    
    Raises:
        HTTPException: Si token invalide
    """
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


# ========== ROUTES ==========

@router.post("/login", response_model=dict)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint - Authentification par username/password
    
    - **username**: Nom d'utilisateur
    - **password**: Mot de passe
    
    Returns:
        Access token JWT
    """
    try:
        # Récupérer l'utilisateur depuis la DB
        users_collection = Database.get_collection("users")
        user = await users_collection.find_one({"username": form_data.username})
        
        # Si utilisateur n'existe pas ou mot de passe incorrect
        if not user or not verify_password(form_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Créer le token
        access_token = create_access_token(
            data={
                "sub": user["username"],
                "user_id": str(user["_id"]),
                "role": user.get("role", "viewer")
            }
        )
        
        logger.info(f"✅ Connexion réussie : {form_data.username}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "username": user["username"],
                "role": user.get("role", "viewer")
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors du login : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication"
        )


@router.post("/register", response_model=dict)
async def register(
    username: str,
    password: str,
    role: str = "viewer"
):
    """
    Register endpoint - Créer un nouvel utilisateur
    
    - **username**: Nom d'utilisateur (unique)
    - **password**: Mot de passe
    - **role**: Rôle (admin, supervisor, viewer)
    
    Returns:
        User créé
    """
    try:
        users_collection = Database.get_collection("users")
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = await users_collection.find_one({"username": username})
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Créer l'utilisateur
        from datetime import datetime
        
        new_user = {
            "username": username,
            "password_hash": get_password_hash(password),
            "role": role,
            "created_at": datetime.now()
        }
        
        result = await users_collection.insert_one(new_user)
        
        logger.info(f"✅ Nouvel utilisateur créé : {username}")
        
        return {
            "message": "User created successfully",
            "user_id": str(result.inserted_id),
            "username": username,
            "role": role
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'inscription : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration"
        )


@router.get("/me", response_model=dict)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Obtenir les informations de l'utilisateur connecté
    
    Returns:
        Informations utilisateur
    """
    return {
        "username": current_user.get("sub"),
        "user_id": current_user.get("user_id"),
        "role": current_user.get("role", "viewer")
    }


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout endpoint (côté client, supprimer le token)
    
    Returns:
        Message de confirmation
    """
    logger.info(f"✅ Déconnexion : {current_user.get('sub')}")
    
    return {
        "message": "Successfully logged out"
    }