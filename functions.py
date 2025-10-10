from datetime import date
from PyQt5.QtWidgets import QListWidget, QMessageBox
import smtplib
from email.mime.text import MIMEText
from database import c, conn
import re

from PyQt5.QtWidgets import QMessageBox

def themed_message(title, message, icon=QMessageBox.Information):
    box = QMessageBox()
    box.setWindowTitle(title) 
    box.setText(message) 
    box.setIcon(QMessageBox.Information)
    box.setStyleSheet("""
        QMessageBox {
            background-color: #121212;
            color: #FFFFFF;
            font-size: 11pt;
            font-family: 'Segoe UI';
        }
        QLabel {
            color: #FFFFFF;
        }
        QPushButton {
            background-color: #888888;
            color: white;
            border-radius: 8px;
            padding: 6px 12px;
        }
    """)
    box.exec_()


def themed_question(parent, title, message):
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(message)
    box.setIcon(QMessageBox.Question)
    box.setStandardButtons(QMessageBox.Yes  | QMessageBox.No)
    box.setStyleSheet("""
        QMessageBox {
            background-color: #121212;
            color: #ffffff;
            font-size: 11pt;
            font-family: 'Segoe UI';
        }
        QLabel {
            color: #ffffff;
        }
        QPushButton {
            background-color: #888888;
            color: white;
            border-radius: 6px;
            padding: 6px 14px;
        }
        QPushButton:hover {
            background-color: #AAAAAA;
        }
    """)
    return box.exec_()



customer_dict = {}

def is_valid_phone(phone):
    return bool(re.fullmatch(r"[0-9 ]+", phone))

def filter_customers(self):
    query = self.search_input.text().lower().strip()
    self.customer_list.clear()
    for display_text in customer_dict.keys():
        if query in display_text.lower():
            self.customer_list.addItem(display_text)


def load_customers(customer_listbox: QListWidget):
    customer_listbox.clear()
    customer_dict.clear()
    c.execute("SELECT * FROM Customers")
    for customer in c.fetchall():
        email = customer[3] if customer[3] else "Email yok"
        display = f"{customer[1]} - {customer[2]} - {email}"
        customer_listbox.addItem(display)
        customer_dict[display] = customer[0]

def add_customer(name_input, phone_input, email_input, country_code_combo, customer_listbox):
    name = name_input.text().strip()
    phone = phone_input.text().strip()
    email = email_input.text().strip()
    country_code = country_code_combo.currentText()

    if not name or not phone:
        themed_message("Uyarı", "Ad ve telefon zorunlu.")
        return

    if not is_valid_phone(phone):
        themed_message("Uyarı", "Telefon sadece rakam ve boşluk içerebilir.")
        return


    full_phone = country_code + phone
    c.execute('INSERT INTO Customers (name, phone_number, email, register_date) VALUES (?, ?, ?, ?)',
              (name, full_phone, email, date.today()))
    conn.commit()
    themed_message("Başarılı", "Müşteri eklendi.")
    name_input.clear()
    phone_input.clear()
    email_input.clear()
    load_customers(customer_listbox)

def delete_customer(customer_listbox: QListWidget):
    selected = customer_listbox.currentItem()
    if selected:
        customer_id = customer_dict[selected.text()]
        confirm = themed_question(None, "Silme", "Müşteri silinsin mi?")
        if confirm == QMessageBox.Yes:
            c.execute("DELETE FROM Customers WHERE customer_id=?", (customer_id,))
            conn.commit()
            themed_message(None, "Başarılı", "Müşteri silindi.")
            load_customers(customer_listbox)
    else:
        themed_message(None, "Uyarı", "Müşteri seçilmedi.")

