from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
    QListWidget, QVBoxLayout, QHBoxLayout, QComboBox, QFrame,
    QInputDialog, QMessageBox, QStackedWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QDialog,
    QFormLayout, QScrollArea, QCheckBox, QSizePolicy, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPalette, QColor, QFont, QBrush

from functions import (
    load_customers, add_customer, delete_customer,
    add_purchase, view_purchases, customer_dict,
    send_bulk_email_to_list, get_top_spenders, search_customers
)
from database import c


# ─── MAIL GÖNDERIM THREAD'İ ───────────────────────────────────────────────────
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


# ─── CREDENTIALS KURULUM DİYALOĞU ────────────────────────────────────────────
class CredentialsSetupDialog(QDialog):
    """
    Kullanıcıya credentials.json nasıl alınır gösterir
    ve dosyayı seçmesini sağlar.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gmail Bağlantısı Kur")
        self.setFixedWidth(560)
        self.setStyleSheet("""
            QDialog   { background-color: #0D0D1A; }
            QLabel    { color: #C0C0E0; font-size: 13px; }
            QPushButton {
                border-radius: 8px; padding: 9px 18px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton#ok_btn {
                background: #3A3AA0; color: white; border: 1px solid #5A5AC0;
            }
            QPushButton#ok_btn:hover { background: #5050C0; }
            QPushButton#pick_btn {
                background: #1A3A1A; color: #90EE90; border: 1px solid #2A6A2A;
            }
            QPushButton#pick_btn:hover { background: #265A26; }
            QPushButton#cancel_btn {
                background: #1E1E30; color: #8080A0; border: 1px solid #30305A;
            }
            QPushButton#cancel_btn:hover { background: #28283A; }
            QFrame#step_box {
                background: #12122A; border: 1px solid #2A2A50;
                border-radius: 10px;
            }
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 28, 28, 28)
        lay.setSpacing(16)

        title = QLabel("Gmail API Kurulumu  —  Bir Kerelik")
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet("color: #9090FF;")
        lay.addWidget(title)

        intro = QLabel(
            "Uygulama, tarayıcı üzerinden Gmail hesabına güvenli şekilde bağlanır.\n"
            "Şifreniz hiçbir yere kaydedilmez. Bunun için bir kez kurulum gerekir:"
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #7070A0; font-size: 12px;")
        lay.addWidget(intro)

        steps_box = QFrame()
        steps_box.setObjectName("step_box")
        steps_lay = QVBoxLayout(steps_box)
        steps_lay.setContentsMargins(16, 14, 16, 14)
        steps_lay.setSpacing(8)

        steps = [
            ("1", "console.cloud.google.com  adresine gidin"),
            ("2", "Yeni proje oluşturun  (örn. 'Butik CRM')"),
            ("3", "Sol menü → APIs & Services → Library\n"
                  "   → 'Gmail API' aratın → Enable"),
            ("4", "APIs & Services → OAuth consent screen\n"
                  "   → External → App name girin → Save"),
            ("5", "Credentials → Create Credentials\n"
                  "   → OAuth client ID → Desktop app → Create"),
            ("6", "İndirilen  credentials.json  dosyasını aşağıdan seçin"),
        ]
        for num, text in steps:
            row = QHBoxLayout()
            num_lbl = QLabel(num)
            num_lbl.setFixedSize(22, 22)
            num_lbl.setAlignment(Qt.AlignCenter)
            num_lbl.setStyleSheet(
                "background:#3A3A8A; color:white; border-radius:11px;"
                "font-size:11px; font-weight:bold;"
            )
            txt_lbl = QLabel(text)
            txt_lbl.setStyleSheet("color:#A0A0C8; font-size:12px;")
            txt_lbl.setWordWrap(True)
            row.addWidget(num_lbl)
            row.addSpacing(8)
            row.addWidget(txt_lbl, 1)
            steps_lay.addLayout(row)

        lay.addWidget(steps_box)

        # Dosya seç
        file_row = QHBoxLayout()
        self._path_lbl = QLabel("Dosya seçilmedi")
        self._path_lbl.setStyleSheet(
            "color:#50507A; font-size:12px; font-style:italic;"
        )
        pick_btn = QPushButton("📂  credentials.json Seç")
        pick_btn.setObjectName("pick_btn")
        pick_btn.setFixedHeight(36)
        pick_btn.clicked.connect(self._pick_file)
        file_row.addWidget(pick_btn)
        file_row.addWidget(self._path_lbl, 1)
        lay.addLayout(file_row)

        # Alt butonlar
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel_btn = QPushButton("İptal")
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.setFixedHeight(40)
        cancel_btn.clicked.connect(self.reject)
        self._ok_btn = QPushButton("Tarayıcıda Giriş Yap →")
        self._ok_btn.setObjectName("ok_btn")
        self._ok_btn.setFixedHeight(40)
        self._ok_btn.setEnabled(False)
        self._ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._ok_btn)
        lay.addLayout(btn_row)

        self._selected_path = None

    def _pick_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "credentials.json Seç", "",
            "JSON Dosyaları (*.json)"
        )
        if path:
            import shutil, os
            # Uygulama klasörüne kopyala
            dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
            shutil.copy(path, dest)
            self._selected_path = dest
            self._path_lbl.setText("✅  " + os.path.basename(path))
            self._path_lbl.setStyleSheet("color:#7DEFA0; font-size:12px;")
            self._ok_btn.setEnabled(True)

    def get_path(self):
        return self._selected_path


