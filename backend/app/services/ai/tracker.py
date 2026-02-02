import numpy as np

class SimpleTracker:
    """
    Tracker simple par centroid (employés)
    """
    def __init__(self, max_distance=50):
        self.objects = {}  # id -> bbox
        self.next_id = 0
        self.max_distance = max_distance

    def update(self, detections):
        # detections: list of bboxes [x1,y1,x2,y2]
        updated_objects = {}
        for det in detections:
            centroid = [(det[0]+det[2])/2, (det[1]+det[3])/2]
            min_dist = float("inf")
            best_id = None
            for oid, obox in self.objects.items():
                ob_centroid = [(obox[0]+obox[2])/2, (obox[1]+obox[3])/2]
                dist = np.linalg.norm(np.array(centroid) - np.array(ob_centroid))
                if dist < min_dist and dist < self.max_distance:
                    min_dist = dist
                    best_id = oid
            if best_id is None:
                updated_objects[self.next_id] = det
                self.next_id += 1
            else:
                updated_objects[best_id] = det
        self.objects = updated_objects
        return self.objects
