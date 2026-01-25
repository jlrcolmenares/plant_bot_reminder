"""
Configuracion del bot de recordatorios de riego.
"""
import os
from pathlib import Path

# Rutas de archivos
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
PLANTS_CONFIG_FILE = DATA_DIR / "plants_config.json"
WATERING_LOG_FILE = DATA_DIR / "watering_log.json"

# Telegram
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Timezone
TIMEZONE = "Europe/Madrid"

# Estaciones del ano (hemisferio norte)
SEASONS = {
    "spring": [3, 4, 5],      # Marzo, Abril, Mayo
    "summer": [6, 7, 8],      # Junio, Julio, Agosto
    "autumn": [9, 10, 11],    # Septiembre, Octubre, Noviembre
    "winter": [12, 1, 2]      # Diciembre, Enero, Febrero
}

# Mensajes motivacionales
MOTIVATIONAL_MESSAGES = [
    "Tus plantas te lo agradeceran!",
    "Un poco de agua y mucho amor!",
    "Las plantas felices hacen hogares felices!",
    "Recuerda: el agua es vida!",
    "Hoy es un gran dia para cuidar de tus plantas!",
    "Tus plantas confian en ti!",
    "El riego es un acto de amor!",
    "Plantas hidratadas = Dueno feliz!",
]

# Mensajes segun urgencia
URGENCY_MESSAGES = {
    "overdue": "URGENTE! Esta planta necesita agua YA!",
    "due": "Es momento de regar esta planta.",
    "soon": "Pronto necesitara agua, estate atento.",
    "ok": "Esta planta esta bien por ahora."
}
