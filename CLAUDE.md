# CLAUDE.md - Contexto para Claude Code

## Descripcion del Proyecto

Bot de Telegram para recordatorios de riego de plantas. Se ejecuta via GitHub Actions diariamente y envia mensajes cuando las plantas necesitan agua.

## Arquitectura

```
src/
├── plant_reminder.py   # Entry point, flujo principal, comandos Telegram
├── config.py           # Variables de entorno, constantes, configuracion
└── utils.py            # Funciones auxiliares, logica de negocio

data/
├── plants_config.json  # Configuracion de plantas (editable por usuario)
├── watering_log.json   # Historial de riegos (actualizado automaticamente)
└── last_update_id.txt  # Control de mensajes Telegram procesados
```

## Flujo de Ejecucion

1. `main()` en `plant_reminder.py` se ejecuta via GitHub Actions
2. Procesa comandos pendientes de Telegram (`/regar`, `/plantas`, `/estado`)
3. Actualiza `watering_log.json` si hubo riegos
4. Verifica que plantas necesitan riego (dias >= minimo recomendado)
5. Envia mensaje solo si hay plantas que regar
6. GitHub Actions hace commit de cambios en `data/`

## Decisiones de Diseno

### Logica de recordatorios
- Solo enviar mensaje cuando `dias_desde_ultimo_riego >= min_recomendado`
- Sin historial de riego = no enviar recordatorio (el usuario debe registrar el primer riego)
- Urgencia "overdue" cuando `dias >= max_recomendado`

### Comandos Telegram
- Se procesan en batch cuando el bot se ejecuta (no en tiempo real)
- `last_update_id.txt` evita reprocesar comandos antiguos
- Alias definidos en `process_watering_commands()` para nombres cortos

### Mensajes
- Estaciones en espanol (Primavera, Verano, Otono, Invierno)
- Un solo mensaje motivacional al final del resumen
- Formato Markdown para Telegram

## Variables de Entorno (Secretos GitHub)

- `TELEGRAM_TOKEN`: Token del bot de Telegram
- `TELEGRAM_CHAT_ID`: Chat ID del usuario (no el ID del bot)

## Consideraciones Tecnicas

### Telegram API
- Usar `getUpdates` con offset para evitar reprocesar mensajes
- Rate limits: el bot maneja reintentos en `send_telegram_message()`
- Error 404 = token o chat_id incorrecto

### GitHub Actions
- Cron `0 7 * * *` = 8:00 AM Madrid (invierno) / 9:00 AM (verano)
- Permisos `contents: write` necesarios para commit automatico
- `[skip ci]` en commits para evitar loops

### Zona horaria
- Configurada para Madrid (`Europe/Madrid`)
- Estaciones basadas en hemisferio norte

## Posibles Mejoras Futuras

1. **Respuesta en tiempo real**: Usar webhook en lugar de polling (requiere servidor)
2. **Botones inline**: Agregar botones al recordatorio para marcar riego inmediato
3. **Multiples usuarios**: Soporte para varios chat_ids
4. **Notificaciones push**: Ejecutar mas frecuentemente para respuesta rapida a comandos
5. **Fotos de plantas**: Permitir adjuntar fotos al historial
6. **Estadisticas**: Comando `/stats` para ver patrones de riego
7. **Recordatorio de fertilizante**: Anadir tracking de fertilizacion

## Comandos Utiles para Desarrollo

```bash
# Test local
cd src && export TELEGRAM_TOKEN=xxx TELEGRAM_CHAT_ID=yyy && python plant_reminder.py

# Ver logs de GitHub Actions
gh run list --workflow=plant-reminder.yml
gh run view <run-id> --log
```

## Notas del Dueno

- Usuario en Madrid, Espana
- 5 plantas: Strelitzia, Pothos, Calathea, Croton, Plectranthus
- Prefiere mensajes concisos, sin repeticion innecesaria
- Bot: @mazarredo_plants_bot
