# 📁 Structure services/ (IA + logique métier)
services/
├── ai/
│   ├── detector.py        # YOLO pour détecter personnes, machines, produits
│   ├── tracker.py         # suivi des personnes (DeepSORT ou simple centroid)
│   └── pose.py            # détection assis/debout
│
├── logic/
│   ├── sewing_logic.py    # règles pour machine à coudre
│   └── knitting_logic.py  # règles pour machine à tricoter