def add_purchase(product_input, amount_input, customer_listbox: QListWidget):
    selected = customer_listbox.currentItem()
    if selected:
        customer_id = customer_dict[selected.text()]
        product = product_input.text().strip()
        amount_text = amount_input.text().strip()

        if not product or not amount_text:
            themed_message(None, "Uyarı", "Alanlar boş olamaz.")
            return

        try:
            amount = float(amount_text)
        except ValueError:
            themed_message(None, "Hata", "Fiyat sayı olmalı.")
            return

        c.execute("INSERT INTO Purchases (customer_id, product_name, amount, purchase_date) VALUES (?, ?, ?, ?)",
                  (customer_id, product, amount, date.today()))
        conn.commit()
        themed_message(None, "Başarılı", "Alışveriş eklendi.")
        product_input.clear()
        amount_input.clear()
    else:
        themed_message.warning(None, "Uyarı", "Müşteri seçin.")

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QLineEdit, QPushButton, QHBoxLayout, QFormLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDateEdit
from PyQt5.QtCore import QDate

def view_purchases(customer_listbox: QListWidget):
    selected = customer_listbox.currentItem()
    if not selected:
        themed_message("warning", "Uyarı", "Lütfen bir müşteri seçin.")
        return

    customer_id = customer_dict[selected.text()]
    c.execute("SELECT * FROM Customers WHERE customer_id=?", (customer_id,))
    customer = c.fetchone()

    c.execute("SELECT * FROM Purchases WHERE customer_id=?", (customer_id,))
    purchases = c.fetchall()

    dialog = QDialog()
    dialog.setWindowTitle("Alışveriş Geçmişi ve Müşteri Güncelleme")
    dialog.setStyleSheet("""
        QDialog { background-color: #121212; color: #E0E0E0; font: 10pt "Segoe UI"; }
        QListWidget { background-color: #1E1E1E; color: #E0E0E0; border: 1px solid #444444; border-radius: 5px; }
        QLineEdit { background-color: #1E1E1E; color: #E0E0E0; border: 1px solid #444444; border-radius: 5px; padding: 4px; }
        QPushButton { background-color: #888888; color: white; border-radius: 6px; padding: 6px; }
        QPushButton:hover { background-color: #AAAAAA; }
        QLabel { color: #E0E0E0; }
    """)

    layout = QVBoxLayout(dialog)

    # --- Müşteri bilgisi güncelleme alanı
    layout.addWidget(QLabel("Müşteri Bilgileri"))

    customer_form = QFormLayout()
    name_input = QLineEdit(customer[1])
    phone_input = QLineEdit(customer[2])
    email_input = QLineEdit(customer[3] if customer[3] else "")

    customer_form.addRow("Ad:", name_input)
    customer_form.addRow("Telefon:", phone_input)
    customer_form.addRow("Email:", email_input)

    layout.addLayout(customer_form)

    def save_customer_update():
        new_name = name_input.text().strip()
        new_phone = phone_input.text().strip()
        new_email = email_input.text().strip()

        if not new_name or not new_phone:
            themed_message("warning", "Uyarı", "Ad ve telefon boş olamaz.")
            return

        if not new_phone.replace(" ", "").isdigit():
            themed_message("warning", "Uyarı", "Telefon yalnızca rakam ve boşluk içerebilir.")
            return

        c.execute("UPDATE Customers SET name=?, phone_number=?, email=? WHERE customer_id=?",
                  (new_name, new_phone, new_email, customer_id))
        conn.commit()
        themed_message("info", "Başarılı", "Müşteri bilgisi güncellendi.")
        dialog.close()

    save_customer_btn = QPushButton("Müşteri Bilgilerini Kaydet")
    save_customer_btn.clicked.connect(save_customer_update)
    layout.addWidget(save_customer_btn)

    # --- Alışveriş listesi
    layout.addWidget(QLabel("Alışveriş Geçmişi"))
    purchase_list = QListWidget()
    for p in purchases:
        item = QListWidgetItem(f"{p[0]} - {p[2]} - {p[3]} TL - {p[4]}")
        purchase_list.addItem(item)
    layout.addWidget(purchase_list)

    # --- Seçili alışverişi düzenle alanı
    form_layout = QFormLayout()
    product_input = QLineEdit()
    amount_input = QLineEdit()
    date_input = QDateEdit()
    date_input.setCalendarPopup(True)  # takvim açılır pencere
    date_input.setDate(QDate.currentDate())  # bugünün tarihi
    date_input.setStyleSheet("background-color: #1E1E1E; color: white; border: 1px solid #444; border-radius: 5px; padding: 4px;")

    form_layout.addRow("Yeni Ürün Adı:", product_input)
    form_layout.addRow("Yeni Tutar:", amount_input)
    form_layout.addRow("Yeni Tarih (YYYY-AA-GG):", date_input)
    layout.addLayout(form_layout)

    def update_selected_purchase():
        item = purchase_list.currentItem()
        if not item:
            themed_message("warning", "Uyarı", "Lütfen bir kayıt seçin.")
            return

        purchase_id = item.text().split(" - ")[0]
        new_product = product_input.text().strip()
        new_amount = amount_input.text().strip()
        new_date = date_input.text().strip()

        if not new_product or not new_amount or not new_date:
            themed_message("warning", "Uyarı", "Alanlar boş olamaz.")
            return

        try:
            float(new_amount)
        except ValueError:
            themed_message("error", "Hata", "Tutar sayısal olmalı.")
            return

        c.execute("UPDATE Purchases SET product_name=?, amount=?, purchase_date=? WHERE purchase_id=?",
                  (new_product, new_amount, new_date, purchase_id))
        conn.commit()
        themed_message("info", "Başarılı", "Alışveriş güncellendi.")
        dialog.close()

    def delete_selected_purchase():
        item = purchase_list.currentItem()
        if not item:
            themed_message("warning", "Uyarı", "Kayıt seçilmedi.")
            return

        purchase_id = item.text().split(" - ")[0]
        confirm = themed_question("Silme", "Bu alışveriş kaydı silinsin mi?")
        if confirm:
            c.execute("DELETE FROM Purchases WHERE purchase_id=?", (purchase_id,))
            conn.commit()
            themed_message("info", "Başarılı", "Kayıt silindi.")
            dialog.close()

    # Butonlar
    button_row = QHBoxLayout()
    update_btn = QPushButton("Güncelle")
    delete_btn = QPushButton("Sil")
    button_row.addWidget(update_btn)
    button_row.addWidget(delete_btn)
    layout.addLayout(button_row)

    update_btn.clicked.connect(update_selected_purchase)
    delete_btn.clicked.connect(delete_selected_purchase)

    dialog.setLayout(layout)
    dialog.resize(600, 500)
    dialog.exec_()



