import sqlite3
from datetime import date

# Veritabanı bağlantısı
conn = sqlite3.connect('butik_database.db')
c = conn.cursor()

# Tabloları oluştur
c.execute('''CREATE TABLE IF NOT EXISTS Customers (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                email TEXT,
                register_date DATE NOT NULL
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS Purchases (
                purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                product_name TEXT NOT NULL,
                amount REAL NOT NULL,
                purchase_date DATE NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
            )''')

conn.commit()
#myk