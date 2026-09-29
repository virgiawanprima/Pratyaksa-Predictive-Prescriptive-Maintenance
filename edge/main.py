import time
import json
import logging
import os
import signal
import threading
from pathlib import Path
from .inference import EdgeInference
from .mqtt_edge import EdgeMQTT
from .nextion import NextionAlert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("pratyaksa.edge")

BASE_DIR = Path(__file__).resolve().parent.parent
META_PATH = BASE_DIR / "artifacts" / "artifact_deploy_meta.json"

with open(META_PATH) as f:
    META = json.load(f)

FITUR_KOLOM = META["FITUR_KOLOM"]
EQUIPMENT_TYPE = META.get("expert_types", ["haul_truck"])[0]
ASSET_ID = os.getenv("ASSET_ID", "edge-unit-01")
BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
NEXTION_PORT = os.getenv("NEXTION_PORT", "/dev/ttyAMA0")

def read_sensors() -> dict:
    # Dummy 37 fitur (sementara)
    data = {name: 0.0 for name in FITUR_KOLOM}
    data.update({
        "vibration_x_g": 1.0, "vibration_y_g": 1.0, "vibration_z_g": 1.0,
        "temperature_c": 50.0, "hydraulic_main_pump_pressure_bar": 275.0,
        "engine_rpm": 1500.0, "payload_tonnage": 40, "road_grade_pct": 5,
        "haul_distance_km": 3, "cycle_time_minutes": 10, "ambient_temp_c": 30,
        "humidity_pct": 60, "dust_concentration_mgm3": 1.5, "days_since_last_pm": 7,
        "last_maintenance_hours": 2000, "oil_change_flag": 0, "connectivity_loss_flag": 0
    })
    return data

shutdown_event = threading.Event()

def shutdown(signum, frame):
    shutdown_event.set()
signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

def main():
    infer = EdgeInference()
    mqtt = EdgeMQTT(broker=BROKER, port=PORT)
    mqtt.connect()
    alert = NextionAlert(port=NEXTION_PORT)
    logger.info("Edge node started. Asset: %s, Type: %s", ASSET_ID, EQUIPMENT_TYPE)
    while not shutdown_event.is_set():
        try:
            data = read_sensors()
            data["asset_id"] = ASSET_ID
            data["equipment_type"] = EQUIPMENT_TYPE
            data["timestamp"] = time.time()
            risk, twin = infer.predict(data)
            payload = {
                "asset_id": ASSET_ID,
                "equipment_type": EQUIPMENT_TYPE,
                "sensor": data,
                "risk_score": risk,
                "twin": twin,
                "timestamp": data["timestamp"]
            }
            mqtt.publish(payload)
            if twin.get("alert_level", "normal") in ["warning", "critical"]:
                alert.send(twin["alert_level"], f"Risk:{risk:.2f}")
            # Event.wait: shutdown signal langsung memutus tidur (responsif SIGINT/SIGTERM)
            shutdown_event.wait(1.0)
        except Exception:
            logger.exception("Edge loop error")
            shutdown_event.wait(1.0)
    mqtt.disconnect()
    logger.info("Edge node stopped.")

if __name__ == "__main__":
    main()