def update_customer(customer_listbox: QListWidget, name_input, phone_input, email_input, country_code_combo):
    selected = customer_listbox.currentItem()
    if selected:
        customer_id = customer_dict[selected.text()]
        new_name = name_input.text().strip()
        new_phone = phone_input.text().strip()
        new_email = email_input.text().strip()
        country_code = country_code_combo.currentText()

        if not new_name or not new_phone:
            themed_message.warning(None, "Uyarı", "Ad ve telefon zorunlu.")
            return

        if not is_valid_phone(new_phone):
            themed_message.warning(None, "Uyarı", "Telefon sadece rakam ve boşluk içerebilir.")
            return


        full_phone = country_code + new_phone
        c.execute("UPDATE Customers SET name=?, phone_number=?, email=? WHERE customer_id=?",
                  (new_name, full_phone, new_email, customer_id))
        conn.commit()
        themed_message.information(None, "Başarılı", "Müşteri güncellendi.")
        load_customers(customer_listbox)
    else:
        themed_message.warning(None, "Uyarı", "Müşteri seçilmedi.")

def send_bulk_email(subject, body, sender_email, sender_password):
    c.execute("SELECT email FROM Customers WHERE email IS NOT NULL AND email != ''")
    recipients = [row[0] for row in c.fetchall()]

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            for recipient in recipients:
                msg['To'] = recipient
                server.sendmail(sender_email, recipient, msg.as_string())
        return True
    except Exception as e:
        print("Mail gönderim hatası:", e)
        return False
