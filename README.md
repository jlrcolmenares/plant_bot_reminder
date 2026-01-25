# Plant Reminder Bot

Bot de Telegram para recordatorios de riego de plantas, ejecutado automaticamente via GitHub Actions.

## Descripcion

Este bot revisa diariamente el estado de tus plantas y te envia recordatorios por Telegram cuando necesitan ser regadas. El sistema:

- Detecta automaticamente la estacion del ano
- Ajusta los intervalos de riego segun la temporada
- Permite registrar riegos via comandos de Telegram
- Solo envia recordatorios cuando realmente toca regar

## Uso Diario

### Comandos de Telegram

Envia estos comandos al bot `@mazarredo_plants_bot`:

| Comando | Descripcion |
|---------|-------------|
| `/regar <planta>` | Registra que regaste una planta |
| `/plantas` | Lista todas las plantas disponibles |
| `/estado` | Muestra dias desde ultimo riego de cada planta |

### Ejemplos de riego

```
/regar pothos
/regar calathea
/regar dinero      (alias para plectranthus)
/regar ave         (alias para strelitzia)
```

### Plantas disponibles

| ID | Alias | Nombre |
|----|-------|--------|
| `strelitzia` | `ave`, `paraiso` | Ave del Paraiso |
| `pothos` | - | Pothos |
| `calathea` | - | Calathea |
| `croton` | - | Croton |
| `plectranthus` | `dinero` | Planta del dinero |

### Cuando llegan los recordatorios

- El bot se ejecuta diariamente a las **8:00 AM** (hora Madrid)
- Solo envia mensaje si alguna planta necesita riego (dias >= minimo recomendado)
- Los comandos de riego se procesan en la siguiente ejecucion del bot

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

### 2. Configurar los Secretos en GitHub

1. Ve a tu repositorio en GitHub
2. Settings > Secrets and variables > Actions
3. Haz clic en "New repository secret"
4. Agrega estos dos secretos:

| Nombre | Valor |
|--------|-------|
| `TELEGRAM_TOKEN` | El token de tu bot |
| `TELEGRAM_CHAT_ID` | Tu Chat ID de Telegram |

### 3. Verificar que funciona

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
- `watering_schedule`: Dias entre riegos para cada estacion (min = cuando enviar recordatorio, max = urgente)

## Logica de Recordatorios

El bot solo envia recordatorio cuando:

1. La planta tiene historial de riego, **Y**
2. Dias desde ultimo riego >= minimo recomendado para la estacion

| Estado | Condicion | Mensaje |
|--------|-----------|---------|
| OK | dias < min | No envia mensaje |
| Es momento | dias >= min | "Es momento de regar esta planta" |
| URGENTE | dias >= max | "URGENTE! Esta planta necesita agua YA!" |

## Estaciones del Ano

El bot detecta automaticamente la estacion:

| Estacion | Meses |
|----------|-------|
| Primavera | Marzo, Abril, Mayo |
| Verano | Junio, Julio, Agosto |
| Otono | Septiembre, Octubre, Noviembre |
| Invierno | Diciembre, Enero, Febrero |

## Ajustar el Horario

Edita `.github/workflows/plant-reminder.yml`:

```yaml
on:
  schedule:
    - cron: '0 7 * * *'  # 7:00 UTC = 8:00 Madrid (invierno)
```

Formato cron: `minuto hora dia mes dia_semana`

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
│   ├── watering_log.json     # Historial de riegos
│   └── last_update_id.txt    # Control de mensajes procesados
├── requirements.txt
├── .gitignore
├── CLAUDE.md                 # Contexto para Claude Code
└── README.md
```

## Testear Localmente

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

## Troubleshooting

### El bot no envia mensajes
1. Verifica que los secretos esten bien configurados en GitHub (sin espacios extra)
2. Asegurate de haber enviado al menos un mensaje al bot primero
3. Revisa los logs en GitHub Actions

### Los comandos /regar no funcionan
1. Asegurate de usar el ID correcto de la planta (ver `/plantas`)
2. Ejecuta el workflow manualmente para procesar comandos pendientes
3. Los comandos se procesan en la siguiente ejecucion, no en tiempo real

### Error 404 en Telegram
El token o chat_id tienen espacios o caracteres incorrectos. Verifica los secretos en GitHub.

## Licencia

Uso personal.
