
import tkinter as tk
from tkinter import messagebox, StringVar, OptionMenu
from tkinter import ttk
from functions import *
from functions import customer_dict, load_customers
from functions import send_bulk_email

def start_gui():
    root = tk.Tk()
    root.title("Butik Yönetim Sistemi (Mail Destekli)")
    root.geometry("1000x700")
    root.minsize(800, 600)
    root.configure(bg="#2E2E2E")

    font_family = ("Helvetica Neue", 10)

    main_frame = tk.Frame(root, bg="#2E2E2E")
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    left_frame = tk.Frame(main_frame, bg="#2E2E2E")
    left_frame.pack(side="left", fill="both", expand=True, padx=5)

    right_frame = tk.Frame(main_frame, bg="#2E2E2E")
    right_frame.pack(side="right", fill="both", expand=True, padx=5)

    # Müşteri Ekle
    customer_label_frame = tk.LabelFrame(left_frame, text="Müşteri Ekle", bg="#3C3C3C", fg="white", font=font_family)
    customer_label_frame.pack(fill="x", pady=10)

    entry_name = tk.Entry(customer_label_frame, font=font_family)
    entry_phone = tk.Entry(customer_label_frame, font=font_family)
    entry_email = tk.Entry(customer_label_frame, font=font_family)

    country_codes = ["+90", "+49"]
    country_code_var = StringVar(value=country_codes[0])
    country_menu = OptionMenu(customer_label_frame, country_code_var, *country_codes)
    country_menu.configure(bg="#3f3f5f", fg="white")

    labels = ["Müşteri Adı", "Ülke Kodu", "Telefon", "Email"]
    entries = [entry_name, country_menu, entry_phone, entry_email]

    for i, (label, widget) in enumerate(zip(labels, entries)):
        tk.Label(customer_label_frame, text=label, bg="#3C3C3C", fg="white", font=font_family).grid(row=i, column=0, sticky="e", padx=5, pady=3)
        widget.grid(row=i, column=1, sticky="ew", padx=5, pady=3)

    def styled_button(master, text, command):
        return tk.Button(master, text=text, command=command, font=("Helvetica Neue", 10, "bold"),
                         bg="#4A47A3", fg="white", activebackground="#635FC7", bd=4, relief="raised", highlightthickness=1, highlightbackground="#777", padx=10, pady=5)

    styled_button(customer_label_frame, "Müşteri Ekle", lambda: add_customer(entry_name, entry_phone, entry_email, country_code_var, customer_listbox)).grid(row=4, column=0, columnspan=2, pady=10)

    # Alışveriş Ekle
    purchase_label_frame = tk.LabelFrame(left_frame, text="Alışveriş Ekle", bg="#3C3C3C", fg="white", font=font_family)
    purchase_label_frame.pack(fill="x", pady=10)

    entry_product = tk.Entry(purchase_label_frame, font=font_family)
    entry_amount = tk.Entry(purchase_label_frame, font=font_family)

    tk.Label(purchase_label_frame, text="Ürün Adı", bg="#3C3C3C", fg="white", font=font_family).grid(row=0, column=0, sticky="e", padx=5, pady=3)
    entry_product.grid(row=0, column=1, sticky="ew", padx=5, pady=3)

    tk.Label(purchase_label_frame, text="Fiyat", bg="#3C3C3C", fg="white", font=font_family).grid(row=1, column=0, sticky="e", padx=5, pady=3)
    entry_amount.grid(row=1, column=1, sticky="ew", padx=5, pady=3)

    styled_button(purchase_label_frame, "Alışveriş Ekle", lambda: add_purchase(entry_product, entry_amount, customer_listbox)).grid(row=2, column=0, columnspan=2, pady=10)

    # Arama
    search_var = StringVar()
    def filter_customers():
        query = search_var.get().lower()
        customer_listbox.delete(0, tk.END)
        for display, cid in customer_dict.items():
            if query in display.lower():
                customer_listbox.insert(tk.END, display)

    search_frame = tk.Frame(right_frame, bg="#2E2E2E")
    search_frame.pack(pady=(0, 10), fill="x")

    tk.Label(search_frame, text="Ara:", bg="#2E2E2E", fg="white", font=font_family).pack(side="left")
    search_entry = tk.Entry(search_frame, textvariable=search_var, font=font_family)
    search_entry.pack(side="left", padx=5)
    styled_button(search_frame, "Filtrele", filter_customers).pack(side="left")

    # Liste
    customer_listbox = tk.Listbox(right_frame, font=font_family, bg="#4B4B4B", fg="white", bd=0, relief="flat")
    customer_listbox.pack(fill="both", expand=True, padx=5, pady=5)

    button_frame = tk.Frame(right_frame, bg="#2E2E2E")
    button_frame.pack(pady=10)

    styled_button(button_frame, "Alışveriş Geçmişini Gör", lambda: view_purchases(customer_listbox)).pack(pady=5)
    styled_button(button_frame, "Müşteriyi Sil", lambda: delete_customer(customer_listbox)).pack(pady=5)
    styled_button(button_frame, "Müşteri Bilgilerini Güncelle", lambda: open_customer_window(customer_dict[customer_listbox.get(tk.ACTIVE)])).pack(pady=5)

    # Toplu Mail Gönderimi
    email_frame = tk.LabelFrame(right_frame, text="Toplu Mail Gönderimi", bg="#3C3C3C", fg="white", font=font_family)
    email_frame.pack(fill="x", padx=5, pady=10)

    tk.Label(email_frame, text="Konu:", bg="#3C3C3C", fg="white", font=font_family).pack(anchor="w", padx=5, pady=(5, 0))
    subject_entry = tk.Entry(email_frame, font=font_family)
    subject_entry.pack(fill="x", padx=5)

    tk.Label(email_frame, text="Mesaj:", bg="#3C3C3C", fg="white", font=font_family).pack(anchor="w", padx=5, pady=(5, 0))
    message_text = tk.Text(email_frame, font=font_family, height=5)
    message_text.pack(fill="x", padx=5)

    def prompt_and_send_email():
        subject = subject_entry.get().strip()
        body = message_text.get("1.0", "end").strip()

        if not subject or not body:
            messagebox.showwarning("Uyarı", "Konu ve mesaj boş bırakılamaz.")
            return

        top = tk.Toplevel(root)
        top.title("Mail Girişi")
        top.geometry("300x150")
        top.grab_set()

        tk.Label(top, text="E-posta Adresi:", font=font_family).pack(pady=5)
        email_var = tk.StringVar()
        tk.Entry(top, textvariable=email_var).pack()

        tk.Label(top, text="Şifre:", font=font_family).pack(pady=5)
        password_var = tk.StringVar()
        tk.Entry(top, textvariable=password_var, show="*").pack()

        def send_now():
            success = send_bulk_email(subject, body, email_var.get(), password_var.get())
            if success:
                messagebox.showinfo("Başarılı", "Mailler gönderildi!")
                top.destroy()
            else:
                messagebox.showerror("Hata", "Mail gönderilemedi!")

        tk.Button(top, text="Gönder", command=send_now).pack(pady=10)

    styled_button(email_frame, "Toplu Mail Gönder", prompt_and_send_email).pack(pady=5)

    load_customers(customer_listbox)
    root.mainloop()
