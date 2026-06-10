# gmail_auth.py
"""
Gmail OAuth2 kimlik doğrulama modülü.
Kullanıcı tarayıcıda Google hesabına giriş yapar, token yerel olarak saklanır.
Bir sonraki kullanımda tekrar giriş gerekmez.
"""

import os
import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

TOKEN_FILE       = "gmail_token.json"
CREDENTIALS_FILE = "credentials.json"

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def _get_credentials():
    """
    Mevcut token'ı yükler ya da OAuth akışını başlatarak tarayıcıda
    kullanıcının Google hesabına giriş yapmasını sağlar.
    """
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None

    # Kayıtlı token varsa yükle
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Token yok ya da süresi dolmuşsa
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(CREDENTIALS_FILE)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            # Tarayıcı açılır, kullanıcı Google hesabına giriş yapar
            creds = flow.run_local_server(port=0, open_browser=True)

        # Token'ı kaydet (bir sonraki çalıştırmada tekrar giriş gerekmez)
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return creds


def send_via_gmail_api(subject: str, body: str, recipients: list[str]) -> tuple[bool, str]:
    """
    Gmail API üzerinden mail gönderir.
    İlk çalıştırmada tarayıcı açılır.
    Returns: (success: bool, message: str)
    """
    try:
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError

        creds   = _get_credentials()
        service = build("gmail", "v1", credentials=creds)

        sent = 0
        errors = []
        for to_addr in recipients:
            try:
                mime = MIMEMultipart("alternative")
                mime["Subject"] = subject
                mime["To"]      = to_addr
                mime.attach(MIMEText(body, "plain", "utf-8"))

                raw = base64.urlsafe_b64encode(mime.as_bytes()).decode("utf-8")
                service.users().messages().send(
                    userId="me",
                    body={"raw": raw}
                ).execute()
                sent += 1
            except HttpError as e:
                errors.append(f"{to_addr}: {e}")

        if sent == len(recipients):
            return True, f"{sent} mail başarıyla gönderildi."
        elif sent > 0:
            return True, f"{sent}/{len(recipients)} mail gönderildi. Hatalar: {'; '.join(errors)}"
        else:
            return False, "Hiçbir mail gönderilemedi: " + "; ".join(errors)

    except FileNotFoundError:
        return False, "CREDENTIALS_NOT_FOUND"
    except Exception as e:
        return False, f"Gmail API hatası: {e}"


def revoke_token():
    """Kayıtlı token'ı siler (hesap değiştirmek için)."""
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
        return True
    return False


def get_logged_in_email() -> str | None:
    """Token varsa hangi hesap giriş yapmış, döndürür."""
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        with open(TOKEN_FILE, encoding="utf-8") as f:
            data = json.load(f)
        # token dosyasında e-posta bilgisi yok, API ile al
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        return profile.get("emailAddress")
    except Exception:
        return None
