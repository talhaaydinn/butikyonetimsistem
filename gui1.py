from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
    QListWidget, QVBoxLayout, QHBoxLayout, QComboBox, QFrame,
    QInputDialog, QMessageBox, QStackedWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QDialog,
    QFormLayout, QCheckBox, QFileDialog, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPalette, QColor, QFont, QBrush

from functions import (
    load_customers, add_customer, delete_customer,
    add_purchase, view_purchases, customer_dict,
    send_bulk_email_to_list, get_top_spenders, search_customers
)
from database import c


# ══════════════════════════════════════════════════════════════════════════════
# YARDIMCI: Kapatılabilir bilgi diyaloğu
# ══════════════════════════════════════════════════════════════════════════════
def info_dialog(parent, title, text, ok_label="Tamam", color="#7DEFA0", bg="#0D0D1A"):
    """Çarpı + OK butonu olan, temalı bilgi diyaloğu."""
    d = QDialog(parent)
    d.setWindowTitle(title)
    d.setMinimumWidth(380)
    d.setStyleSheet(f"""
        QDialog   {{ background:{bg}; }}
        QLabel    {{ color:{color}; font-size:13px; }}
        QPushButton {{
            background:#1A4230; color:#7DEFA0;
            border:1px solid #2A6A45; border-radius:8px;
            padding:8px 24px; font-size:13px; font-weight:bold;
        }}
        QPushButton:hover {{ background:#265A40; }}
    """)
    lay = QVBoxLayout(d)
    lay.setContentsMargins(24, 24, 24, 24)
    lay.setSpacing(16)
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lay.addWidget(lbl)
    btn = QPushButton(ok_label)
    btn.clicked.connect(d.accept)
    btn.setFixedHeight(40)
    lay.addWidget(btn, alignment=Qt.AlignRight)
    d.exec_()


def warn_dialog(parent, title, text):
    info_dialog(parent, title, text, color="#FFA0B0", bg="#0D0D1A")


