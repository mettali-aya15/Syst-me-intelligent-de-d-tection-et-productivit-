import torch
from typing import List, Dict

class YOLODetector:
    def __init__(self, device="cpu"):
        self.model = torch.hub.load(
            "ultralytics/yolov5",
            "yolov5s",
            pretrained=True
        )
        self.device = device
        if device == "cuda":
            self.model.cuda()

    def detect(self, frame) -> List[Dict]:
        results = self.model(frame)
        detections = []

        for *box, conf, cls in results.xyxy[0].tolist():
            label = self.model.names[int(cls)]
            detections.append({
                "label": label,
                "confidence": float(conf),
                "bbox": [int(x) for x in box]
            })

        return detections
