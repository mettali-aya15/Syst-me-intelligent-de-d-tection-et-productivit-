# Architecture Docker

┌───────────────────────────┐
│ Docker Host (Linux)       │
│                           │
│ ┌───────────────┐         │
│ │ fastapi-api   │◄────┐   │
│ └───────────────┘     │   │
│ ┌───────────────┐     │   │
│ │ ai-worker     │◄────┼── GPU
│ └───────────────┘     │   │
│ ┌───────────────┐     │   │
│ │ postgres      │◄────┘   │
│ └───────────────┘         │
└───────────────────────────┘

✔️ Séparation IA / API
✔️ GPU uniquement pour l’IA
✔️ API reste légère et stable

# Lancer le système
## Prérequis serveur
Ubuntu 22.04
NVIDIA Driver >= 525
Docker + docker-compose
NVIDIA Container Toolkit

## Installer support GPU Docker
sudo apt install nvidia-container-toolkit
sudo systemctl restart docker

## Lancer
cd docker
docker compose up -d --build

## Vérifier GPU
docker exec -it factory_ai nvidia-smi

# Consommation matérielle (réaliste)
Équipement  │   Recommandé
──────────────────────────────────
CPU	        │   8 cores
RAM	        │   32 Go
GPU	        │   RTX 3060 / A2000
Caméras	    │   4–12
FPS	        │   1 fps / caméra