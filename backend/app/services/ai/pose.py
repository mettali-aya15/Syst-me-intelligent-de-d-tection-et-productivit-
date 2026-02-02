def is_sitting(person_bbox) -> bool:
    """
    Détection très simple : si bbox hauteur < 60% machine height → assis
    """
    x1, y1, x2, y2 = person_bbox
    height = y2 - y1
    if height < 120:  # seuil arbitraire, calibrer selon caméra
        return True
    return False

def is_absent(person_bbox, machine_bbox) -> bool:
    """
    Détection très simple : si personne hors bbox machine → absent
    """
    px1, py1, px2, py2 = person_bbox
    mx1, my1, mx2, my2 = machine_bbox
    # Vérifier si les bboxes ne se chevauchent pas
    if px2 < mx1 or px1 > mx2 or py2 < my1 or py1 > my2:
        return True
    return False
