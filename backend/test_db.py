#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test de connexion MongoDB"""

import asyncio
from app.core.database import Database
from app.core.config import settings

async def test_connection():
    print("=" * 80)
    print("TEST CONNEXION MONGODB")
    print("=" * 80)
    
    print(f"\n📋 Configuration:")
    print(f"   URL: {settings.MONGODB_URL}")
    print(f"   DB: {settings.MONGODB_DB}")
    
    try:
        print(f"\n🔌 Tentative de connexion...")
        await Database.connect()
        print(f"✅ SUCCÈS - Database.db = {Database.db}")
        print(f"✅ SUCCÈS - Database.client = {Database.client}")
        
        # Test get_collection
        collection = Database.get_collection("video_uploads")
        print(f"✅ Collection obtenue : {collection}")
        
        # Test ping
        result = await Database.client.admin.command('ping')
        print(f"✅ Ping MongoDB : {result}")
        
        await Database.disconnect()
        print(f"\n✅ Déconnexion réussie")
        
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_connection())