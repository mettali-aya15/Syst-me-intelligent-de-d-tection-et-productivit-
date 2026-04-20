#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèles Pydantic pour les utilisateurs
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from bson import ObjectId


class UserCreate(BaseModel):
    """Données pour créer un utilisateur"""
    username: str
    password: str
    role: str = "viewer"


class UserUpdate(BaseModel):
    """Données pour mettre à jour un utilisateur"""
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None


class User(BaseModel):
    """Utilisateur système"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    username: str
    password_hash: str
    role: str = "viewer"
    created_at: datetime = Field(default_factory=datetime.now)


class UserOut(BaseModel):
    """Utilisateur (sortie API - sans password)"""
    _id: str
    username: str
    role: str
    created_at: datetime