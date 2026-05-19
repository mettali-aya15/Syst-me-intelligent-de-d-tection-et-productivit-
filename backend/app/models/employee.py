#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèles Pydantic pour les employés
"""

from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, Annotated
from datetime import datetime
from bson import ObjectId


# ✅ CUSTOM SERIALIZER POUR ObjectId
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        from pydantic_core import core_schema
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ])

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")


class EmployeeCreate(BaseModel):
    """Modèle pour créer un employé"""
    name: str = Field(..., description="Nom détecté par YOLO (ex: aya, mohamed)")
    full_name: str = Field(..., description="Nom complet (ex: Aya Mahmoud)")
    email: Optional[EmailStr] = None
    department: Optional[str] = Field(None, description="Département (Production, Qualité, etc.)")
    photo_url: Optional[str] = None
    active: bool = Field(True, description="Employé actif ou non")


class Employee(BaseModel):
    """Modèle complet d'un employé"""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(None, alias="_id")
    name: str = Field(..., description="Nom détecté par YOLO (minuscule)")
    full_name: str
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    photo_url: Optional[str] = None
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class EmployeeUpdate(BaseModel):
    """Modèle pour mettre à jour un employé"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    photo_url: Optional[str] = None
    active: Optional[bool] = None