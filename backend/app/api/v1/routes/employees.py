#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes API pour les employés
"""

from fastapi import APIRouter, HTTPException
from typing import List

from app.services.employee import EmployeeService
from app.models.employee import Employee, EmployeeCreate, EmployeeUpdate

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=Employee)
async def create_employee(employee: EmployeeCreate):
    """Créer un nouvel employé"""
    try:
        return await EmployeeService.create_employee(employee)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erreur création employé : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[Employee])
async def list_employees(active_only: bool = True):
    """Lister tous les employés"""
    try:
        return await EmployeeService.list_employees(active_only=active_only)
    except Exception as e:
        logger.error(f"❌ Erreur listage employés : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{employee_id}", response_model=Employee)
async def get_employee(employee_id: str):
    """Obtenir un employé par ID"""
    try:
        employee = await EmployeeService.get_employee(employee_id)
        if not employee:
            raise HTTPException(status_code=404, detail="Employé introuvable")
        return employee
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur récupération employé : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{employee_id}", response_model=Employee)
async def update_employee(employee_id: str, update_data: EmployeeUpdate):
    """Mettre à jour un employé"""
    try:
        employee = await EmployeeService.update_employee(employee_id, update_data)
        if not employee:
            raise HTTPException(status_code=404, detail="Employé introuvable")
        return employee
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour employé : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{employee_id}")
async def delete_employee(employee_id: str):
    """Supprimer un employé (soft delete)"""
    try:
        success = await EmployeeService.delete_employee(employee_id)
        if not success:
            raise HTTPException(status_code=404, detail="Employé introuvable")
        return {"message": "Employé supprimé avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur suppression employé : {e}")
        raise HTTPException(status_code=500, detail=str(e))