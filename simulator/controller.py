"""Simulación local sin acceso a equipos ni redes reales."""
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

def run(output, incident=False):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    start = datetime.now(timezone.utc)
    temperature, setpoint, defrost = 3.0, 3.0, 20
    with (output / "controller.jsonl").open("w") as logs, (output / "telemetry.jsonl").open("w") as telemetry:
        for step in range(30):
            timestamp = (start + timedelta(seconds=step * 10)).isoformat()
            if incident and step == 10:
                event = {"timestamp": timestamp, "event": "parameter_change", "session": "simulated-unauthorized-session", "authorized": False, "before": {"setpoint": setpoint, "defrost_minutes": defrost}, "after": {"setpoint": 12.0, "defrost_minutes": 60}}
                logs.write(json.dumps(event) + "\n")
                setpoint, defrost = 12.0, 60
            temperature += (setpoint - temperature) * 0.15
            telemetry.write(json.dumps({"timestamp": timestamp, "temperature": round(temperature, 3), "setpoint": setpoint, "defrost_minutes": defrost}) + "\n")
    (output / "manifest.json").write_text(json.dumps({"simulation": True, "clock": "UTC", "synthetic_interval_seconds": 10, "incident": incident}, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--incident", action="store_true")
    options = parser.parse_args()
    run(options.output, options.incident)
