# Registro asistido con el correo de A.D.A

Abre Gumroad, Ko-fi, Etsy o Stripe y **rellena automáticamente** el correo y la contraseña desde `.env`. Las credenciales son **siempre** `ADA_EMAIL` y `ADA_EMAIL_PASSWORD` (no existe `GUMROAD_CREDENTIALS`; Ollama es el modelo de IA local y no se conecta a Gumroad).

## Requisitos

- Python 3.9+
- En la **raíz del proyecto ADA** un archivo `.env` con:
  - `ADA_EMAIL=tu-correo@gmail.com`
  - `ADA_EMAIL_PASSWORD=...`

## Uso

**Recomendado (todo en uno, venv con Playwright ya configurado):**

```bash
cd /ruta/a/ADA
# Entrar a tu cuenta de Gumroad ya creada (rellena email y contraseña)
./signup-helper/run.sh gumroad_login

# Registro nuevo en Gumroad
./signup-helper/run.sh gumroad
# Otras: ./signup-helper/run.sh kofi  |  etsy  |  stripe
```

Se abrirá el navegador con el correo y la contraseña ya rellenados desde `.env`. Completa CAPTCHA o verificación si aparece.

**Sin run.sh** (si no usas el venv): desde la raíz del proyecto, `pip install -r signup-helper/requirements.txt`, `playwright install chromium`, y luego `python3 signup-helper/register.py gumroad`.

## Abrir el enlace de verificación del correo (opcional)

Si la plataforma envía un correo de verificación a ada@nortcoding.com, puedes hacer que el script lo lea por IMAP y abra el enlace:

1. En `.env` añade (datos de tu servidor de correo, ej. cPanel):
   ```env
   ADA_IMAP_HOST=s422.nyc7.mysecurecloudhost.com
   ADA_IMAP_PORT=993
   ADA_IMAP_USE_SSL=true
   ```
2. Después de registrarte, ejecuta:
   ```bash
   ./signup-helper/run.sh --open-verification
   ```

Si IMAP no está configurado, revisa el correo en el webmail y haz clic en el enlace manualmente.
