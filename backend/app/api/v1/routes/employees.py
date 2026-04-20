#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes API pour les employés
CRUD complet
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from bson import ObjectId

from app.models.employee import Employee, EmployeeCreate, EmployeeUpdate, EmployeeOut
from core.database import Database

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=EmployeeOut)
async def create_employee(employee_data: EmployeeCreate):
    """
    Créer un nouvel employé
    
    - **name**: Nom de l'employé
    - **code**: Code unique
    - **role**: Rôle (barista, serveur, etc.)
    
    Returns:
        Employé créé
    """
    try:
        employee = Employee(**employee_data.dict())
        
        collection = Database.get_collection("employees")
        
        # Vérifier unicité du code
        existing = await collection.find_one({"code": employee.code})
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Un employé avec le code '{employee.code}' existe déjà"
            )
        
        employee_dict = employee.dict(by_alias=True, exclude={"id"})
        result = await collection.insert_one(employee_dict)
        
        employee.id = result.inserted_id
        
        logger.info(f"✅ Employé créé : {employee.name}")
        
        return EmployeeOut(
            _id=str(employee.id),
            name=employee.name,
            code=employee.code,
            role=employee.role,
            is_active=employee.is_active,
            is_temp=employee.is_temp,
            last_seen=employee.last_seen,
            total_detections=employee.total_detections,
            created_at=employee.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur création employé : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[EmployeeOut])
async def list_employees(
    is_active: Optional[bool] = None,
    is_temp: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0)
):
    """
    Lister les employés
    
    - **is_active**: Filtrer par statut actif
    - **is_temp**: Filtrer par employés temporaires
    
    Returns:
        Liste des employés
    """
    try:
        collection = Database.get_collection("employees")
        
        query = {}
        if is_active is not None:
            query["is_active"] = is_active
        if is_temp is not None:
            query["is_temp"] = is_temp
        
        cursor = collection.find(query).sort("name", 1).skip(skip).limit(limit)
        employees = await cursor.to_list(length=limit)
        
        return [
            EmployeeOut(
                _id=str(emp["_id"]),
                name=emp["name"],
                code=emp["code"],
                role=emp["role"],
                is_active=emp["is_active"],
                is_temp=emp["is_temp"],
                last_seen=emp.get("last_seen"),
                total_detections=emp.get("total_detections", 0),
                created_at=emp["created_at"]
            )
            for emp in employees
        ]
    
    except Exception as e:
        logger.error(f"❌ Erreur listage employés : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{employee_id}", response_model=EmployeeOut)
async def get_employee(employee_id: str):
    """
    Obtenir un employé par ID
    
    - **employee_id**: ID de l'employé
    
    Returns:
        Détails de l'employé
    """
    try:
        collection = Database.get_collection("employees")
        employee = await collection.find_one({"_id": ObjectId(employee_id)})
        
        if not employee:
            raise HTTPException(status_code=404, detail="Employé introuvable")
        
        return EmployeeOut(
            _id=str(employee["_id"]),
            name=employee["name"],
            code=employee["code"],
            role=employee["role"],
            is_active=employee["is_active"],
            is_temp=employee["is_temp"],
            last_seen=employee.get("last_seen"),
            total_detections=employee.get("total_detections", 0),
            created_at=employee["created_at"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur récupération employé : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{employee_id}", response_model=EmployeeOut)
async def update_employee(employee_id: str, update_data: EmployeeUpdate):
    """
    Mettre à jour un employé
    
    - **employee_id**: ID de l'employé
    
    Returns:
        Employé mis à jour
    """
    try:
        collection = Database.get_collection("employees")
        
        update_dict = {
            k: v for k, v in update_data.dict(exclude_unset=True).items()
            if v is not None
        }
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")
        
        update_dict["updated_at"] = datetime.now()
        
        result = await collection.find_one_and_update(
            {"_id": ObjectId(employee_id)},
            {"$set": update_dict},
            return_document=True
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Employé introuvable")
        
        logger.info(f"✅ Employé mis à jour : {employee_id}")
        
        return EmployeeOut(
            _id=str(result["_id"]),
            name=result["name"],
            code=result["code"],
            role=result["role"],
            is_active=result["is_active"],
            is_temp=result["is_temp"],
            last_seen=result.get("last_seen"),
            total_detections=result.get("total_detections", 0),
            created_at=result["created_at"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour employé : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{employee_id}")
async def delete_employee(employee_id: str):
    """
    Supprimer un employé
    
    - **employee_id**: ID de l'employé
    
    Returns:
        Message de confirmation
    """
    try:
        collection = Database.get_collection("employees")
        result = await collection.delete_one({"_id": ObjectId(employee_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Employé introuvable")
        
        logger.info(f"✅ Employé supprimé : {employee_id}")
        
        return {"message": "Employé supprimé avec succès", "employee_id": employee_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur suppression employé : {e}")
        raise HTTPException(status_code=500, detail=str(e))