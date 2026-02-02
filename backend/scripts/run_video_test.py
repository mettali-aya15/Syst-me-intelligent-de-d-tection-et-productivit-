import cv2
from datetime import datetime

from app.core.config import settings
from app.services.ai.detector import YOLODetector
from app.services.logic.sewing_logic import SewingMachineLogic
from app.services.logic.knitting_logic import KnittingMachineLogic
from scripts.kpi_calculator import KPICalculator
from app.core.logger import get_logger

logger = get_logger("VIDEO_TEST")

VIDEO_PATH = "data/videos/demo_factory.mp4"
FPS_SAMPLE = settings.FPS_PROCESSING # analyse 1 frame per second

def run_video_test():
    cap = cv2.VideoCapture(VIDEO_PATH)

    if not cap.isOpened():
        raise RuntimeError("Cannot open video")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * FPS_SAMPLE)

    detector = YOLODetector()
    sewing_logic = SewingMachineLogic(machine_id=1)
    knitting_logic = KnittingMachineLogic(machine_id=2)

    kpi = KPICalculator()

    frame_count = 0
    start_time = datetime.utcnow()

    logger.info("Starting video analysis")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % frame_interval != 0:
            continue

        detections = detector.detect(frame)

        # Sewing logic
        sewing_event = sewing_logic.process_frame(detections)
        if sewing_event:
            kpi.update(sewing_event)

        # Knitting logic
        knitting_event = knitting_logic.process_frame(detections)
        if knitting_event:
            kpi.update(knitting_event)

    cap.release()

    end_time = datetime.utcnow()
    report = kpi.generate_report(start_time, end_time)

    print("\n" + "=" * 40)
    print("📊 FINAL KPI REPORT")
    print("=" * 40)

    for k, v in report.items():
        print(f"{k}: {v}")

    logger.info("Video analysis completed")

if __name__ == "__main__":
    run_video_test()