# ══════════════════════════════════════════════════════════════════════════════
# MESAJ GİRİŞ DİYALOĞU
# ══════════════════════════════════════════════════════════════════════════════
class BodyDialog(QDialog):
    def __init__(self, parent=None, default=""):
        super().__init__(parent)
        self.setWindowTitle("Mesaj İçeriği")
        self.setMinimumWidth(500)
        self.setStyleSheet("""
            QDialog   { background:#0D0D1A; }
            QLabel    { color:#A0A0C8; font-size:13px; }
            QTextEdit {
                background:#13131F; color:#E0E0F0;
                border:1px solid #2A2A45; border-radius:8px;
                padding:8px; font-size:13px;
            }
            QPushButton {
                background:#3A3AA0; color:white;
                border:1px solid #5A5AC0; border-radius:8px;
                padding:9px 22px; font-size:13px; font-weight:bold;
            }
            QPushButton:hover { background:#5050C0; }
            QPushButton#cancel_btn {
                background:#1E1E30; color:#7070A0; border-color:#30305A;
            }
            QPushButton#cancel_btn:hover { background:#282838; }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 22, 22, 22)
        lay.setSpacing(12)
        lay.addWidget(QLabel("Mesaj İçeriği:"))
        self._edit = QTextEdit()
        self._edit.setMinimumHeight(180)
        self._edit.setPlainText(default)
        lay.addWidget(self._edit)
        row = QHBoxLayout()
        row.setSpacing(8)
        cancel = QPushButton("İptal")
        cancel.setObjectName("cancel_btn")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Devam Et →")
        ok.clicked.connect(self.accept)
        row.addWidget(cancel)
        row.addStretch()
        row.addWidget(ok)
        lay.addLayout(row)

    def get_text(self):
        return self._edit.toPlainText()


# ══════════════════════════════════════════════════════════════════════════════
# CREDENTIALS KURULUM DİYALOĞU
# ══════════════════════════════════════════════════════════════════════════════
class CredentialsSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gmail API Kurulumu")
        self.setFixedWidth(560)
        self.setStyleSheet("""
            QDialog { background:#0D0D1A; }
            QLabel  { color:#C0C0E0; font-size:13px; }
            QPushButton {
                border-radius:8px; padding:9px 18px;
                font-size:13px; font-weight:bold;
            }
            QPushButton#ok_btn {
                background:#3A3AA0; color:white; border:1px solid #5A5AC0;
            }
            QPushButton#ok_btn:hover { background:#5050C0; }
            QPushButton#pick_btn {
                background:#1A3A1A; color:#90EE90; border:1px solid #2A6A2A;
            }
            QPushButton#pick_btn:hover { background:#265A26; }
            QPushButton#cancel_btn {
                background:#1E1E30; color:#8080A0; border:1px solid #30305A;
            }
            QPushButton#cancel_btn:hover { background:#28283A; }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 28, 28, 28)
        lay.setSpacing(14)

        title = QLabel("Gmail API Kurulumu  —  Bir Kerelik")
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet("color:#9090FF;")
        lay.addWidget(title)

        intro = QLabel(
            "Uygulama, tarayıcı üzerinden Gmail hesabına güvenli bağlanır.\n"
            "Şifreniz hiçbir yere kaydedilmez. Bir kez kurulum yeterlidir:"
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color:#7070A0; font-size:12px;")
        lay.addWidget(intro)

        box = QFrame()
        box.setStyleSheet("QFrame{background:#12122A; border:1px solid #2A2A50; border-radius:10px;}")
        bl = QVBoxLayout(box)
        bl.setContentsMargins(14, 12, 14, 12)
        bl.setSpacing(7)
        steps = [
            ("1", "console.cloud.google.com adresine gidin"),
            ("2", "Yeni proje oluşturun  (örn. 'Butik CRM')"),
            ("3", "APIs & Services → Library → 'Gmail API' → Enable"),
            ("4", "OAuth consent screen → External → App name → Save\n"
                  "   Test Users bölümüne kendi Gmail adresinizi ekleyin"),
            ("5", "Credentials → Create Credentials → OAuth client ID\n"
                  "   → Desktop app → Create → JSON İndir"),
            ("6", "İndirilen credentials.json dosyasını aşağıdan seçin"),
        ]
        for num, text in steps:
            r = QHBoxLayout()
            nl = QLabel(num)
            nl.setFixedSize(20, 20)
            nl.setAlignment(Qt.AlignCenter)
            nl.setStyleSheet(
                "background:#3A3A8A; color:white; border-radius:10px;"
                "font-size:11px; font-weight:bold; border:none;"
            )
            tl = QLabel(text)
            tl.setStyleSheet("color:#A0A0C8; font-size:12px; border:none;")
            tl.setWordWrap(True)
            r.addWidget(nl)
            r.addSpacing(8)
            r.addWidget(tl, 1)
            bl.addLayout(r)
        lay.addWidget(box)

        fr = QHBoxLayout()
        self._path_lbl = QLabel("Dosya seçilmedi")
        self._path_lbl.setStyleSheet("color:#50507A; font-size:12px; font-style:italic;")
        pick = QPushButton("📂  credentials.json Seç")
        pick.setObjectName("pick_btn")
        pick.setFixedHeight(36)
        pick.clicked.connect(self._pick)
        fr.addWidget(pick)
        fr.addWidget(self._path_lbl, 1)
        lay.addLayout(fr)

        br = QHBoxLayout()
        br.setSpacing(10)
        cancel = QPushButton("İptal")
        cancel.setObjectName("cancel_btn")
        cancel.setFixedHeight(40)
        cancel.clicked.connect(self.reject)
        self._ok = QPushButton("Tarayıcıda Giriş Yap →")
        self._ok.setObjectName("ok_btn")
        self._ok.setFixedHeight(40)
        self._ok.setEnabled(False)
        self._ok.clicked.connect(self.accept)
        br.addWidget(cancel)
        br.addStretch()
        br.addWidget(self._ok)
        lay.addLayout(br)

    def _pick(self):
        path, _ = QFileDialog.getOpenFileName(self, "credentials.json Seç", "", "JSON (*.json)")
        if path:
            import shutil, os
            dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
            shutil.copy(path, dest)
            self._path_lbl.setText("✅  " + os.path.basename(path))
            self._path_lbl.setStyleSheet("color:#7DEFA0; font-size:12px; border:none;")
            self._ok.setEnabled(True)


# ══════════════════════════════════════════════════════════════════════════════
# OAUTH WORKER — token al (tarayıcı açılır)
# ══════════════════════════════════════════════════════════════════════════════
class AuthWorker(QThread):
    done = pyqtSignal(bool, str)   # (success, email_or_error)

    def run(self):
        try:
            from gmail_auth import _get_credentials
            _get_credentials()
            # E-postayı al
            from gmail_auth import get_logged_in_email
            email = get_logged_in_email() or "Bilinmiyor"
            self.done.emit(True, email)
        except Exception as e:
            self.done.emit(False, str(e))


# ══════════════════════════════════════════════════════════════════════════════
# MAIL GÖNDERIM WORKER
# ══════════════════════════════════════════════════════════════════════════════
class EmailWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, subject, body, recipients):
        super().__init__()
        self.subject    = subject
        self.body       = body
        self.recipients = recipients

    def run(self):
        ok, msg = send_bulk_email_to_list(self.subject, self.body, self.recipients)
        self.finished.emit(ok, msg)


