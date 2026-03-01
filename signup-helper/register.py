#!/usr/bin/env python3
"""
Registro asistido para A.D.A: abre la página de signup de una plataforma
y rellena email + contraseña desde variables de entorno.
Uso: python register.py <plataforma>   ej. python register.py gumroad
Requiere: ADA_EMAIL, ADA_EMAIL_PASSWORD en .env o entorno.
Opcional: ADA_IMAP_* para abrir el enlace de verificación por correo.
"""
import os
import re
import sys
import time
import imaplib
import email
from email.header import decode_header

# Cargar .env si existe (raíz del proyecto ADA)
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.isfile(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# Credenciales: siempre desde .env → ADA_EMAIL y ADA_EMAIL_PASSWORD (no hay GUMROAD_CREDENTIALS ni conexión con Ollama).
PLATFORMS = {
    "gumroad": {"url": "https://gumroad.com/signup", "name": "Gumroad (registro)"},
    "gumroad_login": {"url": "https://gumroad.com/login", "name": "Gumroad (iniciar sesión)"},
    "kofi": {"url": "https://ko-fi.com/", "name": "Ko-fi"},
    "etsy": {"url": "https://www.etsy.com/join", "name": "Etsy"},
    "stripe": {"url": "https://dashboard.stripe.com/register", "name": "Stripe"},
}


def get_credentials():
    email_addr = os.getenv("ADA_EMAIL", "").strip()
    password = os.getenv("ADA_EMAIL_PASSWORD", "").strip()
    if not email_addr or not password:
        print("Falta ADA_EMAIL o ADA_EMAIL_PASSWORD en el entorno o .env")
        sys.exit(1)
    return email_addr, password


def fetch_verification_link_from_imap(max_emails=5):
    """Obtiene el primer enlace de verificación/confirmación del buzón (IMAP)."""
    host = os.getenv("ADA_IMAP_HOST", "").strip()
    port = int(os.getenv("ADA_IMAP_PORT", "993"))
    use_ssl = os.getenv("ADA_IMAP_USE_SSL", "true").lower() in ("1", "true", "yes")
    user = os.getenv("ADA_EMAIL", "").strip()
    password = os.getenv("ADA_EMAIL_PASSWORD", "").strip()
    if not host or not user or not password:
        return None
    try:
        if use_ssl:
            M = imaplib.IMAP4_SSL(host, port=port)
        else:
            M = imaplib.IMAP4(host, port=port)
        M.login(user, password)
        M.select("INBOX")
        _, nums = M.search(None, "ALL")
        ids = nums[0].split()
        if not ids:
            M.logout()
            return None
        # Últimos correos primero
        for uid in reversed(ids[-max_emails:]):
            _, data = M.fetch(uid, "(RFC822)")
            raw = data[0][1]
            msg = email.message_from_bytes(raw)
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True)
                        if body:
                            body = body.decode(errors="ignore")
                        break
                    if part.get_content_type() == "text/html" and not body:
                        body = part.get_payload(decode=True)
                        if body:
                            body = body.decode(errors="ignore")
            else:
                body = msg.get_payload(decode=True)
                if body:
                    body = body.decode(errors="ignore")
            if not body:
                continue
            # Buscar enlaces de verificación típicos
            urls = re.findall(r"https?://[^\s<>\"']+(?:verify|confirm|activation|validate|token=[^\s<>\"']+)?", body, re.I)
            for u in urls:
                if any(x in u.lower() for x in ("verify", "confirm", "activation", "token=", "validate")):
                    M.logout()
                    return u
        M.logout()
    except Exception as e:
        print(f"IMAP: {e}")
    return None


def main():
    if len(sys.argv) < 2:
        print("Uso: python register.py <plataforma>   o   python register.py --open-verification")
        print("Plataformas:", ", ".join(PLATFORMS))
        print("  gumroad = registro; gumroad_login = entrar con la cuenta ya creada (rellena email y contraseña desde .env)")
        sys.exit(1)
    if sys.argv[1] == "--open-verification":
        link = fetch_verification_link_from_imap()
        if link:
            print("Abriendo enlace de verificación:", link[:80], "...")
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    b = p.chromium.launch(headless=False)
                    pg = b.new_page()
                    pg.goto(link, timeout=15000)
                    input("Pulsa Enter para cerrar...")
                    b.close()
            except ImportError:
                print("Instala Playwright para abrir el enlace, o ábrelo manualmente:", link)
        else:
            print("No se encontró enlace de verificación. Configura ADA_IMAP_* y revisa el correo.")
        return
    platform = sys.argv[1].lower().strip()
    if platform not in PLATFORMS:
        print(f"Plataforma desconocida: {platform}. Válidas: {list(PLATFORMS)}")
        sys.exit(1)
    email_addr, password = get_credentials()
    info = PLATFORMS[platform]
    url = info["url"]
    print(f"Abriendo {info['name']}: {url}")
    print(f"Email: {email_addr} (contraseña cargada desde env)")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        import webbrowser
        webbrowser.open(url)
        print("(Playwright no instalado. Para rellenar automático: cd signup-helper && ./run.sh gumroad)")
        print("Copia y pega en el formulario:")
        print(f"  Email: {email_addr}")
        print(f"  Contraseña: (la que está en .env → ADA_EMAIL_PASSWORD)")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(1.5)
        # Intentar rellenar campos típicos
        try:
            email_sel = page.query_selector('input[type="email"], input[name*="email"], input[id*="email"], input[placeholder*="mail" i]')
            if email_sel:
                email_sel.fill(email_addr)
                print("Email rellenado.")
            pass_sel = page.query_selector('input[type="password"], input[name*="password"], input[id*="password"]')
            if pass_sel:
                pass_sel.fill(password)
                print("Contraseña rellenada.")
        except Exception as e:
            print("Relleno automático parcial:", e)
        print("Completa CAPTCHA o pasos extra en el navegador si los hay. Cierra el navegador cuando termines.")
        print("Para abrir el enlace de verificación por correo, ejecuta después: python register.py --open-verification")
        try:
            input("Pulsa Enter para cerrar el navegador (o espera y cierra manualmente)...")
        except (EOFError, KeyboardInterrupt):
            pass
        browser.close()


if __name__ == "__main__":
    main()
