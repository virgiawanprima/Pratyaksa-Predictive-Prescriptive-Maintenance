"""MQTT to Redis Streams bridge.

Subscribes to edge/data topic and fans sensor readings out to per-equipment
Redis streams consumed by the PRATYAKSA inference API.
"""
import json
import logging
import os

import paho.mqtt.client as mqtt
import redis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("pratyaksa.bridge")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASS = os.environ.get("MQTT_PASS")
if not MQTT_USER or not MQTT_PASS:
    raise RuntimeError("MQTT_USER/MQTT_PASS tidak diset — atur via .env atau environment variable")
STREAM_PREFIX = "stream:sensors:"

r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

FITUR_KOLOM = [
    "engine_rpm", "engine_load_pct", "coolant_temp_c", "coolant_pressure_kpa",
    "engine_oil_temp_c", "engine_oil_pressure_kpa", "transmission_oil_temp_c",
    "transmission_oil_pressure_kpa", "fuel_consumption_rate_lph",
    "boost_pressure_kpa", "exhaust_gas_temp_c", "battery_voltage_v",
    "vibration_x_g", "vibration_y_g", "vibration_z_g",
    "acoustic_emission_db", "hydraulic_main_pump_pressure_bar",
    "oil_viscosity_cst", "oil_particle_count_iso", "oil_moisture_pct",
    "wear_metal_fe_ppm", "wear_metal_cu_ppm", "payload_tonnage",
    "cycle_time_minutes", "haul_distance_km", "road_grade_pct",
    "ambient_temp_c", "humidity_pct", "dust_concentration_mgm3",
    "days_since_last_pm", "last_maintenance_hours", "oil_change_flag",
    "oil_particle_count_iso_dropout_flag", "payload_tonnage_dropout_flag",
    "cycle_time_minutes_dropout_flag", "haul_distance_km_dropout_flag",
    "oil_change_flag_dropout_flag",
]


def on_connect(client, userdata, flags, rc):
    client.subscribe("edge/data")
    logger.info("Bridge connected to MQTT (rc=%s)", rc)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload)
        etype = data.get("equipment_type", "unknown")
        raw_sensor = data.get("sensor", {})
        features = [raw_sensor.get(name, 0.0) for name in FITUR_KOLOM]
        stream_key = f"{STREAM_PREFIX}{etype}"
        r.xadd(stream_key, {
            "asset_id": data.get("asset_id", "edge_asset"),
            "equipment_type": etype,
            "timestamp": data.get("timestamp", ""),
            "features": json.dumps(features),
        })
        logger.info("Data masuk ke Redis Stream: %s", stream_key)
    except Exception:
        logger.exception("Bridge error memproses pesan MQTT")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(MQTT_USER, MQTT_PASS)

client.connect("mosquitto", 1883, 60)
logger.info("Bridge starting loop_forever")
client.loop_forever()