# ══════════════════════════════════════════════════════════════════════════════
# İLERLEME DİYALOĞU — çarpıyla kapatılabilir
# ══════════════════════════════════════════════════════════════════════════════
class ProgressDialog(QDialog):
    def __init__(self, parent, title, text):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(420)
        # Çarpı butonunu göster ama "in-progress" modunda ignore et
        self.setWindowFlags(self.windowFlags() | Qt.WindowCloseButtonHint)
        self._allow_close = False
        self.setStyleSheet("""
            QDialog { background:#0D0D1A; }
            QLabel  { color:#C0C0E0; font-size:13px; }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 28, 28, 28)
        lay.setSpacing(12)
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lay.addWidget(lbl)

    def allow_close(self):
        self._allow_close = True

    def closeEvent(self, event):
        if self._allow_close:
            event.accept()
        else:
            # İşlem sürüyor, arka plana al ama kapatma
            event.ignore()
            self.hide()


# ══════════════════════════════════════════════════════════════════════════════
# ANA PENCERE
# ══════════════════════════════════════════════════════════════════════════════
class BoutiqueApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Butik CRM")
        self.setGeometry(80, 60, 1500, 920)
        self._set_palette()
        self._apply_global_styles()

        root = QWidget()
        self.setCentralWidget(root)
        rl = QHBoxLayout(root)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)
        rl.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        rl.addWidget(self.stack)

        self._build_all_pages()
        self._set_active(0)

    # ── tema ──────────────────────────────────────────────────────────────────
    def _set_palette(self):
        p = QPalette()
        p.setColor(QPalette.Window,          QColor("#0B0B14"))
        p.setColor(QPalette.WindowText,      QColor("#E0E0F0"))
        p.setColor(QPalette.Base,            QColor("#13131F"))
        p.setColor(QPalette.AlternateBase,   QColor("#0F0F1A"))
        p.setColor(QPalette.Text,            QColor("#E0E0F0"))
        p.setColor(QPalette.Button,          QColor("#1E1E38"))
        p.setColor(QPalette.ButtonText,      QColor("#FFFFFF"))
        p.setColor(QPalette.Highlight,       QColor("#4040AA"))
        p.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        self.setPalette(p)

    def _apply_global_styles(self):
        self.setStyleSheet("""
            * { font-family: 'Segoe UI', Arial, sans-serif; }
            QMainWindow, QWidget { background-color: #0B0B14; }
            QLabel { color: #C8C8E8; font-size: 13px; }

            QLineEdit, QTextEdit, QComboBox {
                background-color: #13131F; color: #E0E0F0;
                border: 1px solid #2A2A45; border-radius: 8px;
                padding: 7px 12px; font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #5A5ABA; background-color: #16162A;
            }
            QComboBox::drop-down { border: none; width: 28px; }
            QComboBox QAbstractItemView {
                background:#1A1A2E; color:#E0E0F0;
                border:1px solid #3A3A6A;
                selection-background-color:#3A3A7A;
            }

            QTableWidget {
                background-color: #0F0F1A; color: #D0D0EE;
                border: none; gridline-color: #1E1E32;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 6px 10px; border-bottom: 1px solid #1A1A2E;
            }
            QTableWidget::item:hover    { background-color: #1E1E38; }
            QTableWidget::item:selected { background-color: #2A2A55; color:#FFF; }
            QHeaderView::section {
                background-color: #13131F; color: #7070B0;
                border: none; border-bottom: 2px solid #2A2A45;
                padding: 8px 10px; font-weight: bold; font-size: 12px;
            }

            QListWidget {
                background-color: #13131F; border: 1px solid #2A2A45;
                border-radius: 10px; color: #D0D0EE;
                font-size: 13px; outline: none; padding: 4px;
            }
            QListWidget::item { padding: 9px 12px; border-radius: 6px; margin: 1px 4px; }
            QListWidget::item:selected { background-color: #2E2E60; color: #FFF; }
            QListWidget::item:hover    { background-color: #1A1A30; }

            QPushButton {
                background-color: #1E1E3A; color: #A0A0D8;
                border: 1px solid #3A3A6A; padding: 9px 18px;
                border-radius: 8px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover   { background-color:#2A2A50; color:#FFF; border-color:#6060C0; }
            QPushButton:pressed { background-color:#18183A; }

            QPushButton#btn_primary  { background:#3A3AA0; color:white; border-color:#5A5AC0; }
            QPushButton#btn_primary:hover  { background:#4A4AB8; border-color:#8080E0; }
            QPushButton#btn_success  { background:#1A4230; color:#7DEFA0; border-color:#2A6A45; }
            QPushButton#btn_success:hover  { background:#265A40; border-color:#3A9060; }
            QPushButton#btn_danger   { background:#4A1520; color:#FFA0B0; border-color:#7A2535; }
            QPushButton#btn_danger:hover   { background:#6A1E2E; border-color:#B03050; }
            QPushButton#btn_gold     { background:#3A2A00; color:#FFD060; border-color:#6A5000; }
            QPushButton#btn_gold:hover     { background:#503A00; border-color:#9A7800; }

            QScrollBar:vertical {
                background:#0B0B14; width:7px; border-radius:4px; margin:0;
            }
            QScrollBar::handle:vertical {
                background:#2E2E5A; border-radius:4px; min-height:30px;
            }
            QScrollBar::handle:vertical:hover { background:#4A4A8A; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
            QScrollBar:horizontal { background:#0B0B14; height:7px; border-radius:4px; }
            QScrollBar::handle:horizontal { background:#2E2E5A; border-radius:4px; }
        """)

    # ── sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        sb = QFrame()
        sb.setFixedWidth(230)
        sb.setStyleSheet("QFrame{background:#07070F; border-right:1px solid #16162A;}")
        lay = QVBoxLayout(sb)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        wrap = QFrame()
        wrap.setStyleSheet("background:transparent; border:none;")
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(22, 30, 22, 22)
        wl.setSpacing(3)
        b = QLabel("BUTIK CRM")
        b.setFont(QFont("Segoe UI", 16, QFont.Bold))
        b.setStyleSheet("color:#7070FF; letter-spacing:2px; border:none;")
        s = QLabel("Müşteri Yönetim Sistemi")
        s.setStyleSheet("color:#30305A; font-size:10px; border:none;")
        wl.addWidget(b)
        wl.addWidget(s)
        lay.addWidget(wrap)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background:#16162A; border:none; margin:0 18px;")
        sep.setFixedHeight(1)
        lay.addWidget(sep)
        lay.addSpacing(10)

        self._nav_btns = []
        for txt, idx in [
            ("  📊  Dashboard",   0),
            ("  👥  Müşteriler",  1),
            ("  🛒  Alışveriş",   2),
            ("  📨  Mail Gönder", 3),
        ]:
            btn = QPushButton(txt)
            btn.setCheckable(True)
            btn.setFixedHeight(46)
            btn.setStyleSheet("""
                QPushButton {
                    background:transparent; border:none; border-radius:0;
                    text-align:left; padding-left:18px;
                    color:#50507A; font-size:14px;
                }
                QPushButton:hover   { background:#0F0F1E; color:#B0B0FF; border-left:3px solid #3A3A80; }
                QPushButton:checked { background:#14142A; color:#FFF; border-left:3px solid #6A6AFF; font-weight:bold; }
            """)
            btn.clicked.connect(lambda _, i=idx: self._set_active(i))
            lay.addWidget(btn)
            self._nav_btns.append(btn)

        lay.addStretch()
        v = QLabel("v3.0  •  CRM")
        v.setStyleSheet("color:#1E1E38; font-size:10px; padding:16px 20px; border:none;")
        lay.addWidget(v)
        return sb

    def _set_active(self, idx):
        self.stack.setCurrentIndex(idx)
        for i, b in enumerate(self._nav_btns):
            b.setChecked(i == idx)
        if idx == 0:
            self.refresh_dashboard()

    # ── sayfa oluştur ─────────────────────────────────────────────────────────
    def _build_all_pages(self):
        self.stack.addWidget(self._page_dashboard())
        self.stack.addWidget(self._page_customers())
        self.stack.addWidget(self._page_purchase())
        self.stack.addWidget(self._page_mail())
        self._nav_btns[0].setChecked(True)

    # ── yardımcılar ───────────────────────────────────────────────────────────
    @staticmethod
    def _card(r=14):
        f = QFrame()
        f.setStyleSheet(f"QFrame{{background:#0F0F1A; border:1px solid #1E1E35; border-radius:{r}px;}}")
        return f

    @staticmethod
    def _sec_title(t):
        l = QLabel(t)
        l.setFont(QFont("Segoe UI", 14, QFont.Bold))
        l.setStyleSheet("color:#B0B0FF; background:transparent; border:none;")
        return l

    @staticmethod
    def _flabel(t):
        l = QLabel(t)
        l.setStyleSheet("color:#606090; font-size:11px; font-weight:bold; background:transparent; border:none;")
        return l

    @staticmethod
    def _inp(ph="", h=40):
        w = QLineEdit()
        w.setPlaceholderText(ph)
        w.setFixedHeight(h)
        return w

    # ══════════════════════════════════════════════════════════════════════════
    # DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    def _page_dashboard(self):
        page = QWidget()
        page.setStyleSheet("background:#0B0B14;")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(32, 28, 32, 28)
        outer.setSpacing(20)

        # başlık + arama
        hrow = QHBoxLayout()
        ttl = QLabel("Dashboard")
        ttl.setFont(QFont("Segoe UI", 22, QFont.Bold))
        ttl.setStyleSheet("color:#FFF;")
        hrow.addWidget(ttl)
        hrow.addStretch()
        self._dash_search = self._inp("  🔍  Ad, telefon veya e-posta ile ara...", 40)
        self._dash_search.setFixedWidth(320)
        self._dash_search.textChanged.connect(self._on_dash_search)
        hrow.addWidget(self._dash_search)
        outer.addLayout(hrow)

        # arama sonuç
        self._sr_frame = self._card()
        srl = QVBoxLayout(self._sr_frame)
        srl.setContentsMargins(14, 12, 14, 12)
        srl.setSpacing(6)
        sl = QLabel("Arama Sonuçları")
        sl.setStyleSheet("color:#8080C0; font-size:12px; font-weight:bold; background:transparent; border:none;")
        srl.addWidget(sl)
        self._sr_table = self._cust_table(["Ad Soyad", "Telefon", "E-Posta", "Kayıt Tarihi"])
        self._sr_table.setFixedHeight(150)
        srl.addWidget(self._sr_table)
        self._sr_frame.setVisible(False)
        outer.addWidget(self._sr_frame)

        # stat kartları
        srow = QHBoxLayout()
        srow.setSpacing(16)
        self._sc = {}
        cards = [
            ("customers", "Toplam Müşteri",   "0",  "#12122A", "#4848B8", "👥"),
            ("purchases", "Alışveriş Sayısı", "0",  "#0A2018", "#2A8050", "🛒"),
            ("revenue",   "Toplam Ciro",      "₺0", "#251800", "#886010", "💰"),
            ("today",     "Bugün Kayıt",      "0",  "#18082A", "#6A28A0", "📅"),
        ]
        for key, lbl, val, bg, accent, icon in cards:
            self._sc[key] = self._stat_card(lbl, val, bg, accent, icon)
            srow.addWidget(self._sc[key])
        outer.addLayout(srow)

        # içerik
        crow = QHBoxLayout()
        crow.setSpacing(20)

        # top spenders
        tc = self._card()
        tl = QVBoxLayout(tc)
        tl.setContentsMargins(18, 18, 18, 18)
        tl.setSpacing(12)
        th = QHBoxLayout()
        th.addWidget(self._sec_title("🏆  En Çok Harcayan Müşteriler  (Son 3 Ay)"))
        th.addStretch()
        pn = QLabel("son 90 gün")
        pn.setStyleSheet("color:#30306A; font-size:11px; background:transparent; border:none;")
        th.addWidget(pn)
        tl.addLayout(th)
        self._top_table = self._make_top_table()
        tl.addWidget(self._top_table)

        tmr = QHBoxLayout()
        tmr.setSpacing(10)
        sa_btn = QPushButton("Tümünü Seç / Kaldır")
        sa_btn.setObjectName("btn_primary")
        sa_btn.setFixedHeight(34)
        sa_btn.setStyleSheet(sa_btn.styleSheet() + "QPushButton{font-size:12px; padding:4px 12px;}")
        sa_btn.clicked.connect(self._toggle_select_all)
        ml_btn = QPushButton("✉  Seçili Müşterilere İndirim Maili Gönder")
        ml_btn.setObjectName("btn_gold")
        ml_btn.setFixedHeight(40)
        ml_btn.clicked.connect(self._top_mail)
        tmr.addWidget(sa_btn)
        tmr.addStretch()
        tmr.addWidget(ml_btn)
        tl.addLayout(tmr)
        crow.addWidget(tc, 3)

        # son müşteriler
        rc = self._card()
        rl = QVBoxLayout(rc)
        rl.setContentsMargins(18, 18, 18, 18)
        rl.setSpacing(12)
        rl.addWidget(self._sec_title("🕐  Son Eklenen Müşteriler"))
        self._recent_table = self._cust_table(["Ad Soyad", "Telefon", "Kayıt Tarihi"])
        rl.addWidget(self._recent_table)
        crow.addWidget(rc, 2)

        outer.addLayout(crow)
        self.refresh_dashboard()
        return page

    def _make_top_table(self):
        t = QTableWidget(0, 5)
        t.setHorizontalHeaderLabels(["", "Sıra", "Ad Soyad", "E-Posta", "Toplam"])
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed); t.setColumnWidth(0, 36)
        t.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed); t.setColumnWidth(1, 50)
        t.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        t.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        t.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed); t.setColumnWidth(4, 130)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        t.setSelectionMode(QAbstractItemView.NoSelection)
        t.verticalHeader().setVisible(False)
        t.setShowGrid(False)
        t.setAlternatingRowColors(True)
        t.setStyleSheet("QTableWidget{alternate-background-color:#11111E;}")
        return t

    def _cust_table(self, cols):
        t = QTableWidget(0, len(cols))
        t.setHorizontalHeaderLabels(cols)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        t.setSelectionMode(QAbstractItemView.NoSelection)
        t.verticalHeader().setVisible(False)
        t.setShowGrid(False)
        return t

    def _stat_card(self, label, value, bg, accent, icon=""):
        card = QFrame()
        card.setStyleSheet(f"QFrame{{background:{bg}; border:1px solid {accent}; border-radius:14px;}}")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(4)
        il = QLabel(icon)
        il.setFont(QFont("Segoe UI", 22))
        il.setStyleSheet("background:transparent; border:none; color:#FFF;")
        lay.addWidget(il)
        vl = QLabel(value)
        vl.setFont(QFont("Segoe UI", 26, QFont.Bold))
        vl.setStyleSheet("color:#FFF; background:transparent; border:none;")
        vl.setObjectName("sv")
        lay.addWidget(vl)
        tl = QLabel(label)
        tl.setStyleSheet(f"color:{accent}; font-size:11px; background:transparent; border:none;")
        lay.addWidget(tl)
        return card

    def refresh_dashboard(self):
        from datetime import date, timedelta
        try:
            c.execute("SELECT COUNT(*) FROM Customers")
            nc = c.fetchone()[0]
            c.execute("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM Purchases")
            row = c.fetchone(); np_, rev = row[0], row[1]
            c.execute("SELECT COUNT(*) FROM Customers WHERE register_date=?", (str(date.today()),))
            nt = c.fetchone()[0]

            self._sc["customers"].findChild(QLabel, "sv").setText(str(nc))
            self._sc["purchases"].findChild(QLabel, "sv").setText(str(np_))
            self._sc["revenue"].findChild(QLabel, "sv").setText(f"₺{rev:,.0f}")
            self._sc["today"].findChild(QLabel, "sv").setText(str(nt))

            cutoff = str(date.today() - timedelta(days=90))
            self._fill_top(get_top_spenders(cutoff, limit=10))

            c.execute("SELECT name,phone_number,register_date FROM Customers ORDER BY customer_id DESC LIMIT 12")
            self._fill_table(self._recent_table, c.fetchall())
        except Exception as e:
            print("Dashboard hata:", e)

    def _fill_top(self, rows):
        t = self._top_table
        t.setRowCount(0)
        medals = ["🥇", "🥈", "🥉"]
        for rank, (cid, name, email, total) in enumerate(rows, 1):
            r = t.rowCount(); t.insertRow(r)
            chk = QCheckBox()
            chk.setStyleSheet("QCheckBox{margin-left:8px;}")
            chk.setProperty("email", email)
            chk.setProperty("name", name)
            w = QWidget(); wl = QHBoxLayout(w)
            wl.setContentsMargins(4, 0, 0, 0); wl.addWidget(chk)
            w.setStyleSheet("background:transparent;")
            t.setCellWidget(r, 0, w)
            mi = QTableWidgetItem(medals[rank-1] if rank <= 3 else str(rank))
            mi.setTextAlignment(Qt.AlignCenter)
            if rank <= 3: mi.setFont(QFont("Segoe UI", 14))
            t.setItem(r, 1, mi)
            ni = QTableWidgetItem(name)
            if rank == 1: ni.setForeground(QBrush(QColor("#FFD700")))
            t.setItem(r, 2, ni)
            ei = QTableWidgetItem(email if email else "—")
            ei.setForeground(QBrush(QColor("#6060A0")))
            t.setItem(r, 3, ei)
            ai = QTableWidgetItem(f"  ₺{total:,.2f}")
            ai.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            ai.setFont(QFont("Segoe UI", 13, QFont.Bold))
            if rank == 1: ai.setForeground(QBrush(QColor("#FFD700")))
            elif rank <= 3: ai.setForeground(QBrush(QColor("#A0D0FF")))
            t.setItem(r, 4, ai)
            t.setRowHeight(r, 40)

    def _fill_table(self, t, rows):
        t.setRowCount(0)
        for row in rows:
            r = t.rowCount(); t.insertRow(r)
            for col, val in enumerate(row):
                t.setItem(r, col, QTableWidgetItem(str(val) if val else "—"))
            t.setRowHeight(r, 36)

    def _get_chk(self, row):
        w = self._top_table.cellWidget(row, 0)
        return w.findChild(QCheckBox) if w else None

    def _toggle_select_all(self):
        t = self._top_table
        all_on = all(self._get_chk(r).isChecked() for r in range(t.rowCount()) if self._get_chk(r))
        for r in range(t.rowCount()):
            chk = self._get_chk(r)
            if chk: chk.setChecked(not all_on)

    def _top_mail(self):
        sel = []
        for r in range(self._top_table.rowCount()):
            chk = self._get_chk(r)
            if chk and chk.isChecked():
                e = chk.property("email")
                n = chk.property("name")
                if e: sel.append((n, e))
        if not sel:
            warn_dialog(self, "Uyarı", "Lütfen en az bir müşteri seçin.")
            return

        preview = "\n".join(f"  • {n}" for n, _ in sel[:5])
        if len(sel) > 5: preview += f"\n  ... ve {len(sel)-5} kişi daha"

        subject, ok = QInputDialog.getText(
            self, "Mail Konusu",
            f"{len(sel)} müşteriye gönderilecek:\n{preview}\n\nKonu:",
            text="Özel İndirim Fırsatı — Sadece Size!"
        )
        if not ok or not subject.strip(): return

        bdlg = BodyDialog(self, default=(
            "Merhaba,\n\nDeğerli müşterimiz olarak size özel bir indirim fırsatı sunmaktan "
            "büyük mutluluk duyuyoruz.\n\nBu ay tüm alışverişlerinizde %15 indirimden "
            "yararlanabilirsiniz.\n\nİyi alışverişler,\nButik CRM"
        ))
        if bdlg.exec_() != QDialog.Accepted: return
        body = bdlg.get_text()
        if not body.strip(): return

        self._run_send(subject, body, [e for _, e in sel])

    def _on_dash_search(self, text):
        text = text.strip()
        if not text:
            self._sr_frame.setVisible(False)
            return
        self._fill_table(self._sr_table, search_customers(text))
        self._sr_frame.setVisible(True)

    # ══════════════════════════════════════════════════════════════════════════
    # MÜŞTERİLER
    # ══════════════════════════════════════════════════════════════════════════
    def _page_customers(self):
        page = QWidget(); page.setStyleSheet("background:#0B0B14;")
        lay = QHBoxLayout(page)
        lay.setContentsMargins(28, 28, 28, 28); lay.setSpacing(20)

        fc = self._card(); fc.setFixedWidth(340)
        fl = QVBoxLayout(fc); fl.setContentsMargins(22,22,22,22); fl.setSpacing(13)
        fl.addWidget(self._sec_title("Yeni Müşteri Ekle"))
        fl.addWidget(self._flabel("AD SOYAD"))
        self.name_input = self._inp("Müşteri adını girin..."); fl.addWidget(self.name_input)
        fl.addWidget(self._flabel("ÜLKE KODU"))
        self.country_code = QComboBox()
        self.country_code.addItems(["+90  Türkiye","+49  Almanya","+1  ABD","+44  İngiltere","+33  Fransa"])
        self.country_code.setFixedHeight(40); fl.addWidget(self.country_code)
        fl.addWidget(self._flabel("TELEFON"))
        self.phone_input = self._inp("5XX XXX XX XX"); fl.addWidget(self.phone_input)
        fl.addWidget(self._flabel("E-POSTA"))
        self.email_input = self._inp("ornek@email.com"); fl.addWidget(self.email_input)
        fl.addSpacing(6)
        ab = QPushButton("➕  Müşteri Ekle")
        ab.setObjectName("btn_primary"); ab.setFixedHeight(44)
        ab.clicked.connect(self._on_add_customer); fl.addWidget(ab)
        fl.addStretch(); lay.addWidget(fc)

        lc = self._card()
        ll = QVBoxLayout(lc); ll.setContentsMargins(22,22,22,22); ll.setSpacing(12)
        ll.addWidget(self._sec_title("Kayıtlı Müşteriler"))
        self.search_input = self._inp("🔍  İsim, telefon veya e-posta ile ara...")
        self.search_input.textChanged.connect(self.filter_customers); ll.addWidget(self.search_input)
        self.customer_list = QListWidget(); ll.addWidget(self.customer_list)
        br = QHBoxLayout(); br.setSpacing(10)
        vb = QPushButton("🔍  Görüntüle / Güncelle"); vb.setFixedHeight(38)
        vb.clicked.connect(lambda: view_purchases(self.customer_list))
        db = QPushButton("🗑  Sil"); db.setObjectName("btn_danger")
        db.setFixedHeight(38); db.setFixedWidth(90)
        db.clicked.connect(lambda: (delete_customer(self.customer_list), self.refresh_dashboard()))
        br.addWidget(vb); br.addWidget(db); ll.addLayout(br)
        lay.addWidget(lc)

        load_customers(self.customer_list)
        return page

    def filter_customers(self):
        q = self.search_input.text().lower().strip()
        self.customer_list.clear()
        for d in customer_dict:
            if q in d.lower(): self.customer_list.addItem(d)

    def _on_add_customer(self):
        code = self.country_code.currentText().split(" ")[0]
        class _C:
            def currentText(_): return code
        add_customer(self.name_input, self.phone_input, self.email_input, _C(), self.customer_list)
        self.refresh_dashboard()

    # ══════════════════════════════════════════════════════════════════════════
    # ALIŞVERİŞ
    # ══════════════════════════════════════════════════════════════════════════
    def _page_purchase(self):
        page = QWidget(); page.setStyleSheet("background:#0B0B14;")
        lay = QHBoxLayout(page)
        lay.setContentsMargins(28,28,28,28); lay.setSpacing(20)

        fc = self._card(); fc.setFixedWidth(340)
        fl = QVBoxLayout(fc); fl.setContentsMargins(22,22,22,22); fl.setSpacing(13)
        fl.addWidget(self._sec_title("Alışveriş Ekle"))
        info = QLabel("Sağ listeden müşteri seçin,\nardından ürün bilgilerini girin.")
        info.setStyleSheet("color:#40405A; font-size:12px; background:transparent; border:none;")
        fl.addWidget(info)
        fl.addWidget(self._flabel("ÜRÜN ADI"))
        self.product_input = self._inp("Ürün adı..."); fl.addWidget(self.product_input)
        fl.addWidget(self._flabel("TUTAR (₺)"))
        self.amount_input = self._inp("0.00"); fl.addWidget(self.amount_input)
        fl.addSpacing(6)
        sb = QPushButton("💾  Alışverişi Kaydet")
        sb.setObjectName("btn_success"); sb.setFixedHeight(44)
        sb.clicked.connect(self._on_add_purchase); fl.addWidget(sb)
        fl.addStretch(); lay.addWidget(fc)

        lc = self._card()
        ll = QVBoxLayout(lc); ll.setContentsMargins(22,22,22,22); ll.setSpacing(12)
        ll.addWidget(self._sec_title("Müşteri Seç"))
        self._ps = self._inp("🔍  Müşteri ara...")
        self._ps.textChanged.connect(self._filter_purch); ll.addWidget(self._ps)
        self.purchase_customer_list = QListWidget(); ll.addWidget(self.purchase_customer_list)
        lay.addWidget(lc)

        load_customers(self.purchase_customer_list)
        return page

    def _filter_purch(self):
        q = self._ps.text().lower().strip()
        self.purchase_customer_list.clear()
        for d in customer_dict:
            if q in d.lower(): self.purchase_customer_list.addItem(d)

    def _on_add_purchase(self):
        add_purchase(self.product_input, self.amount_input, self.purchase_customer_list)
        self.refresh_dashboard()

    # ══════════════════════════════════════════════════════════════════════════
    # MAİL
    # ══════════════════════════════════════════════════════════════════════════
    def _page_mail(self):
        page = QWidget(); page.setStyleSheet("background:#0B0B14;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(32,28,32,28); lay.setSpacing(20)

        ttl = QLabel("Toplu Mail Gönderimi")
        ttl.setFont(QFont("Segoe UI", 22, QFont.Bold))
        ttl.setStyleSheet("color:#FFF;"); lay.addWidget(ttl)

        # hesap durum kartı
        ac = self._card()
        al = QHBoxLayout(ac); al.setContentsMargins(20,14,20,14); al.setSpacing(14)
        self._acct_icon = QLabel("🔴")
        self._acct_icon.setFont(QFont("Segoe UI", 16))
        self._acct_icon.setStyleSheet("background:transparent; border:none;")
        al.addWidget(self._acct_icon)
        self._acct_lbl = QLabel("Gmail hesabı bağlı değil")
        self._acct_lbl.setStyleSheet("color:#6060A0; font-size:13px; background:transparent; border:none;")
        al.addWidget(self._acct_lbl, 1)
        self._connect_btn = QPushButton("🔗  Gmail'e Bağlan")
        self._connect_btn.setObjectName("btn_primary"); self._connect_btn.setFixedHeight(36)
        self._connect_btn.clicked.connect(self._connect_gmail)
        al.addWidget(self._connect_btn)
        self._logout_btn = QPushButton("Hesabı Kaldır")
        self._logout_btn.setObjectName("btn_danger"); self._logout_btn.setFixedHeight(36)
        self._logout_btn.setVisible(False)
        self._logout_btn.clicked.connect(self._revoke_gmail)
        al.addWidget(self._logout_btn)
        lay.addWidget(ac)
        # Hesap durumunu arka planda yükle (API çağrısı yavaş olabilir)
        self._load_acct_status_async()

        # form
        card = self._card()
        cl = QVBoxLayout(card); cl.setContentsMargins(28,28,28,28); cl.setSpacing(14)
        cl.addWidget(self._flabel("KONU"))
        self.subject_input = self._inp("Mail konusu...", 44); cl.addWidget(self.subject_input)
        cl.addWidget(self._flabel("MESAJ İÇERİĞİ"))
        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText("Mesajınızı buraya yazın...")
        self.body_input.setMinimumHeight(180); cl.addWidget(self.body_input)
        sb = QPushButton("🚀  Tüm Müşterilere Gönder")
        sb.setObjectName("btn_primary"); sb.setFixedHeight(48)
        sb.clicked.connect(self._mail_send_all); cl.addWidget(sb)
        lay.addWidget(card); lay.addStretch()
        return page

    def _refresh_acct_status(self):
        import os, json
        token = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gmail_token.json")

        email = None
        if os.path.exists(token):
            # Önce token dosyasını oku — API çağrısı yapmadan e-postayı bul
            try:
                with open(token, encoding="utf-8") as f:
                    data = json.load(f)
                # google-auth token dosyasında direkt e-posta alanı yok,
                # ama gmail_auth.get_logged_in_email() güvenli şekilde alıyor
                from gmail_auth import get_logged_in_email
                email = get_logged_in_email()
            except Exception:
                pass

        if email:
            self._acct_icon.setText("🟢")
            self._acct_lbl.setText(f"Bağlı:  {email}")
            self._acct_lbl.setStyleSheet(
                "color:#7DEFA0; font-size:13px; background:transparent; border:none;"
            )
            self._connect_btn.setVisible(False)
            self._logout_btn.setVisible(True)
        else:
            # Token var ama geçersiz/okunamıyor, ya da hiç yok
            self._acct_icon.setText("🔴")
            self._acct_lbl.setText("Gmail hesabı bağlı değil")
            self._acct_lbl.setStyleSheet(
                "color:#6060A0; font-size:13px; background:transparent; border:none;"
            )
            self._connect_btn.setVisible(True)
            self._logout_btn.setVisible(False)

    def _connect_gmail(self):
        import os
        creds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
        if not os.path.exists(creds_path):
            dlg = CredentialsSetupDialog(self)
            if dlg.exec_() != QDialog.Accepted:
                return

        # İlerleme diyaloğu — ProgressDialog çarpıyla gizlenebilir ama işlemi durdurmaz
        prog = ProgressDialog(
            self, "Gmail'e Bağlanıyor",
            "🌐  Tarayıcı açılıyor...\n\n"
            "Google hesabınıza giriş yapın ve izin verin.\n"
            "İşlem tamamlandığında bu pencere kapanır."
        )

        worker = AuthWorker()

        def on_done(ok, msg):
            prog.allow_close()
            prog.close()
            QApplication.processEvents()
            if ok:
                # Hesap durumunu ayrı thread'de güncelle (API çağrısı yavaş olabilir)
                self._acct_icon.setText("🟢")
                self._acct_lbl.setText(f"Bağlı:  {msg}")
                self._acct_lbl.setStyleSheet(
                    "color:#7DEFA0; font-size:13px; background:transparent; border:none;"
                )
                self._connect_btn.setVisible(False)
                self._logout_btn.setVisible(True)
                info_dialog(self, "Bağlantı Başarılı",
                            f"✅  {msg} hesabı başarıyla bağlandı.")
            else:
                warn_dialog(self, "Bağlantı Hatası",
                            f"❌  Bağlantı başarısız:\n\n{msg}")

        worker.done.connect(on_done)
        # Worker'ı başlat, SONRA diyaloğu aç (exec_ bloklar ama done sinyali UI loop'ta işlenir)
        worker.start()
        self._auth_worker = worker   # GC'den korunmak için referans tut
        prog.exec_()

    def _load_acct_status_async(self):
        """Token varsa e-postayı arka planda yükle, UI'ı bloklamasın."""
        import os
        token = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gmail_token.json")
        if not os.path.exists(token):
            # Token yok, hemen kırmızı göster
            self._refresh_acct_status()
            return

        # Token var, önce sarı "kontrol ediliyor" göster
        self._acct_icon.setText("🟡")
        self._acct_lbl.setText("Gmail hesabı kontrol ediliyor...")
        self._acct_lbl.setStyleSheet(
            "color:#C0A040; font-size:13px; background:transparent; border:none;"
        )

        class _StatusWorker(QThread):
            result = pyqtSignal(str)  # email ya da ""
            def run(self_w):
                try:
                    from gmail_auth import get_logged_in_email
                    email = get_logged_in_email() or ""
                    self_w.result.emit(email)
                except Exception:
                    self_w.result.emit("")

        w = _StatusWorker()
        def _on_result(email):
            if email:
                self._acct_icon.setText("🟢")
                self._acct_lbl.setText(f"Bağlı:  {email}")
                self._acct_lbl.setStyleSheet(
                    "color:#7DEFA0; font-size:13px; background:transparent; border:none;"
                )
                self._connect_btn.setVisible(False)
                self._logout_btn.setVisible(True)
            else:
                self._refresh_acct_status()

        w.result.connect(_on_result)
        w.start()
        self._status_worker = w  # GC koruması

    def _revoke_gmail(self):
        from gmail_auth import revoke_token
        revoke_token()
        self._refresh_acct_status()
        info_dialog(self, "Hesap Kaldırıldı", "Gmail bağlantısı kaldırıldı.")

    def _mail_send_all(self):
        subject = self.subject_input.text().strip()
        body    = self.body_input.toPlainText().strip()
        if not subject or not body:
            warn_dialog(self, "Eksik", "Konu ve mesaj boş olamaz.")
            return
        c.execute("SELECT email FROM Customers WHERE email IS NOT NULL AND email != ''")
        recs = [r[0] for r in c.fetchall()]
        if not recs:
            info_dialog(self, "Bilgi", "Kayıtlı e-posta adresi bulunamadı.")
            return
        self._run_send(subject, body, recs)

    # ── ortak gönderim ────────────────────────────────────────────────────────
    def _run_send(self, subject, body, recipients):
        import os
        creds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
        token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gmail_token.json")

        if not os.path.exists(creds_path):
            dlg = CredentialsSetupDialog(self)
            if dlg.exec_() != QDialog.Accepted: return
            if os.path.exists(token_path): os.remove(token_path)

        prog = ProgressDialog(
            self, "Gönderiliyor",
            f"📨  {len(recipients)} alıcıya gönderiliyor...\n\n"
            "Token yoksa tarayıcı açılır ve giriş yapmanız istenir.\n"
            "Lütfen bekleyin..."
        )

        worker = EmailWorker(subject, body, recipients)

        def on_done(ok, msg):
            prog.allow_close()
            prog.close()
            QApplication.processEvents()
            if msg == "CREDENTIALS_NOT_FOUND":
                warn_dialog(self, "Hata",
                            "credentials.json bulunamadı.\nÖnce Gmail API kurulumunu tamamlayın.")
                return
            if ok:
                info_dialog(self, "Başarılı", f"✅  {msg}")
            else:
                warn_dialog(self, "Hata", f"❌  {msg}")

        worker.finished.connect(on_done)
        worker.start()
        self._email_worker = worker
        prog.exec_()
