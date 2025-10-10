from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
    QListWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox, QFrame,
    QInputDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QFont

from functions import (
    load_customers, add_customer, delete_customer, update_customer,
    add_purchase, view_purchases, send_bulk_email, customer_dict
)


class BoutiqueApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Müşteri Yönetim Sistemi")
        self.setGeometry(100, 100, 1200, 800)
        self.set_dark_theme()
        self.apply_styles()

        self.widget = QWidget()
        self.setCentralWidget(self.widget)

        self.create_ui()

    def filter_customers(self):
        query = self.search_input.text().lower().strip()
        self.customer_list.clear()
        for display_text in customer_dict.keys():
            if query in display_text.lower():
                self.customer_list.addItem(display_text)

    
    def set_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#121212"))
        palette.setColor(QPalette.WindowText, QColor("#E0E0E0"))
        palette.setColor(QPalette.Base, QColor("#121212"))
        palette.setColor(QPalette.AlternateBase, QColor("#121212"))
        palette.setColor(QPalette.Text, QColor("#E0E0E0"))
        palette.setColor(QPalette.Button, QColor("#3A3A3A"))
        palette.setColor(QPalette.ButtonText, QColor("#FFFFFF"))
        palette.setColor(QPalette.Highlight, QColor("#888888"))
        palette.setColor(QPalette.HighlightedText, QColor("#121212"))
        self.setPalette(palette)

    def apply_styles(self):
        self.setStyleSheet("""
            QLabel {
                color: #E0E0E0;
                font-size: 14px;
            }

            QListWidget {
                padding: 8px;
                border: 1px solid #333;
                border-radius: 10px;
                background-color: #1E1E1E;
                color: white;
                font-size: 14px;
            }

            QListWidget::item {
                color: white;
                padding: 6px;
            }

            QTextEdit, QLineEdit, QComboBox {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #444;
                border-radius: 10px;
                padding: 6px 8px;
                font-size: 14px;
            }

            QPushButton {
                background-color: #3A3A3A;
                color: white;
                border: 2px solid #3A3A3A;
                padding: 12px 20px;
                border-radius: 20px;
                font-size: 16px;
                font-weight: bold;
             
            }

            QPushButton:hover {
                background-color: #5A5A5A;
                border: 2px solid #B0C4FF;
                
                
            }

            QPushButton:pressed {
                background-color: #2A2A2A;
                border: 2px solid #88A2FF;
                
            }

            QFrame[section="true"] {
                background-color: #1C1C1C;
                border-radius: 16px;
                padding: 16px;
                margin-bottom: 20px;
            }
        """)

    def create_ui(self):
        main_layout = QGridLayout()

        def title(text):
            label = QLabel(text)
            label.setFont(QFont("Helvetica", 13, QFont.Bold))
            label.setStyleSheet("color: #E0E0E0; margin-bottom: 10px;")
            return label

        # Bölüm: Müşteri Ekle
        customer_section = QFrame()
        customer_section.setProperty("section", True)
        customer_layout = QVBoxLayout(customer_section)

        customer_layout.addWidget(title("👥 Müşteri Ekle"))
        customer_form = QGridLayout()

        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.country_code = QComboBox()
        self.country_code.addItems(["+90", "+49"])

        customer_form.addWidget(QLabel("Ad:"), 0, 0)
        customer_form.addWidget(self.name_input, 0, 1)
        customer_form.addWidget(QLabel("Ülke Kodu:"), 1, 0)
        customer_form.addWidget(self.country_code, 1, 1)
        customer_form.addWidget(QLabel("Telefon:"), 2, 0)
        customer_form.addWidget(self.phone_input, 2, 1)
        customer_form.addWidget(QLabel("Email:"), 3, 0)
        customer_form.addWidget(self.email_input, 3, 1)

        self.add_customer_btn = QPushButton("Müşteri Ekle")
        self.add_customer_btn.clicked.connect(lambda: add_customer(
            self.name_input, self.phone_input, self.email_input, self.country_code, self.customer_list))
        customer_form.addWidget(self.add_customer_btn, 4, 0, 1, 2)

        customer_layout.addLayout(customer_form)

        # Bölüm: Alışveriş Ekle
        purchase_section = QFrame()
        purchase_section.setProperty("section", True)
        purchase_layout = QVBoxLayout(purchase_section)

        purchase_layout.addWidget(title("🛒 Alışveriş Ekle"))
        purchase_form = QGridLayout()

        self.product_input = QLineEdit()
        self.amount_input = QLineEdit()

        purchase_form.addWidget(QLabel("Ürün:"), 0, 0)
        purchase_form.addWidget(self.product_input, 0, 1)
        purchase_form.addWidget(QLabel("Tutar:"), 1, 0)
        purchase_form.addWidget(self.amount_input, 1, 1)

        self.add_purchase_btn = QPushButton("Alışveriş Kaydet")
        self.add_purchase_btn.clicked.connect(lambda: add_purchase(
            self.product_input, self.amount_input, self.customer_list))
        purchase_form.addWidget(self.add_purchase_btn, 2, 0, 1, 2)

        purchase_layout.addLayout(purchase_form)



                # Bölüm: Kayıtlı Müşteriler
        list_section = QFrame()
        list_section.setProperty("section", True)
        list_layout = QVBoxLayout(list_section)

        list_layout.addWidget(title("📋 Kayıtlı Müşteriler"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("İsim, telefon veya email ile ara...")
        self.search_input.setStyleSheet("""
            background-color: #1E1E1E;
            color: white;
            border: 1px solid #444;
            border-radius: 6px;
            padding: 6px;
        """)
        self.search_input.textChanged.connect(self.filter_customers)
        list_layout.addWidget(self.search_input)  

        self.customer_list = QListWidget()
        self.customer_list.setStyleSheet("""
            QListWidget {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: none;
                border-radius: 8px;
                padding: 4px;
            }

            QScrollBar:vertical {
                background: #1E1E1E;
                width: 12px;
                margin: 2px 0 2px 0;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background: #888888;
                min-height: 20px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical:hover {
                background: #B0B0B0;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                subcontrol-origin: margin;
            }

            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        list_layout.addWidget(self.customer_list)

        self.view_btn = QPushButton("Bilgi Görüntüleme ve Güncelleme")
        self.view_btn.clicked.connect(lambda: view_purchases(self.customer_list))
        self.delete_btn = QPushButton("Sil")
        self.delete_btn.clicked.connect(lambda: delete_customer(self.customer_list))

        list_layout.addWidget(self.view_btn)
        list_layout.addWidget(self.delete_btn)





        # Bölüm: Mail Gönderimi
        mail_section = QFrame()
        mail_section.setProperty("section", True)
        mail_layout = QVBoxLayout(mail_section)

        mail_layout.addWidget(title("📨 Toplu Mail Gönderimi"))
        self.subject_input = QLineEdit()
        self.body_input = QTextEdit()
        self.send_email_btn = QPushButton("Mail Gönder")
        self.send_email_btn.clicked.connect(self.send_email_clicked)

        mail_layout.addWidget(QLabel("Konu:"))
        mail_layout.addWidget(self.subject_input)
        mail_layout.addWidget(QLabel("Mesaj:"))
        mail_layout.addWidget(self.body_input)
        mail_layout.addWidget(self.send_email_btn)

        # Ana Grid Yerleşimi (4 Bölme)
        main_layout.addWidget(customer_section, 0, 0)
        main_layout.addWidget(purchase_section, 1, 0)
        main_layout.addWidget(list_section, 0, 1, 2, 1)
        main_layout.addWidget(mail_section, 2, 0, 1, 2)

        self.widget.setLayout(main_layout)

        # Müşterileri yükle
        load_customers(self.customer_list)

    def send_email_clicked(self):
        subject = self.subject_input.text()
        body = self.body_input.toPlainText()
        if not subject or not body:
            QMessageBox.warning(self, "Uyarı", "Konu ve mesaj boş olamaz.")
            return
        from_email, ok1 = QInputDialog.getText(self, "Mail Girişi", "Gönderici E-Posta:")
        password, ok2 = QInputDialog.getText(self, "Mail Girişi", "Şifre:", QLineEdit.Password)
        if ok1 and ok2:
            success = send_bulk_email(subject, body, from_email, password)
            if success:
                QMessageBox.information(self, "Başarılı", "Mailler gönderildi.")
            else:
                QMessageBox.critical(self, "Hata", "Gönderim başarısız.")
