"""
Utilidades para el bot de recordatorios de riego.
"""
import json
import random
import logging
from datetime import datetime
from typing import Optional

import pytz
from dateutil import parser as date_parser

from config import (
    TIMEZONE,
    SEASONS,
    MOTIVATIONAL_MESSAGES,
    URGENCY_MESSAGES,
    PLANTS_CONFIG_FILE,
    WATERING_LOG_FILE
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_current_datetime() -> datetime:
    """Obtiene la fecha y hora actual en la zona horaria de Madrid."""
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz)


def get_current_season() -> str:
    """Determina la estacion actual basandose en el mes."""
    month = get_current_datetime().month
    for season, months in SEASONS.items():
        if month in months:
            return season
    return "winter"


def load_plants_config() -> dict:
    """Carga la configuracion de plantas desde el archivo JSON."""
    try:
        with open(PLANTS_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Archivo de configuracion no encontrado: {PLANTS_CONFIG_FILE}")
        return {"plants": []}
    except json.JSONDecodeError as e:
        logger.error(f"Error al parsear JSON de configuracion: {e}")
        return {"plants": []}


def load_watering_log() -> dict:
    """Carga el historial de riegos desde el archivo JSON."""
    try:
        with open(WATERING_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Archivo de log no encontrado, creando nuevo: {WATERING_LOG_FILE}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error al parsear JSON de log: {e}")
        return {}


def save_watering_log(log: dict) -> bool:
    """Guarda el historial de riegos en el archivo JSON."""
    try:
        with open(WATERING_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error al guardar log de riegos: {e}")
        return False


def days_since_last_watering(plant_id: str, log: dict) -> Optional[int]:
    """Calcula los dias desde el ultimo riego de una planta."""
    if plant_id not in log:
        return None

    last_watered = log[plant_id].get("last_watered")
    if not last_watered:
        return None

    try:
        last_date = date_parser.parse(last_watered).date()
        today = get_current_datetime().date()
        return (today - last_date).days
    except Exception as e:
        logger.error(f"Error al calcular dias desde ultimo riego: {e}")
        return None


def get_watering_urgency(days: Optional[int], schedule: dict, season: str) -> str:
    """
    Determina la urgencia del riego basandose en los dias transcurridos.

    Returns:
        'overdue': Excede el maximo recomendado
        'due': Esta en el rango optimo de riego
        'soon': Se acerca al rango optimo
        'ok': No necesita riego todavia
    """
    if days is None:
        return "due"  # Sin historial, mejor regar

    season_schedule = schedule.get(season, {"min": 7, "max": 10})
    min_days = season_schedule["min"]
    max_days = season_schedule["max"]

    # Calcular punto optimo (promedio del rango)
    optimal = (min_days + max_days) // 2

    if days >= max_days:
        return "overdue"
    elif days >= optimal:
        return "due"
    elif days >= min_days - 1:
        return "soon"
    else:
        return "ok"


def should_send_reminder(urgency: str) -> bool:
    """Determina si se debe enviar recordatorio segun la urgencia."""
    return urgency in ["overdue", "due"]


def get_random_motivational_message() -> str:
    """Devuelve un mensaje motivacional aleatorio."""
    return random.choice(MOTIVATIONAL_MESSAGES)


def format_plant_message(
    plant: dict,
    days_since: Optional[int],
    urgency: str,
    season: str
) -> str:
    """Formatea el mensaje para una planta especifica."""
    emoji = plant.get("emoji", "🌱")
    name = plant.get("name", "Planta")
    schedule = plant.get("watering_schedule", {})
    season_schedule = schedule.get(season, {"min": 7, "max": 10})

    urgency_msg = URGENCY_MESSAGES.get(urgency, "")
    motivational = get_random_motivational_message()

    if days_since is not None:
        days_text = f"Dias desde ultimo riego: {days_since}"
    else:
        days_text = "Sin registro de riego previo"

    message = f"""
{emoji} *{name}*

{urgency_msg}

{days_text}
Rango recomendado ({season}): cada {season_schedule['min']}-{season_schedule['max']} dias

_{motivational}_
"""
    return message.strip()


def format_daily_summary(plants_to_water: list[dict], season: str) -> str:
    """Formatea el resumen diario de riego."""
    if not plants_to_water:
        return "Hoy no hay plantas que necesiten riego. Buen dia!"

    header = f"🌱 *RECORDATORIO DE RIEGO* 🌱\n"
    header += f"📅 {get_current_datetime().strftime('%d/%m/%Y')}\n"
    header += f"🍃 Estacion: {season.capitalize()}\n"
    header += "─" * 20 + "\n\n"

    body = "\n\n".join([
        format_plant_message(
            p["plant"],
            p["days_since"],
            p["urgency"],
            season
        )
        for p in plants_to_water
    ])

    return header + body