# ─── ANA PENCERE ──────────────────────────────────────────────────────────────
class BoutiqueApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Butik CRM")
        self.setGeometry(80, 60, 1500, 920)
        self._set_palette()
        self._apply_global_styles()

        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        root_layout.addWidget(self.stack)

        self._build_all_pages()
        self._set_active(0)

    # ══════════════════════════════════════════════════════════════════════════
    # TEMA / STILLER
    # ══════════════════════════════════════════════════════════════════════════
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

            /* ── Inputs ── */
            QLineEdit, QTextEdit, QComboBox {
                background-color: #13131F;
                color: #E0E0F0;
                border: 1px solid #2A2A45;
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus { border: 1px solid #5A5ABA; background-color: #16162A; }
            QLineEdit::placeholder { color: #40406A; }

            QComboBox::drop-down { border: none; width: 28px; }
            QComboBox QAbstractItemView {
                background-color: #1A1A2E; color: #E0E0F0;
                border: 1px solid #3A3A6A;
                selection-background-color: #3A3A7A;
            }

            /* ── Table ── */
            QTableWidget {
                background-color: #0F0F1A;
                color: #D0D0EE;
                border: none;
                gridline-color: #1E1E32;
                font-size: 13px;
                selection-background-color: #2A2A55;
                selection-color: #FFFFFF;
            }
            QTableWidget::item { padding: 6px 10px; border-bottom: 1px solid #1A1A2E; }
            QTableWidget::item:hover { background-color: #1E1E38; }
            QHeaderView::section {
                background-color: #13131F;
                color: #7070B0;
                border: none;
                border-bottom: 2px solid #2A2A45;
                padding: 8px 10px;
                font-weight: bold;
                font-size: 12px;
            }

            /* ── List ── */
            QListWidget {
                background-color: #13131F;
                border: 1px solid #2A2A45;
                border-radius: 10px;
                color: #D0D0EE;
                font-size: 13px;
                outline: none;
                padding: 4px;
            }
            QListWidget::item { padding: 9px 12px; border-radius: 6px; margin: 1px 4px; }
            QListWidget::item:selected { background-color: #2E2E60; color: #FFFFFF; }
            QListWidget::item:hover    { background-color: #1A1A30; }

            /* ── Buttons ── */
            QPushButton {
                background-color: #1E1E3A;
                color: #A0A0D8;
                border: 1px solid #3A3A6A;
                padding: 9px 18px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover   { background-color: #2A2A50; color: #FFFFFF; border-color: #6060C0; }
            QPushButton:pressed { background-color: #18183A; }

            QPushButton#btn_primary {
                background-color: #3A3AA0; color: white; border-color: #5A5AC0;
            }
            QPushButton#btn_primary:hover { background-color: #4A4AB8; border-color: #8080E0; }

            QPushButton#btn_success {
                background-color: #1A4230; color: #7DEFA0; border-color: #2A6A45;
            }
            QPushButton#btn_success:hover { background-color: #265A40; border-color: #3A9060; color: #AAFFCC; }

            QPushButton#btn_danger {
                background-color: #4A1520; color: #FFA0B0; border-color: #7A2535;
            }
            QPushButton#btn_danger:hover { background-color: #6A1E2E; border-color: #B03050; color: #FFCCCC; }

            QPushButton#btn_gold {
                background-color: #3A2A00; color: #FFD060; border-color: #6A5000;
            }
            QPushButton#btn_gold:hover { background-color: #503A00; border-color: #9A7800; color: #FFE090; }

            /* ── Scrollbars ── */
            QScrollBar:vertical {
                background: #0B0B14; width: 7px; border-radius: 4px; margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #2E2E5A; border-radius: 4px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #4A4A8A; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar:horizontal {
                background: #0B0B14; height: 7px; border-radius: 4px;
            }
            QScrollBar::handle:horizontal { background: #2E2E5A; border-radius: 4px; }
        """)

    # ══════════════════════════════════════════════════════════════════════════
    # SIDEBAR
    # ══════════════════════════════════════════════════════════════════════════
    def _build_sidebar(self):
        sb = QFrame()
        sb.setFixedWidth(230)
        sb.setStyleSheet("QFrame { background-color: #07070F; border-right: 1px solid #16162A; }")
        lay = QVBoxLayout(sb)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Logo bölümü
        logo_wrap = QFrame()
        logo_wrap.setStyleSheet("background: transparent; border: none;")
        logo_lay = QVBoxLayout(logo_wrap)
        logo_lay.setContentsMargins(22, 30, 22, 22)
        logo_lay.setSpacing(3)

        lbl_brand = QLabel("BUTIK CRM")
        lbl_brand.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl_brand.setStyleSheet("color: #7070FF; letter-spacing: 2px; border: none;")
        lbl_sub = QLabel("Müşteri Yönetim Sistemi")
        lbl_sub.setStyleSheet("color: #30305A; font-size: 10px; border: none;")
        logo_lay.addWidget(lbl_brand)
        logo_lay.addWidget(lbl_sub)
        lay.addWidget(logo_wrap)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background:#16162A; border:none; margin: 0 18px;")
        sep.setFixedHeight(1)
        lay.addWidget(sep)
        lay.addSpacing(10)

        self._nav_btns = []
        items = [
            ("  📊  Dashboard",   0),
            ("  👥  Müşteriler",  1),
            ("  🛒  Alışveriş",   2),
            ("  📨  Mail Gönder", 3),
        ]
        for txt, idx in items:
            btn = QPushButton(txt)
            btn.setCheckable(True)
            btn.setFixedHeight(46)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent; border: none; border-radius: 0;
                    text-align: left; padding-left: 18px;
                    color: #50507A; font-size: 14px;
                }
                QPushButton:hover   { background: #0F0F1E; color: #B0B0FF; border-left: 3px solid #3A3A80; }
                QPushButton:checked { background: #14142A; color: #FFFFFF;  border-left: 3px solid #6A6AFF; font-weight: bold; }
            """)
            btn.clicked.connect(lambda _, i=idx: self._set_active(i))
            lay.addWidget(btn)
            self._nav_btns.append(btn)

        lay.addStretch()
        ver = QLabel("v3.0  •  CRM")
        ver.setStyleSheet("color: #1E1E38; font-size: 10px; padding: 16px 20px; border: none;")
        lay.addWidget(ver)
        return sb

    def _set_active(self, idx):
        self.stack.setCurrentIndex(idx)
        for i, b in enumerate(self._nav_btns):
            b.setChecked(i == idx)
        if idx == 0:
            self.refresh_dashboard()

    # ══════════════════════════════════════════════════════════════════════════
    # SAYFALAR
    # ══════════════════════════════════════════════════════════════════════════
    def _build_all_pages(self):
        self.stack.addWidget(self._page_dashboard())
        self.stack.addWidget(self._page_customers())
        self.stack.addWidget(self._page_purchase())
        self.stack.addWidget(self._page_mail())
        self._nav_btns[0].setChecked(True)

    # ── yardımcı widget fabrikası ─────────────────────────────────────────────
    @staticmethod
    def _card(radius=14):
        f = QFrame()
        f.setStyleSheet(f"""
            QFrame {{
                background-color: #0F0F1A;
                border: 1px solid #1E1E35;
                border-radius: {radius}px;
            }}
        """)
        return f

    @staticmethod
    def _section_title(text):
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 14, QFont.Bold))
        lbl.setStyleSheet("color: #B0B0FF; background: transparent; border: none;")
        return lbl

    @staticmethod
    def _field_label(text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #606090; font-size: 11px; font-weight: bold; background: transparent; border: none;")
        return lbl

    @staticmethod
    def _inp(placeholder="", height=40):
        w = QLineEdit()
        w.setPlaceholderText(placeholder)
        w.setFixedHeight(height)
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

        # ── başlık + arama ───────────────────────────────────────────────────
        header_row = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color:#FFFFFF;")
        header_row.addWidget(title)
        header_row.addStretch()

        self._dash_search = QLineEdit()
        self._dash_search.setPlaceholderText("  🔍  Ad, telefon veya e-posta ile ara...")
        self._dash_search.setFixedWidth(320)
        self._dash_search.setFixedHeight(40)
        self._dash_search.textChanged.connect(self._on_dash_search)
        header_row.addWidget(self._dash_search)
        outer.addLayout(header_row)

        # ── arama sonuç tablosu (başta gizli) ────────────────────────────────
        self._search_result_frame = self._card()
        sr_lay = QVBoxLayout(self._search_result_frame)
        sr_lay.setContentsMargins(16, 14, 16, 14)
        sr_lay.setSpacing(8)
        sr_lbl = QLabel("Arama Sonuçları")
        sr_lbl.setStyleSheet("color:#8080C0; font-size:12px; font-weight:bold; background:transparent; border:none;")
        sr_lay.addWidget(sr_lbl)
        self._search_result_table = self._make_customer_table(["Ad Soyad", "Telefon", "E-Posta", "Kayıt Tarihi"])
        self._search_result_table.setFixedHeight(160)
        sr_lay.addWidget(self._search_result_table)
        self._search_result_frame.setVisible(False)
        outer.addWidget(self._search_result_frame)

        # ── stat kartları ─────────────────────────────────────────────────────
        stat_row = QHBoxLayout()
        stat_row.setSpacing(16)
        self._sc_customers = self._stat_card("Toplam Müşteri",   "0",  "#12122A", "#4848B8", "👥")
        self._sc_purchases = self._stat_card("Alışveriş Sayısı", "0",  "#0A2018", "#2A8050", "🛒")
        self._sc_revenue   = self._stat_card("Toplam Ciro",      "₺0", "#251800", "#886010", "💰")
        self._sc_today     = self._stat_card("Bugün Kayıt",      "0",  "#18082A", "#6A28A0", "📅")
        for sc in [self._sc_customers, self._sc_purchases, self._sc_revenue, self._sc_today]:
            stat_row.addWidget(sc)
        outer.addLayout(stat_row)

        # ── ana içerik: top listesi (sol) + son müşteriler (sağ) ─────────────
        content_row = QHBoxLayout()
        content_row.setSpacing(20)

        # ─ TOP SPENDERS ──────────────────────────────────────────────────────
        top_card = self._card()
        top_lay = QVBoxLayout(top_card)
        top_lay.setContentsMargins(18, 18, 18, 18)
        top_lay.setSpacing(12)

        top_header = QHBoxLayout()
        top_lbl = self._section_title("🏆  En Çok Harcayan Müşteriler  (Son 3 Ay)")
        top_header.addWidget(top_lbl)
        top_header.addStretch()
        period_note = QLabel("son 90 gün")
        period_note.setStyleSheet("color:#30306A; font-size:11px; background:transparent; border:none;")
        top_header.addWidget(period_note)
        top_lay.addLayout(top_header)

        self._top_table = self._make_top_table()
        top_lay.addWidget(self._top_table)

        # seçili kişilere mail gönder butonu
        top_mail_row = QHBoxLayout()
        top_mail_row.setSpacing(10)
        self._sel_all_chk = QPushButton("Tümünü Seç / Kaldır")
        self._sel_all_chk.setFixedHeight(34)
        self._sel_all_chk.setObjectName("btn_primary")
        self._sel_all_chk.setStyleSheet(
            self._sel_all_chk.styleSheet() +
            "QPushButton { font-size:12px; padding: 4px 12px; border-radius:6px; }"
        )
        self._sel_all_chk.clicked.connect(self._toggle_select_all_top)

        self._top_mail_btn = QPushButton("✉  Seçili Müşterilere İndirim Maili Gönder")
        self._top_mail_btn.setObjectName("btn_gold")
        self._top_mail_btn.setFixedHeight(40)
        self._top_mail_btn.clicked.connect(self._send_top_spender_mails)

        top_mail_row.addWidget(self._sel_all_chk)
        top_mail_row.addStretch()
        top_mail_row.addWidget(self._top_mail_btn)
        top_lay.addLayout(top_mail_row)
        content_row.addWidget(top_card, 3)

        # ─ SON MÜŞTERİLER ────────────────────────────────────────────────────
        recent_card = self._card()
        recent_lay = QVBoxLayout(recent_card)
        recent_lay.setContentsMargins(18, 18, 18, 18)
        recent_lay.setSpacing(12)
        recent_lay.addWidget(self._section_title("🕐  Son Eklenen Müşteriler"))

        self._recent_table = self._make_customer_table(
            ["Ad Soyad", "Telefon", "Kayıt Tarihi"]
        )
        recent_lay.addWidget(self._recent_table)
        content_row.addWidget(recent_card, 2)

        outer.addLayout(content_row)
        self.refresh_dashboard()
        return page

    # ── top spenders tablosu ─────────────────────────────────────────────────
    def _make_top_table(self):
        tbl = QTableWidget(0, 5)
        tbl.setHorizontalHeaderLabels(["", "Sıra", "Ad Soyad", "E-Posta", "Toplam Harcama"])
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        tbl.setColumnWidth(0, 36)
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        tbl.setColumnWidth(1, 52)
        tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        tbl.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        tbl.setColumnWidth(4, 140)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setSelectionMode(QAbstractItemView.NoSelection)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        tbl.setAlternatingRowColors(True)
        tbl.setStyleSheet(tbl.styleSheet() + """
            QTableWidget { alternate-background-color: #11111E; }
        """)
        return tbl

    def _make_customer_table(self, columns):
        tbl = QTableWidget(0, len(columns))
        tbl.setHorizontalHeaderLabels(columns)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setSelectionMode(QAbstractItemView.NoSelection)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        return tbl

    # ── stat kart ────────────────────────────────────────────────────────────
    def _stat_card(self, label, value, bg, accent, icon=""):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{ background:{bg}; border:1px solid {accent}; border-radius:14px; }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(4)

        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI", 22))
        icon_lbl.setStyleSheet("background:transparent; border:none; color:#FFFFFF;")
        lay.addWidget(icon_lbl)

        val_lbl = QLabel(value)
        val_lbl.setFont(QFont("Segoe UI", 26, QFont.Bold))
        val_lbl.setStyleSheet("color:#FFFFFF; background:transparent; border:none;")
        val_lbl.setObjectName("stat_value")
        lay.addWidget(val_lbl)

        txt_lbl = QLabel(label)
        txt_lbl.setStyleSheet(f"color:{accent}; font-size:11px; background:transparent; border:none;")
        lay.addWidget(txt_lbl)
        return card

    # ── dashboard yenileme ───────────────────────────────────────────────────
    def refresh_dashboard(self):
        from datetime import date, timedelta
        try:
            c.execute("SELECT COUNT(*) FROM Customers")
            n_cust = c.fetchone()[0]
            c.execute("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM Purchases")
            row = c.fetchone()
            n_purch, revenue = row[0], row[1]
            c.execute("SELECT COUNT(*) FROM Customers WHERE register_date=?", (str(date.today()),))
            n_today = c.fetchone()[0]

            self._sc_customers.findChild(QLabel, "stat_value").setText(str(n_cust))
            self._sc_purchases.findChild(QLabel, "stat_value").setText(str(n_purch))
            self._sc_revenue.findChild(QLabel, "stat_value").setText(f"₺{revenue:,.0f}")
            self._sc_today.findChild(QLabel, "stat_value").setText(str(n_today))

            # top spenders
            cutoff = str(date.today() - timedelta(days=90))
            rows = get_top_spenders(cutoff, limit=10)
            self._fill_top_table(rows)

            # son müşteriler
            c.execute("""
                SELECT name, phone_number, register_date
                FROM Customers ORDER BY customer_id DESC LIMIT 12
            """)
            self._fill_table(self._recent_table, c.fetchall())
        except Exception as e:
            print("Dashboard refresh error:", e)

    def _fill_top_table(self, rows):
        tbl = self._top_table
        tbl.setRowCount(0)
        medals = ["🥇", "🥈", "🥉"]
        for rank, (cust_id, name, email, total) in enumerate(rows, 1):
            r = tbl.rowCount()
            tbl.insertRow(r)

            # checkbox
            chk = QCheckBox()
            chk.setStyleSheet("QCheckBox { margin-left: 8px; }")
            chk_widget = QWidget()
            chk_lay = QHBoxLayout(chk_widget)
            chk_lay.setContentsMargins(4, 0, 0, 0)
            chk_lay.addWidget(chk)
            chk_widget.setStyleSheet("background: transparent;")
            chk.setProperty("customer_email", email)
            chk.setProperty("customer_name", name)
            tbl.setCellWidget(r, 0, chk_widget)

            # sıra
            medal = medals[rank - 1] if rank <= 3 else str(rank)
            rank_item = QTableWidgetItem(medal)
            rank_item.setTextAlignment(Qt.AlignCenter)
            if rank <= 3:
                rank_item.setFont(QFont("Segoe UI", 14))
            tbl.setItem(r, 1, rank_item)

            # ad
            name_item = QTableWidgetItem(name)
            if rank == 1:
                name_item.setForeground(QBrush(QColor("#FFD700")))
            tbl.setItem(r, 2, name_item)

            # email
            email_item = QTableWidgetItem(email if email else "—")
            email_item.setForeground(QBrush(QColor("#6060A0")))
            tbl.setItem(r, 3, email_item)

            # tutar
            amt_item = QTableWidgetItem(f"  ₺{total:,.2f}")
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            amt_item.setFont(QFont("Segoe UI", 13, QFont.Bold))
            if rank == 1:
                amt_item.setForeground(QBrush(QColor("#FFD700")))
            elif rank <= 3:
                amt_item.setForeground(QBrush(QColor("#A0D0FF")))
            tbl.setItem(r, 4, amt_item)

            tbl.setRowHeight(r, 40)

    def _fill_table(self, tbl, rows):
        tbl.setRowCount(0)
        for row in rows:
            r = tbl.rowCount()
            tbl.insertRow(r)
            for col, val in enumerate(row):
                item = QTableWidgetItem(str(val) if val else "—")
                tbl.setItem(r, col, item)
            tbl.setRowHeight(r, 36)

    def _toggle_select_all_top(self):
        tbl = self._top_table
        # Herhangi biri işaretsizse hepsini seç, hepsi seçiliyse kaldır
        all_checked = all(
            self._get_chk(tbl, r).isChecked()
            for r in range(tbl.rowCount())
        )
        for r in range(tbl.rowCount()):
            self._get_chk(tbl, r).setChecked(not all_checked)

    @staticmethod
    def _get_chk(tbl, row):
        w = tbl.cellWidget(row, 0)
        return w.findChild(QCheckBox)

    def _send_top_spender_mails(self):
        tbl = self._top_table
        selected = []
        for r in range(tbl.rowCount()):
            chk = self._get_chk(tbl, r)
            if chk and chk.isChecked():
                email = chk.property("customer_email")
                name  = chk.property("customer_name")
                if email:
                    selected.append((name, email))

        if not selected:
            QMessageBox.warning(self, "Uyarı", "Lütfen en az bir müşteri seçin.")
            return

        names_preview = "\n".join(f"  • {n}" for n, _ in selected[:5])
        if len(selected) > 5:
            names_preview += f"\n  ... ve {len(selected)-5} kişi daha"

        # Konu ve mesaj onayı
        subject, ok1 = QInputDialog.getText(
            self, "Mail Konusu",
            f"Seçili {len(selected)} müşteriye gönderilecek:\n{names_preview}\n\nKonu:",
            text="Özel İndirim Fırsatı — Sadece Size!"
        )
        if not ok1 or not subject.strip():
            return

        body_dlg = _BodyDialog(
            self,
            default=(
                "Merhaba,\n\n"
                "Değerli müşterimiz olarak size özel bir indirim fırsatı sunmaktan "
                "büyük mutluluk duyuyoruz.\n\n"
                "Bu ay tüm alışverişlerinizde %15 indirimden yararlanabilirsiniz.\n\n"
                "İyi alışverişler,\nButik CRM"
            )
        )
        if body_dlg.exec_() != QDialog.Accepted:
            return
        body = body_dlg.get_text()
        if not body.strip():
            return

        recipients = [e for _, e in selected]
        self._run_mail_send(subject, body, recipients)

    # ── dashboard arama ───────────────────────────────────────────────────────
    def _on_dash_search(self, text):
        text = text.strip()
        if not text:
            self._search_result_frame.setVisible(False)
            return
        results = search_customers(text)
        self._fill_table(self._search_result_table, results)
        self._search_result_frame.setVisible(True)

    # ══════════════════════════════════════════════════════════════════════════
    # MÜŞTERİLER SAYFASI
    # ══════════════════════════════════════════════════════════════════════════
    def _page_customers(self):
        page = QWidget()
        page.setStyleSheet("background:#0B0B14;")
        lay = QHBoxLayout(page)
        lay.setContentsMargins(28, 28, 28, 28)
        lay.setSpacing(20)

        # ─ Sol form ──────────────────────────────────────────────────────────
        form_card = self._card()
        form_card.setFixedWidth(340)
        fl = QVBoxLayout(form_card)
        fl.setContentsMargins(22, 22, 22, 22)
        fl.setSpacing(13)

        fl.addWidget(self._section_title("Yeni Müşteri Ekle"))

        fl.addWidget(self._field_label("AD SOYAD"))
        self.name_input = self._inp("Müşteri adını girin...")
        fl.addWidget(self.name_input)

        fl.addWidget(self._field_label("ÜLKE KODU"))
        self.country_code = QComboBox()
        self.country_code.addItems(["+90  Türkiye", "+49  Almanya", "+1  ABD",
                                    "+44  İngiltere", "+33  Fransa", "+31  Hollanda"])
        self.country_code.setFixedHeight(40)
        fl.addWidget(self.country_code)

        fl.addWidget(self._field_label("TELEFON"))
        self.phone_input = self._inp("5XX XXX XX XX")
        fl.addWidget(self.phone_input)

        fl.addWidget(self._field_label("E-POSTA"))
        self.email_input = self._inp("ornek@email.com")
        fl.addWidget(self.email_input)

        fl.addSpacing(6)
        add_btn = QPushButton("➕  Müşteri Ekle")
        add_btn.setObjectName("btn_primary")
        add_btn.setFixedHeight(44)
        add_btn.clicked.connect(self._on_add_customer)
        fl.addWidget(add_btn)
        fl.addStretch()
        lay.addWidget(form_card)

        # ─ Sağ liste ─────────────────────────────────────────────────────────
        list_card = self._card()
        ll = QVBoxLayout(list_card)
        ll.setContentsMargins(22, 22, 22, 22)
        ll.setSpacing(12)

        ll.addWidget(self._section_title("Kayıtlı Müşteriler"))

        self.search_input = self._inp("🔍  İsim, telefon veya e-posta ile ara...")
        self.search_input.textChanged.connect(self.filter_customers)
        ll.addWidget(self.search_input)

        self.customer_list = QListWidget()
        ll.addWidget(self.customer_list)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        view_btn = QPushButton("🔍  Görüntüle / Güncelle")
        view_btn.setFixedHeight(38)
        view_btn.clicked.connect(lambda: view_purchases(self.customer_list))
        del_btn = QPushButton("🗑  Sil")
        del_btn.setObjectName("btn_danger")
        del_btn.setFixedHeight(38)
        del_btn.setFixedWidth(90)
        del_btn.clicked.connect(lambda: (delete_customer(self.customer_list), self.refresh_dashboard()))
        btn_row.addWidget(view_btn)
        btn_row.addWidget(del_btn)
        ll.addLayout(btn_row)

        lay.addWidget(list_card)
        load_customers(self.customer_list)
        return page

    def filter_customers(self):
        q = self.search_input.text().lower().strip()
        self.customer_list.clear()
        for display in customer_dict:
            if q in display.lower():
                self.customer_list.addItem(display)

    def _on_add_customer(self):
        code = self.country_code.currentText().split(" ")[0]

        class _Combo:
            def currentText(_): return code

        add_customer(self.name_input, self.phone_input, self.email_input,
                     _Combo(), self.customer_list)
        self.refresh_dashboard()

    # ══════════════════════════════════════════════════════════════════════════
    # ALIŞVERİŞ SAYFASI
    # ══════════════════════════════════════════════════════════════════════════
    def _page_purchase(self):
        page = QWidget()
        page.setStyleSheet("background:#0B0B14;")
        lay = QHBoxLayout(page)
        lay.setContentsMargins(28, 28, 28, 28)
        lay.setSpacing(20)

        form_card = self._card()
        form_card.setFixedWidth(340)
        fl = QVBoxLayout(form_card)
        fl.setContentsMargins(22, 22, 22, 22)
        fl.setSpacing(13)

        fl.addWidget(self._section_title("Alışveriş Ekle"))
        info = QLabel("Sağ listeden müşteri seçin,\nardından ürün bilgilerini girin.")
        info.setStyleSheet("color:#40405A; font-size:12px; background:transparent; border:none;")
        fl.addWidget(info)

        fl.addWidget(self._field_label("ÜRÜN ADI"))
        self.product_input = self._inp("Ürün adı...")
        fl.addWidget(self.product_input)

        fl.addWidget(self._field_label("TUTAR (₺)"))
        self.amount_input = self._inp("0.00")
        fl.addWidget(self.amount_input)

        fl.addSpacing(6)
        save_btn = QPushButton("💾  Alışverişi Kaydet")
        save_btn.setObjectName("btn_success")
        save_btn.setFixedHeight(44)
        save_btn.clicked.connect(self._on_add_purchase)
        fl.addWidget(save_btn)
        fl.addStretch()
        lay.addWidget(form_card)

        list_card = self._card()
        ll = QVBoxLayout(list_card)
        ll.setContentsMargins(22, 22, 22, 22)
        ll.setSpacing(12)
        ll.addWidget(self._section_title("Müşteri Seç"))

        self._purch_search = self._inp("🔍  Müşteri ara...")
        self._purch_search.textChanged.connect(self._filter_purch_customers)
        ll.addWidget(self._purch_search)

        self.purchase_customer_list = QListWidget()
        ll.addWidget(self.purchase_customer_list)
        lay.addWidget(list_card)

        load_customers(self.purchase_customer_list)
        return page

    def _filter_purch_customers(self):
        q = self._purch_search.text().lower().strip()
        self.purchase_customer_list.clear()
        for display in customer_dict:
            if q in display.lower():
                self.purchase_customer_list.addItem(display)

    def _on_add_purchase(self):
        add_purchase(self.product_input, self.amount_input, self.purchase_customer_list)
        self.refresh_dashboard()

    # ══════════════════════════════════════════════════════════════════════════
    # MAİL SAYFASI
    # ══════════════════════════════════════════════════════════════════════════
    def _page_mail(self):
        page = QWidget()
        page.setStyleSheet("background:#0B0B14;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(20)

        title = QLabel("Toplu Mail Gönderimi")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color:#FFFFFF;")
        lay.addWidget(title)

        # ── Hesap durum kartı ────────────────────────────────────────────────
        acct_card = self._card()
        acct_lay = QHBoxLayout(acct_card)
        acct_lay.setContentsMargins(20, 14, 20, 14)
        acct_lay.setSpacing(14)

        self._acct_icon = QLabel("🔴")
        self._acct_icon.setFont(QFont("Segoe UI", 16))
        self._acct_icon.setStyleSheet("background:transparent; border:none;")
        acct_lay.addWidget(self._acct_icon)

        self._acct_lbl = QLabel("Gmail hesabı bağlı değil")
        self._acct_lbl.setStyleSheet("color:#6060A0; font-size:13px; background:transparent; border:none;")
        acct_lay.addWidget(self._acct_lbl, 1)

        self._connect_btn = QPushButton("🔗  Gmail'e Bağlan")
        self._connect_btn.setObjectName("btn_primary")
        self._connect_btn.setFixedHeight(36)
        self._connect_btn.clicked.connect(self._connect_gmail)
        acct_lay.addWidget(self._connect_btn)

        self._logout_btn = QPushButton("Hesabı Kaldır")
        self._logout_btn.setObjectName("btn_danger")
        self._logout_btn.setFixedHeight(36)
        self._logout_btn.setVisible(False)
        self._logout_btn.clicked.connect(self._revoke_gmail)
        acct_lay.addWidget(self._logout_btn)

        lay.addWidget(acct_card)
        self._refresh_acct_status()

        # ── Mail formu ───────────────────────────────────────────────────────
        card = self._card()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(28, 28, 28, 28)
        cl.setSpacing(14)

        cl.addWidget(self._field_label("KONU"))
        self.subject_input = self._inp("Mail konusu...", height=44)
        cl.addWidget(self.subject_input)

        cl.addWidget(self._field_label("MESAJ İÇERİĞİ"))
        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText("Mesajınızı buraya yazın...")
        self.body_input.setMinimumHeight(180)
        cl.addWidget(self.body_input)

        send_all_btn = QPushButton("🚀  Tüm Müşterilere Gönder")
        send_all_btn.setObjectName("btn_primary")
        send_all_btn.setFixedHeight(48)
        send_all_btn.clicked.connect(self._mail_send_all)
        cl.addWidget(send_all_btn)

        lay.addWidget(card)
        lay.addStretch()
        return page

    def _refresh_acct_status(self):
        import os
        token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gmail_token.json")
        if os.path.exists(token_path):
            try:
                from gmail_auth import get_logged_in_email
                email = get_logged_in_email()
                if email:
                    self._acct_icon.setText("🟢")
                    self._acct_lbl.setText(f"Bağlı hesap:  {email}")
                    self._acct_lbl.setStyleSheet("color:#7DEFA0; font-size:13px; background:transparent; border:none;")
                    self._connect_btn.setVisible(False)
                    self._logout_btn.setVisible(True)
                    return
            except Exception:
                pass
        self._acct_icon.setText("🔴")
        self._acct_lbl.setText("Gmail hesabı bağlı değil")
        self._acct_lbl.setStyleSheet("color:#6060A0; font-size:13px; background:transparent; border:none;")
        self._connect_btn.setVisible(True)
        self._logout_btn.setVisible(False)

    def _connect_gmail(self):
        import os
        creds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
        if not os.path.exists(creds_path):
            setup = CredentialsSetupDialog(self)
            if setup.exec_() != QDialog.Accepted:
                return

        # Token yoksa tarayıcı akışını başlat
        self._send_progress = QMessageBox(self)
        self._send_progress.setWindowTitle("Gmail Bağlanıyor")
        self._send_progress.setText("🌐  Tarayıcı açılıyor...\nGoogle hesabınıza giriş yapın ve izin verin.")
        self._send_progress.setStandardButtons(QMessageBox.NoButton)
        self._send_progress.setStyleSheet("QMessageBox{background:#0D0D1A;} QLabel{color:#C0C0E0;}")
        self._send_progress.show()

        class _AuthWorker(QThread):
            done = pyqtSignal(bool, str)
            def run(self_w):
                try:
                    from gmail_auth import _get_credentials, get_logged_in_email
                    _get_credentials()
                    email = get_logged_in_email() or "Bilinmiyor"
                    self_w.done.emit(True, email)
                except Exception as e:
                    self_w.done.emit(False, str(e))

        self._auth_worker = _AuthWorker()
        def _on_auth_done(ok, msg):
            self._send_progress.close()
            if ok:
                self._refresh_acct_status()
                QMessageBox.information(self, "Bağlandı", f"✅  {msg} hesabı bağlandı.")
            else:
                QMessageBox.critical(self, "Hata", f"❌  {msg}")
        self._auth_worker.done.connect(_on_auth_done)
        self._auth_worker.start()

    def _revoke_gmail(self):
        from gmail_auth import revoke_token
        revoke_token()
        self._refresh_acct_status()
        QMessageBox.information(self, "Hesap Kaldırıldı", "Gmail bağlantısı kaldırıldı.")

    def _mail_send_all(self):
        subject = self.subject_input.text().strip()
        body    = self.body_input.toPlainText().strip()
        if not subject or not body:
            QMessageBox.warning(self, "Eksik", "Konu ve mesaj boş olamaz.")
            return

        c.execute("SELECT email FROM Customers WHERE email IS NOT NULL AND email != ''")
        recipients = [r[0] for r in c.fetchall()]
        if not recipients:
            QMessageBox.information(self, "Bilgi", "Kayıtlı e-posta adresi bulunamadı.")
            return

        self._run_mail_send(subject, body, recipients)

    # ── ortak mail başlatma ───────────────────────────────────────────────────
    def _run_mail_send(self, subject: str, body: str, recipients: list):
        """credentials.json kontrolü yapar, gerekirse kurulum diyaloğu açar,
        ardından OAuth akışını thread'de başlatır."""
        import os
        creds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
        token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gmail_token.json")

        # credentials.json yoksa kurulum yap
        if not os.path.exists(creds_path):
            setup = CredentialsSetupDialog(self)
            if setup.exec_() != QDialog.Accepted:
                return
            # token varsa sil (yeni credentials için)
            if os.path.exists(token_path):
                os.remove(token_path)

        # İlerleme mesajı
        self._send_progress = QMessageBox(self)
        self._send_progress.setWindowTitle("Gmail ile Bağlanıyor")
        self._send_progress.setText(
            "🌐  Tarayıcı üzerinden Gmail hesabına giriş yapın...\n\n"
            "Token zaten varsa tarayıcı açılmaz ve gönderim başlar.\n\n"
            "Lütfen bekleyin..."
        )
        self._send_progress.setStandardButtons(QMessageBox.NoButton)
        self._send_progress.setStyleSheet("""
            QMessageBox { background:#0D0D1A; }
            QLabel { color:#C0C0E0; font-size:13px; }
        """)
        self._send_progress.show()

        self._worker = EmailWorker(subject, body, recipients)
        self._worker.finished.connect(self._on_mail_done)
        self._worker.start()

    def _on_mail_done(self, success, message):
        self._send_progress.close()

        # credentials.json bulunamadı hatası
        if message == "CREDENTIALS_NOT_FOUND":
            QMessageBox.critical(
                self, "Hata",
                "credentials.json bulunamadı.\n"
                "Lütfen önce Gmail API kurulumunu tamamlayın."
            )
            return

        if success:
            QMessageBox.information(self, "Başarılı", f"✅  {message}")
        else:
            QMessageBox.critical(self, "Hata", f"❌  {message}")


# ─── MESAJ GİRİŞ DİYALOĞU ────────────────────────────────────────────────────
class _BodyDialog(QDialog):
    """Çok satırlı mesaj girişi için minimal diyalog."""
    def __init__(self, parent=None, default=""):
        super().__init__(parent)
        self.setWindowTitle("Mesaj İçeriği")
        self.setMinimumWidth(480)
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
            QPushButton#cancel {
                background:#1E1E30; color:#7070A0; border-color:#30305A;
            }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 22, 22, 22)
        lay.setSpacing(12)
        lay.addWidget(QLabel("Mesaj İçeriği:"))
        self._edit = QTextEdit()
        self._edit.setMinimumHeight(160)
        self._edit.setPlainText(default)
        lay.addWidget(self._edit)
        row = QHBoxLayout()
        row.setSpacing(8)
        cancel = QPushButton("İptal")
        cancel.setObjectName("cancel")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Devam Et →")
        ok.clicked.connect(self.accept)
        row.addWidget(cancel)
        row.addStretch()
        row.addWidget(ok)
        lay.addLayout(row)

    def get_text(self):
        return self._edit.toPlainText()
