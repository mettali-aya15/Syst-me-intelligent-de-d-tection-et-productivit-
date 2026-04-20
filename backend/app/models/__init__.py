#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèles Pydantic
"""

from .video import VideoUpload, VideoCreate, VideoStatus
from .detection import Detection, BoundingBox, FrameDetection
from .employee import Employee, EmployeeCreate, EmployeeUpdate
from .machine import Machine, MachineCreate, MachineUpdate, MachineStatus  # ✅ Maintenant ça existe
from .user import User, UserCreate, UserUpdate

__all__ = [
    # Video
    "VideoUpload",
    "VideoCreate",
    "VideoStatus",
    # Detection
    "Detection",
    "BoundingBox",
    "FrameDetection",
    # Employee
    "Employee",
    "EmployeeCreate",
    "EmployeeUpdate",
    # Machine
    "Machine",
    "MachineCreate",
    "MachineUpdate",
    "MachineStatus",
    # User
    "User",
    "UserCreate",
    "UserUpdate",
]