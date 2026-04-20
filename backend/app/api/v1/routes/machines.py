#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes API pour les machines
CRUD + Statuts + Anomalies + Disponibilité
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId

from app.models.machine import Machine, MachineCreate, MachineUpdate, MachineOut
from app.services.logic import MachineLogic
from core.database import Database

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=MachineOut)
async def create_machine(machine_data: MachineCreate):
    """
    Créer une nouvelle machine
    
    - **name**: Nom de la machine
    - **type**: Type (coffee_machine, oven, etc.)
    - **zone**: Zone (production, café, etc.)
    
    Returns:
        Machine créée
    """
    try:
        machine = await MachineLogic.create_machine(machine_data)
        
        return MachineOut(
            _id=str(machine.id),
            name=machine.name,
            type=machine.type,
            zone=machine.zone,
            status=machine.status,
            last_activity=machine.last_activity,
            total_detections=machine.total_detections,
            created_at=machine.created_at
        )
    
    except Exception as e:
        logger.error(f"❌ Erreur création machine : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[MachineOut])
async def list_machines(
    zone: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0)
):
    """
    Lister les machines
    
    - **zone**: Filtrer par zone
    - **status**: Filtrer par statut (active, stopped, maintenance)
    
    Returns:
        Liste des machines
    """
    try:
        collection = Database.get_collection("machines")
        
        query = {}
        if zone:
            query["zone"] = zone
        if status:
            query["status"] = status
        
        cursor = collection.find(query).sort("name", 1).skip(skip).limit(limit)
        machines = await cursor.to_list(length=limit)
        
        return [
            MachineOut(
                _id=str(m["_id"]),
                name=m["name"],
                type=m["type"],
                zone=m["zone"],
                status=m["status"],
                last_activity=m.get("last_activity"),
                total_detections=m.get("total_detections", 0),
                created_at=m["created_at"]
            )
            for m in machines
        ]
    
    except Exception as e:
        logger.error(f"❌ Erreur listage machines : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{machine_id}", response_model=MachineOut)
async def get_machine(machine_id: str):
    """
    Obtenir une machine par ID
    
    - **machine_id**: ID de la machine
    
    Returns:
        Détails de la machine
    """
    try:
        collection = Database.get_collection("machines")
        machine = await collection.find_one({"_id": ObjectId(machine_id)})
        
        if not machine:
            raise HTTPException(status_code=404, detail="Machine introuvable")
        
        return MachineOut(
            _id=str(machine["_id"]),
            name=machine["name"],
            type=machine["type"],
            zone=machine["zone"],
            status=machine["status"],
            last_activity=machine.get("last_activity"),
            total_detections=machine.get("total_detections", 0),
            created_at=machine["created_at"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur récupération machine : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{machine_id}", response_model=MachineOut)
async def update_machine(machine_id: str, update_data: MachineUpdate):
    """
    Mettre à jour une machine
    
    - **machine_id**: ID de la machine
    
    Returns:
        Machine mise à jour
    """
    try:
        machine = await MachineLogic.update_machine(machine_id, update_data)
        
        if not machine:
            raise HTTPException(status_code=404, detail="Machine introuvable")
        
        return MachineOut(
            _id=str(machine.id),
            name=machine.name,
            type=machine.type,
            zone=machine.zone,
            status=machine.status,
            last_activity=machine.last_activity,
            total_detections=machine.total_detections,
            created_at=machine.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour machine : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{machine_id}")
async def delete_machine(machine_id: str):
    """
    Supprimer une machine
    
    - **machine_id**: ID de la machine
    
    Returns:
        Message de confirmation
    """
    try:
        collection = Database.get_collection("machines")
        result = await collection.delete_one({"_id": ObjectId(machine_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Machine introuvable")
        
        return {"message": "Machine supprimée avec succès", "machine_id": machine_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur suppression machine : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{machine_id}/availability")
async def get_machine_availability(
    machine_id: str,
    days: int = Query(7, ge=1, le=30)
):
    """
    Calculer la disponibilité d'une machine
    
    - **machine_id**: ID de la machine
    - **days**: Nombre de jours à analyser
    
    Returns:
        Métriques de disponibilité
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        availability = await MachineLogic.calculate_machine_availability(
            machine_id=machine_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return availability
    
    except Exception as e:
        logger.error(f"❌ Erreur calcul disponibilité : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{machine_id}/maintenance-prediction")
async def predict_maintenance(machine_id: str):
    """
    Prédire le besoin de maintenance
    
    - **machine_id**: ID de la machine
    
    Returns:
        Prédiction de maintenance
    """
    try:
        prediction = await MachineLogic.predict_maintenance_need(machine_id)
        
        return prediction
    
    except Exception as e:
        logger.error(f"❌ Erreur prédiction maintenance : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/summary")
async def get_machines_status_summary():
    """
    Obtenir le résumé des statuts de toutes les machines
    
    Returns:
        Résumé des machines
    """
    try:
        summary = await MachineLogic.get_machines_status_summary()
        
        return summary
    
    except Exception as e:
        logger.error(f"❌ Erreur résumé machines : {e}")
        raise HTTPException(status_code=500, detail=str(e))