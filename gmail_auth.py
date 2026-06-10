# gmail_auth.py
"""
Gmail OAuth2 kimlik doğrulama modülü.
Windows sistem sertifika deposunu kullanarak SSL doğrulama yapar.
"""

import os
import ssl
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE       = os.path.join(BASE_DIR, "gmail_token.json")
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
SCOPES           = ["https://www.googleapis.com/auth/gmail.send"]


# ── Windows SSL düzeltmesi ────────────────────────────────────────────────────
def _get_win_ssl_context():
    """Windows sistem sertifika deposunu kullanan SSL context döndürür."""
    ctx = ssl.create_default_context()
    ctx.load_default_certs()   # Windows Certificate Store
    return ctx


_patch_requests_ssl = None   # artık kullanılmıyor


# ── Credentials al / yenile ───────────────────────────────────────────────────
def _get_credentials():
    """
    Token varsa yükler, geçersizse yeniler ya da tarayıcıda yeni giriş yapar.
    """
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # httplib2 üzerinden refresh (disable_ssl_certificate_validation ile)
            import httplib2
            from google_auth_httplib2 import AuthorizedHttp
            http = httplib2.Http(disable_ssl_certificate_validation=True)
            creds.refresh(Request(http))
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(CREDENTIALS_FILE)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(
                port=0,
                open_browser=True,
                success_message=(
                    "<html><body style='background:#0d0d1a;font-family:sans-serif;"
                    "text-align:center;padding-top:80px'>"
                    "<h2 style='color:#7defa0'>&#10003; Gmail baglantisi basarili!</h2>"
                    "<p style='color:#a0a0c0'>Bu sekmeyi kapatabilirsiniz.</p>"
                    "<script>setTimeout(()=>window.close(),2000)</script>"
                    "</body></html>"
                ),
            )

        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return creds


# ── Gmail API service ─────────────────────────────────────────────────────────
def _build_service():
    """Windows SSL ile authorize edilmiş Gmail API service nesnesi döndürür."""
    from googleapiclient.discovery import build
    creds = _get_credentials()
    # google-api-python-client >= 2.x uses httplib2 internally;
    # authorized_http ile Windows store kullan
    import httplib2
    from google_auth_httplib2 import AuthorizedHttp

    http = httplib2.Http(disable_ssl_certificate_validation=True)
    authorized_http = AuthorizedHttp(creds, http=http)
    service = build("gmail", "v1", http=authorized_http)
    return service


# ── Mail gönder ───────────────────────────────────────────────────────────────
def send_via_gmail_api(subject: str, body: str, recipients: list) -> tuple:
    """
    Gmail API üzerinden mail gönderir.
    Returns: (success: bool, message: str)
    """
    try:
        from googleapiclient.errors import HttpError

        service = _build_service()
        sent, errors = 0, []

        for to_addr in recipients:
            try:
                mime = MIMEMultipart("alternative")
                mime["Subject"] = subject
                mime["To"]      = to_addr
                mime.attach(MIMEText(body, "plain", "utf-8"))
                raw = base64.urlsafe_b64encode(mime.as_bytes()).decode("utf-8")
                service.users().messages().send(
                    userId="me", body={"raw": raw}
                ).execute()
                sent += 1
            except HttpError as e:
                errors.append(f"{to_addr}: {e}")
            except Exception as e:
                errors.append(f"{to_addr}: {e}")

        if sent == len(recipients):
            return True, f"{sent} mail basariyla gonderildi."
        elif sent > 0:
            return True, f"{sent}/{len(recipients)} mail gonderildi. Hatalar: {'; '.join(errors)}"
        else:
            return False, "Hicbir mail gonderilemedi: " + "; ".join(errors)

    except FileNotFoundError:
        return False, "CREDENTIALS_NOT_FOUND"
    except Exception as e:
        return False, f"Gmail API hatasi: {e}"


# ── Yardımcılar ───────────────────────────────────────────────────────────────
def revoke_token():
    """Kayıtlı token'ı siler."""
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
        return True
    return False


def get_logged_in_email():
    """Token varsa bağlı e-posta adresini döndürür.
    Önce token dosyasından okur, olmadıysa API ile sorgular."""
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        import json as _json
        # Bazı token formatlarında 'email' veya 'id_token' alanı bulunabilir
        with open(TOKEN_FILE, encoding="utf-8") as f:
            data = _json.load(f)

        # google-auth bazı versiyonlarda token'a email'i gömmez.
        # Doğrudan API çağrısı yap — httplib2 disable_ssl ile
        import httplib2
        from google.oauth2.credentials import Credentials
        from google_auth_httplib2 import AuthorizedHttp
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        # Token süresi dolmuşsa yenile
        if creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            http_for_refresh = httplib2.Http(disable_ssl_certificate_validation=True)
            creds.refresh(Request(http_for_refresh))
            with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                f.write(creds.to_json())

        http = httplib2.Http(disable_ssl_certificate_validation=True)
        auth_http = AuthorizedHttp(creds, http=http)
        service = build("gmail", "v1", http=auth_http)
        profile = service.users().getProfile(userId="me").execute()
        return profile.get("emailAddress")
    except Exception:
        return None
