# Plant Reminder Bot

Bot de Telegram para recordatorios de riego de plantas, ejecutado automaticamente via GitHub Actions.

## Descripcion

Este bot revisa diariamente el estado de tus plantas y te envia recordatorios por Telegram cuando necesitan ser regadas. El sistema:

- Detecta automaticamente la estacion del ano
- Ajusta los intervalos de riego segun la temporada
- Registra el historial de riegos
- Envia mensajes personalizados con urgencia y motivacion

## Configuracion Inicial

### 1. Obtener tu Chat ID de Telegram

1. Abre Telegram y busca el bot `@mazarredo_plants_bot`
2. Envia cualquier mensaje al bot (por ejemplo: "hola")
3. Abre esta URL en tu navegador (reemplaza `TU_TOKEN` con el token del bot):
   ```
   https://api.telegram.org/botTU_TOKEN/getUpdates
   ```
4. Busca en la respuesta JSON el campo `"chat":{"id":XXXXXXXX}`
5. Ese numero es tu Chat ID

**Alternativa:** Busca el bot `@userinfobot` en Telegram y te dira tu Chat ID.

### 2. Crear el repositorio en GitHub

1. Ve a [github.com/new](https://github.com/new)
2. Nombre del repositorio: `plant-reminder-bot`
3. Selecciona "Private" (recomendado)
4. NO inicialices con README (ya tenemos uno)
5. Haz clic en "Create repository"

### 3. Configurar los Secretos en GitHub

1. Ve a tu repositorio en GitHub
2. Settings > Secrets and variables > Actions
3. Haz clic en "New repository secret"
4. Agrega estos dos secretos:

| Nombre | Valor |
|--------|-------|
| `TELEGRAM_TOKEN` | El token de tu bot (ej: `8313249901:AAH3i1yduOslCbOvmxPzaxnS1uMQQMxhXto`) |
| `TELEGRAM_CHAT_ID` | Tu Chat ID de Telegram |

### 4. Subir el codigo

```bash
cd plant-reminder-bot
git init
git add .
git commit -m "Initial commit: Plant reminder bot"
git branch -M main
git remote add origin git@github.com:TU_USUARIO/plant-reminder-bot.git
git push -u origin main
```

### 5. Verificar que funciona

1. Ve a tu repositorio en GitHub
2. Actions > Plant Watering Reminder
3. Haz clic en "Run workflow" > "Run workflow"
4. Espera a que termine y revisa tu Telegram

## Personalizar las Plantas

Edita el archivo `data/plants_config.json`:

```json
{
  "plants": [
    {
      "id": "mi_planta",
      "name": "Mi Planta Favorita",
      "emoji": "🌸",
      "watering_schedule": {
        "spring": {"min": 5, "max": 7},
        "summer": {"min": 3, "max": 5},
        "autumn": {"min": 7, "max": 10},
        "winter": {"min": 10, "max": 14}
      }
    }
  ]
}
```

- `id`: Identificador unico (sin espacios ni caracteres especiales)
- `name`: Nombre que aparecera en los mensajes
- `emoji`: Emoji para identificar la planta
- `watering_schedule`: Dias entre riegos para cada estacion

## Registrar un Riego Manual

Cuando riegues una planta, actualiza `data/watering_log.json`:

```json
{
  "mi_planta": {
    "last_watered": "2026-01-25",
    "history": ["2026-01-25", "2026-01-15", "2026-01-05"]
  }
}
```

Haz commit y push del cambio:

```bash
git add data/watering_log.json
git commit -m "Watered mi_planta"
git push
```

## Sistema de Tracking

El archivo `data/watering_log.json` almacena:

- `last_watered`: Fecha del ultimo riego (formato: YYYY-MM-DD)
- `history`: Historial de todos los riegos

El bot calcula automaticamente los dias desde el ultimo riego y compara con el rango recomendado para la estacion actual.

### Logica de urgencia:

- **URGENTE**: Excede el maximo de dias recomendado
- **Es momento**: Esta en el rango optimo (promedio del rango)
- **Pronto**: Se acerca al rango recomendado
- **OK**: No necesita riego todavia

## Testejar Localmente

1. Crea un archivo `.env` (NO lo commitees):
   ```
   TELEGRAM_TOKEN=tu_token_aqui
   TELEGRAM_CHAT_ID=tu_chat_id_aqui
   ```

2. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Ejecuta el bot:
   ```bash
   cd src
   export $(cat ../.env | xargs) && python plant_reminder.py
   ```

## Ajustar el Horario

Edita `.github/workflows/plant-reminder.yml`:

```yaml
on:
  schedule:
    - cron: '0 7 * * *'  # 7:00 UTC = 8:00 Madrid (invierno)
```

Formato cron: `minuto hora dia mes dia_semana`

Ejemplos:
- `'0 6 * * *'` - 7:00 AM Madrid (invierno)
- `'30 7 * * *'` - 8:30 AM Madrid (invierno)
- `'0 7 * * 1-5'` - Solo dias laborables

## Estaciones del Ano

El bot detecta automaticamente la estacion:

| Estacion | Meses |
|----------|-------|
| Primavera | Marzo, Abril, Mayo |
| Verano | Junio, Julio, Agosto |
| Otono | Septiembre, Octubre, Noviembre |
| Invierno | Diciembre, Enero, Febrero |

## Estructura del Proyecto

```
plant-reminder-bot/
├── .github/workflows/
│   └── plant-reminder.yml    # GitHub Actions workflow
├── src/
│   ├── plant_reminder.py     # Script principal
│   ├── config.py             # Configuracion
│   └── utils.py              # Funciones auxiliares
├── data/
│   ├── plants_config.json    # Configuracion de plantas
│   └── watering_log.json     # Historial de riegos
├── requirements.txt          # Dependencias Python
├── .gitignore
└── README.md
```

## Troubleshooting

### El bot no envia mensajes
1. Verifica que los secretos esten bien configurados en GitHub
2. Asegurate de haber enviado al menos un mensaje al bot primero
3. Revisa los logs en GitHub Actions

### Error de permisos en GitHub Actions
Asegurate de que el workflow tenga permisos de escritura:
```yaml
permissions:
  contents: write
```

### Las plantas no aparecen
Verifica que `data/plants_config.json` tenga el formato JSON correcto.

## Licencia

Uso personal.
