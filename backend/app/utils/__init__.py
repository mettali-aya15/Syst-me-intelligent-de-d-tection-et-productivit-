#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitaires
"""

# ✅ Imports existants (garde-les)
# ... (tout ce qui était déjà là)

# ✅ AJOUTE ÇA À LA FIN
from .file_hash import calculate_file_hash, calculate_uploaded_file_hash

__all__ = [
    # ... (garde ce qui était déjà dans __all__ si ça existe)
    'calculate_file_hash', 
    'calculate_uploaded_file_hash'
]