#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'initialisation des employés CAMIA-Factory
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.employee import EmployeeService
from app.models.employee import EmployeeCreate
from app.core.database import Database


async def init_employees():
    """Créer les 10 employés de CAMIA-Factory"""
    
    # Connexion à la base de données
    await Database.connect()
    print("✅ Connecté à MongoDB")
    
    employees_data = [
        {
            "name": "adem",
            "full_name": "Adem",
            "department": "Production",
            "email": "adem@camia-factory.tn",
            "active": True
        },
        {
            "name": "alena",
            "full_name": "Alena",
            "department": "Production",
            "email": "alena@camia-factory.tn",
            "active": True
        },
        {
            "name": "ali",
            "full_name": "Ali",
            "department": "Production",
            "email": "ali@camia-factory.tn",
            "active": True
        },
        {
            "name": "amelie",
            "full_name": "Amelie",
            "department": "Production",
            "email": "amelie@camia-factory.tn",
            "active": True
        },
        {
            "name": "amir",
            "full_name": "Amir",
            "department": "Production",
            "email": "amir@camia-factory.tn",
            "active": True
        },
        {
            "name": "ibtihel",
            "full_name": "Ibtihel",
            "department": "Production",
            "email": "ibtihel@camia-factory.tn",
            "active": True
        },
        {
            "name": "insaf",
            "full_name": "Insaf",
            "department": "Production",
            "email": "insaf@camia-factory.tn",
            "active": True
        },
        {
            "name": "mohamed",
            "full_name": "Mohamed",
            "department": "Production",
            "email": "mohamed@camia-factory.tn",
            "active": True
        },
        {
            "name": "sami",
            "full_name": "Sami",
            "department": "Production",
            "email": "sami@camia-factory.tn",
            "active": True
        },
        {
            "name": "seline",
            "full_name": "Seline",
            "department": "Production",
            "email": "seline@camia-factory.tn",
            "active": True
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for emp_data in employees_data:
        try:
            employee = EmployeeCreate(**emp_data)
            created = await EmployeeService.create_employee(employee)
            print(f"✅ {created.full_name} créé avec succès")
            created_count += 1
        except ValueError as e:
            print(f"⚠️  {emp_data['full_name']}: Déjà existant")
            skipped_count += 1
        except Exception as e:
            print(f"❌ Erreur pour {emp_data['full_name']}: {e}")
    
    print("\n" + "="*50)
    print(f"📊 RÉSUMÉ:")
    print(f"   ✅ Créés: {created_count}")
    print(f"   ⚠️  Ignorés: {skipped_count}")
    print(f"   📋 Total: {len(employees_data)}")
    print("="*50)
    
    # Afficher la liste complète
    all_employees = await EmployeeService.list_employees(active_only=True)
    print(f"\n👥 EMPLOYÉS ACTIFS ({len(all_employees)}):")
    for emp in all_employees:
        print(f"   - {emp.full_name} ({emp.name}) - {emp.department}")
    
    await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(init_employees())