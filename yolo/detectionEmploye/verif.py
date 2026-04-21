import os, glob

label_dir = "labels"
errors = 0
for f in glob.glob(os.path.join(label_dir, "*.txt")):
    with open(f) as file:
        for i, line in enumerate(file, 1):
            parts = line.strip().split()
            if not parts: continue
            if len(parts) != 5:
                print(f"❌ Format invalide ligne {i} dans {os.path.basename(f)}")
                errors += 1
            else:
                cls = int(parts[0])
                if not (0 <= cls <= 16):
                    print(f"⚠️  ID hors plage ({cls}) dans {os.path.basename(f)}")
                    errors += 1

print("✅ Vérification terminée." if errors == 0 else f"🔧 {errors} erreur(s) détectée(s).")