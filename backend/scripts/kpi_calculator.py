from collections import defaultdict

class KPICalculator:
    def __init__(self):
        self.stats = defaultdict(int)

    def update(self, event: dict):
        """
        event example:
        {
          "workstation_id": 1,
          "status": "WORKING" | "IDLE",
          "employee_present": True,
          "duration": 1
        }
        """
        duration = event.get("duration", 1)

        if event["status"] == "WORKING":
            self.stats["working_time"] += duration
        else:
            self.stats["idle_time"] += duration

        if event.get("employee_present"):
            self.stats["presence_time"] += duration

        self.stats["total_time"] += duration

    def generate_report(self, start, end):
        total = max(self.stats["total_time"], 1)

        productivity = (self.stats["working_time"] / total) * 100
        utilization = (self.stats["working_time"] / total) * 100

        return {
            "Start time": start.isoformat(),
            "End time": end.isoformat(),
            "Total analyzed time (s)": total,
            "Working time (s)": self.stats["working_time"],
            "Idle time (s)": self.stats["idle_time"],
            "Presence time (s)": self.stats["presence_time"],
            "Productivity (%)": round(productivity, 2),
            "Workstation utilization (%)": round(utilization, 2)
        }