#!/usr/bin/env python3
"""
Bot de Telegram para recordatorios de riego de plantas.
Ejecutado diariamente via GitHub Actions.
"""
import sys
import time
import logging
import requests
from datetime import datetime

from config import TELEGRAM_API_URL, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN, DATA_DIR
from utils import (
    get_current_season,
    get_current_datetime,
    load_plants_config,
    load_watering_log,
    save_watering_log,
    days_since_last_watering,
    get_watering_urgency,
    should_send_reminder,
    format_daily_summary,
    logger
)

LAST_UPDATE_FILE = DATA_DIR / "last_update_id.txt"


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


def get_last_update_id() -> int:
    """Obtiene el ultimo update_id procesado."""
    try:
        if LAST_UPDATE_FILE.exists():
            return int(LAST_UPDATE_FILE.read_text().strip())
    except (ValueError, IOError):
        pass
    return 0


def save_last_update_id(update_id: int) -> None:
    """Guarda el ultimo update_id procesado."""
    try:
        LAST_UPDATE_FILE.write_text(str(update_id))
    except IOError as e:
        logger.error(f"Error guardando last_update_id: {e}")


def get_telegram_updates(offset: int = 0) -> list:
    """Obtiene los mensajes nuevos de Telegram."""
    url = f"{TELEGRAM_API_URL}/getUpdates"
    params = {"offset": offset, "timeout": 5}

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                return data.get("result", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Error obteniendo updates: {e}")

    return []


def process_watering_commands() -> list[str]:
    """
    Procesa comandos /regar de Telegram y actualiza el log.

    Returns:
        Lista de mensajes de confirmacion para enviar.
    """
    config = load_plants_config()
    plants = {p["id"]: p for p in config.get("plants", [])}
    plant_aliases = {}
    for pid, pdata in plants.items():
        plant_aliases[pid] = pid
        plant_aliases[pid.lower()] = pid
        # Alias cortos
        if pid == "plectranthus":
            plant_aliases["dinero"] = pid
        if pid == "strelitzia":
            plant_aliases["ave"] = pid
            plant_aliases["paraiso"] = pid

    last_update_id = get_last_update_id()
    logger.info(f"Ultimo update_id procesado: {last_update_id}")

    offset = last_update_id + 1 if last_update_id else 0
    logger.info(f"Buscando updates con offset: {offset}")

    updates = get_telegram_updates(offset=offset)
    logger.info(f"Updates recibidos: {len(updates)}")

    if not updates:
        logger.info("No hay mensajes nuevos de Telegram")
        return []

    watering_log = load_watering_log()
    confirmations = []
    new_last_update_id = last_update_id

    for update in updates:
        update_id = update.get("update_id", 0)
        new_last_update_id = max(new_last_update_id, update_id)

        message = update.get("message", {})
        chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "").strip()

        logger.info(f"Update {update_id}: chat_id={chat_id}, text='{text[:50]}'")

        # Solo procesar mensajes de nuestro chat
        if chat_id != TELEGRAM_CHAT_ID:
            logger.info(f"Ignorando mensaje de chat_id {chat_id} (esperado: {TELEGRAM_CHAT_ID})")
            continue

        # Comando /regar <planta>
        if text.lower().startswith("/regar"):
            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                confirmations.append("Uso: /regar <planta>\nPlantas: " + ", ".join(plants.keys()))
                continue

            plant_query = parts[1].strip().lower()
            plant_id = plant_aliases.get(plant_query)

            if not plant_id or plant_id not in plants:
                confirmations.append(f"Planta '{parts[1]}' no encontrada.\nPlantas disponibles: {', '.join(plants.keys())}")
                continue

            # Registrar riego
            today = get_current_datetime().strftime("%Y-%m-%d")
            if plant_id not in watering_log:
                watering_log[plant_id] = {"last_watered": None, "history": []}

            watering_log[plant_id]["last_watered"] = today
            if today not in watering_log[plant_id]["history"]:
                watering_log[plant_id]["history"].insert(0, today)
                # Mantener solo los ultimos 30 registros
                watering_log[plant_id]["history"] = watering_log[plant_id]["history"][:30]

            plant_name = plants[plant_id].get("name", plant_id)
            plant_emoji = plants[plant_id].get("emoji", "🌱")
            confirmations.append(f"{plant_emoji} *{plant_name}* regada!\nRegistrado: {today}")
            logger.info(f"Riego registrado: {plant_id} - {today}")

        # Comando /plantas - listar plantas
        elif text.lower() == "/plantas":
            plant_list = "\n".join([f"- `{pid}`: {p.get('emoji', '')} {p.get('name', '')}"
                                    for pid, p in plants.items()])
            confirmations.append(f"*Plantas disponibles:*\n{plant_list}")

        # Comando /estado - estado actual
        elif text.lower() == "/estado":
            status_lines = []
            for pid, pdata in plants.items():
                days = days_since_last_watering(pid, watering_log)
                emoji = pdata.get("emoji", "🌱")
                name = pdata.get("name", pid)
                if days is not None:
                    status_lines.append(f"{emoji} {name}: {days} dias")
                else:
                    status_lines.append(f"{emoji} {name}: sin registro")
            confirmations.append("*Estado de riego:*\n" + "\n".join(status_lines))

    # Guardar cambios
    if new_last_update_id > last_update_id:
        save_last_update_id(new_last_update_id)

    if watering_log:
        save_watering_log(watering_log)

    return confirmations


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

    # Debug: verificar que los secretos estan configurados
    token_status = "configurado" if TELEGRAM_TOKEN else "NO CONFIGURADO"
    chat_id_status = "configurado" if TELEGRAM_CHAT_ID else "NO CONFIGURADO"
    logger.info(f"TELEGRAM_TOKEN: {token_status} (longitud: {len(TELEGRAM_TOKEN)})")
    logger.info(f"TELEGRAM_CHAT_ID: {chat_id_status} (valor: {TELEGRAM_CHAT_ID})")
    logger.info(f"API URL: {TELEGRAM_API_URL[:40]}...")

    try:
        # 1. Procesar comandos de riego pendientes
        logger.info("Procesando comandos de Telegram...")
        confirmations = process_watering_commands()

        # 2. Enviar confirmaciones de riego
        for msg in confirmations:
            send_telegram_message(msg)

        # 3. Enviar recordatorios
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
