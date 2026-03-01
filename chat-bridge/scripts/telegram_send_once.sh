#!/bin/bash
# Envía mensaje de prueba a Telegram. Usa .env del proyecto (raíz ADA).
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ENV="$ROOT/.env"
if [ ! -f "$ENV" ]; then
  echo "No existe $ENV"
  exit 1
fi
# Cargar solo variables TELEGRAM_ sin imprimir
while IFS= read -r line; do
  case "$line" in
    TELEGRAM_BOT_TOKEN=*) export TELEGRAM_BOT_TOKEN="${line#TELEGRAM_BOT_TOKEN=}";;
    TELEGRAM_CHAT_ID=*)   export TELEGRAM_CHAT_ID="${line#TELEGRAM_CHAT_ID=}";;
  esac
done < "$ENV"
# Permitir pasar chat_id por argumento: ./telegram_send_once.sh 123456789
[ -n "$1" ] && [[ "$1" =~ ^[0-9-]+$ ]] && TELEGRAM_CHAT_ID="$1"
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
  echo "Falta TELEGRAM_BOT_TOKEN en .env (obtén el token en @BotFather)"
  exit 1
fi
cd "$ROOT"
# Obtener chat_id si no está definido
if [ -z "$TELEGRAM_CHAT_ID" ]; then
  echo "Obteniendo chat_id (quienes han escrito al bot)..."
  docker compose --profile extended --profile telegram run --rm \
    -e TELEGRAM_BOT_TOKEN \
    chat-bridge python -c "
import os, httpx
r = httpx.get('https://api.telegram.org/bot%s/getUpdates' % os.getenv('TELEGRAM_BOT_TOKEN'), timeout=10)
d = r.json()
if not d.get('ok'):
    print('Error:', d)
    exit(1)
for u in d.get('result', [])[-15:]:
    m = u.get('message') or {}
    c = m.get('chat', {})
    print('  chat_id=%s  @%s  %s' % (c.get('id'), c.get('username',''), c.get('first_name','')))
if not d.get('result'):
    print('Nadie ha escrito al bot. Abre el bot con tu número +573228610411 y envía /start.')
"
  echo ""
  echo "Copia un chat_id y ejecuta: TELEGRAM_CHAT_ID=ese_numero $0"
  exit 0
fi
echo "Enviando mensaje de prueba a chat_id=$TELEGRAM_CHAT_ID ..."
docker compose --profile extended --profile telegram run --rm \
  -e TELEGRAM_BOT_TOKEN -e TELEGRAM_CHAT_ID \
  chat-bridge python -c "
import os, httpx
t = os.getenv('TELEGRAM_BOT_TOKEN')
cid = os.getenv('TELEGRAM_CHAT_ID')
text = 'Hola, mensaje de prueba desde ADA. (Tu número +573228610411)'
r = httpx.post('https://api.telegram.org/bot%s/sendMessage' % t, json={'chat_id': cid, 'text': text}, timeout=10)
d = r.json()
if d.get('ok'):
    print('Enviado correctamente a', cid)
else:
    print('Error:', d.get('description', d))
    exit(1)
"
echo "Listo."
