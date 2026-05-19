#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service de gestion des employés
"""

from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.models.employee import Employee, EmployeeCreate, EmployeeUpdate

import logging
logger = logging.getLogger(__name__)


class EmployeeService:
    """Service de gestion des employés"""
    
    @staticmethod
    def _get_db():
        """Obtenir Database avec import tardif"""
        from app.core.database import Database
        if Database.db is None:
            raise Exception("Database not connected")
        return Database
    
    @staticmethod
    async def create_employee(employee_data: EmployeeCreate) -> Employee:
        """Créer un nouvel employé"""
        Database = EmployeeService._get_db()
        collection = Database.get_collection("employees")
        
        # Vérifier si le nom existe déjà
        existing = await collection.find_one({"name": employee_data.name.lower()})
        if existing:
            raise ValueError(f"Un employé avec le nom '{employee_data.name}' existe déjà")
        
        employee_dict = employee_data.model_dump()
        employee_dict["name"] = employee_dict["name"].lower()  # Normaliser en minuscule
        employee_dict["created_at"] = datetime.now()
        employee_dict["updated_at"] = datetime.now()
        
        result = await collection.insert_one(employee_dict)
        
        created_employee = await collection.find_one({"_id": result.inserted_id})
        logger.info(f"✅ Employé créé : {employee_data.full_name} ({employee_data.name})")
        
        return Employee(**created_employee)
    
    @staticmethod
    async def get_employee(employee_id: str) -> Optional[Employee]:
        """Récupérer un employé par ID"""
        Database = EmployeeService._get_db()
        collection = Database.get_collection("employees")
        
        employee_doc = await collection.find_one({"_id": ObjectId(employee_id)})
        return Employee(**employee_doc) if employee_doc else None
    
    @staticmethod
    async def get_employee_by_name(name: str) -> Optional[Employee]:
        """Récupérer un employé par nom YOLO"""
        Database = EmployeeService._get_db()
        collection = Database.get_collection("employees")
        
        employee_doc = await collection.find_one({"name": name.lower()})
        return Employee(**employee_doc) if employee_doc else None
    
    @staticmethod
    async def list_employees(active_only: bool = True) -> List[Employee]:
        """Lister tous les employés"""
        Database = EmployeeService._get_db()
        collection = Database.get_collection("employees")
        
        query = {"active": True} if active_only else {}
        cursor = collection.find(query).sort("full_name", 1)
        employees = await cursor.to_list(length=None)
        
        return [Employee(**emp) for emp in employees]
    
    @staticmethod
    async def update_employee(employee_id: str, update_data: EmployeeUpdate) -> Optional[Employee]:
        """Mettre à jour un employé"""
        Database = EmployeeService._get_db()
        collection = Database.get_collection("employees")
        
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        if not update_dict:
            return await EmployeeService.get_employee(employee_id)
        
        update_dict["updated_at"] = datetime.now()
        
        await collection.update_one(
            {"_id": ObjectId(employee_id)},
            {"$set": update_dict}
        )
        
        return await EmployeeService.get_employee(employee_id)
    
    @staticmethod
    async def delete_employee(employee_id: str) -> bool:
        """Supprimer un employé (soft delete)"""
        Database = EmployeeService._get_db()
        collection = Database.get_collection("employees")
        
        result = await collection.update_one(
            {"_id": ObjectId(employee_id)},
            {"$set": {"active": False, "updated_at": datetime.now()}}
        )
        
        return result.modified_count > 0
    
    @staticmethod
    async def get_absent_employees(detected_names: List[str]) -> List[Employee]:
        """Obtenir la liste des employés absents"""
        all_employees = await EmployeeService.list_employees(active_only=True)
        
        # Normaliser les noms détectés
        detected_normalized = [name.lower() for name in detected_names]
        
        # Filtrer les absents
        absent = [emp for emp in all_employees if emp.name not in detected_normalized]
        
        logger.info(f"👥 Total: {len(all_employees)} | Présents: {len(detected_names)} | Absents: {len(absent)}")
        
        return absent