#!/usr/bin/env python3
"""
Bot de Telegram para recordatorios de riego de plantas.
Ejecutado diariamente via GitHub Actions.
"""
import sys
import time
import logging
import requests

from config import TELEGRAM_API_URL, TELEGRAM_CHAT_ID
from utils import (
    get_current_season,
    load_plants_config,
    load_watering_log,
    days_since_last_watering,
    get_watering_urgency,
    should_send_reminder,
    format_daily_summary,
    logger
)


def send_telegram_message(message: str, parse_mode: str = "Markdown") -> bool:
    """
    Envia un mensaje a Telegram.

    Args:
        message: Texto del mensaje a enviar
        parse_mode: Formato del mensaje (Markdown o HTML)

    Returns:
        True si el mensaje se envio correctamente, False en caso contrario
    """
    if not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_CHAT_ID no configurado")
        return False

    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": parse_mode
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=30)

            if response.status_code == 200:
                logger.info("Mensaje enviado correctamente a Telegram")
                return True
            elif response.status_code == 429:
                # Rate limit - esperar y reintentar
                retry_after = response.json().get("parameters", {}).get("retry_after", 30)
                logger.warning(f"Rate limit alcanzado. Esperando {retry_after} segundos...")
                time.sleep(retry_after)
            else:
                logger.error(f"Error al enviar mensaje: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout en intento {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(5)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexion: {e}")
            return False

    return False


def check_plants_and_notify() -> bool:
    """
    Verifica el estado de todas las plantas y envia notificaciones.

    Returns:
        True si todo fue exitoso, False si hubo errores
    """
    # Cargar configuracion
    config = load_plants_config()
    plants = config.get("plants", [])

    if not plants:
        logger.warning("No hay plantas configuradas")
        return True

    # Cargar historial de riegos
    watering_log = load_watering_log()

    # Obtener estacion actual
    season = get_current_season()
    logger.info(f"Estacion actual: {season}")

    # Verificar cada planta
    plants_to_water = []

    for plant in plants:
        plant_id = plant.get("id")
        plant_name = plant.get("name")
        schedule = plant.get("watering_schedule", {})

        # Calcular dias desde ultimo riego
        days_since = days_since_last_watering(plant_id, watering_log)

        # Determinar urgencia
        urgency = get_watering_urgency(days_since, schedule, season)

        logger.info(
            f"Planta: {plant_name} | "
            f"Dias desde riego: {days_since} | "
            f"Urgencia: {urgency}"
        )

        # Agregar a lista si necesita riego
        if should_send_reminder(urgency):
            plants_to_water.append({
                "plant": plant,
                "days_since": days_since,
                "urgency": urgency
            })

    # Enviar resumen
    if plants_to_water:
        message = format_daily_summary(plants_to_water, season)
        success = send_telegram_message(message)

        if not success:
            logger.error("No se pudo enviar el mensaje de recordatorio")
            return False

        logger.info(f"Recordatorio enviado para {len(plants_to_water)} plantas")
    else:
        logger.info("No hay plantas que necesiten riego hoy")
        # Opcionalmente enviar mensaje de que todo esta bien
        # send_telegram_message("Hoy no hay plantas que necesiten riego. Buen dia!")

    return True


def main() -> int:
    """Funcion principal del bot."""
    logger.info("=" * 50)
    logger.info("Iniciando bot de recordatorios de riego")
    logger.info("=" * 50)

    try:
        success = check_plants_and_notify()
        if success:
            logger.info("Bot ejecutado correctamente")
            return 0
        else:
            logger.error("El bot encontro errores durante la ejecucion")
            return 1
    except Exception as e:
        logger.exception(f"Error inesperado: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
