import flet as ft
import pandas as pd
import json
import os

DB_FILE = "database_modal.json"

def muat_database():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def simpan_database(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

def bersihkan_angka(val):
    if pd.isna(val) or str(val).strip() == '': return 0
    return float(str(val).replace('.', '').split(',')[0])

def main(page: ft.Page):
    page.title = "Shine Perabot - Laba Bersih"
    page.window_width = 400
    page.window_height = 800
    page.bgcolor = "#F4F7FE"
    page.scroll = "auto"
    page.padding = 0
    
    db_modal = muat_database()
    
    # State Variables
    file_path_terpilih = ft.Text("Belum ada file...", size=12, color="#A3AED0", italic=True)
    list_produk_ui = ft.Column(spacing=10)
    label_laba_bersih = ft.Text("Rp 0", size=32, weight="bold", color="#2B3674")
    label_omset = ft.Text("Omset: Rp 0", size=12, color="#05CD99", weight="bold")
    
    input_admin = ft.TextField(label="Admin (%)", value="9.0", width=120, height=45, text_size=12, bgcolor="white", border_color="#E2E8F0")
    input_iklan = ft.TextField(label="Iklan (Rp)", value="0", width=150, height=45, text_size=12, bgcolor="white", border_color="#E2E8F0")

    # Variabel untuk menampung DataFrame Excel
    df_global = {"data": None}

    def proses_file_excel(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            file_path_terpilih.value = f"📄 {e.files[0].name}"
            
            try:
                df = pd.read_excel(file_path, dtype=str)
                if 'Subtotal Pesanan' not in df.columns or 'Jumlah' not in df.columns:
                    file_path_terpilih.value = "Format Laporan Shopee Salah!"
                    page.update()
                    return
                
                df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0)
                df['Subtotal Pesanan'] = df['Subtotal Pesanan'].apply(bersihkan_angka)
                df_global["data"] = df
                
                # Rekap per produk
                produk_terjual = df.groupby('Nama Produk').agg({'Jumlah': 'sum', 'Subtotal Pesanan': 'sum'}).reset_index()
                produk_terjual = produk_terjual[produk_terjual['Jumlah'] > 0]
                produk_terjual = produk_terjual.sort_values(by='Jumlah', ascending=False)
                
                list_produk_ui.controls.clear()
                
                for _, row in produk_terjual.iterrows():
                    nama = str(row['Nama Produk'])
                    terjual = int(row['Jumlah'])
                    omset_produk = float(row['Subtotal Pesanan'])
                    hpp_lama = db_modal.get(nama, "")
                    
                    input_hpp = ft.TextField(
                        value=str(hpp_lama), hint_text="HPP (Rp)", width=90, height=40,
                        text_size=12, bgcolor="#F4F7FE", border_color="#E2E8F0"
                    )
                    
                    card = ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(nama[:25] + "..." if len(nama) > 25 else nama, size=12, weight="bold", color="#2B3674"),
                                ft.Text(f"🔥 {terjual} Terjual | Omset: Rp {omset_produk:,.0f}", size=10, color="#FF9800", weight="bold")
                            ], expand=True),
                            input_hpp
                        ], alignment="spaceBetween"),
                        bgcolor="white", padding=10, border_radius=8
                    )
                    card.data = {"nama": nama, "terjual": terjual, "omset": omset_produk, "input": input_hpp}
                    list_produk_ui.controls.append(card)
                
                page.update()
            except Exception as err:
                file_path_terpilih.value = f"Error: {err}"
                page.update()

    file_picker = ft.FilePicker(on_result=proses_file_excel)
    page.overlay.append(file_picker)

    def hitung_laba_kotor(e):
        if df_global["data"] is None:
            return
        
        total_omset = 0
        total_modal = 0
        
        for card in list_produk_ui.controls:
            nama = card.data["nama"]
            terjual = card.data["terjual"]
            omset = card.data["omset"]
            
            hpp_str = card.data["input"].value
            hpp = float(hpp_str) if hpp_str else 0
            
            if hpp_str:
                db_modal[nama] = hpp_str
                
            total_omset += omset
            total_modal += (hpp * terjual)
            
        simpan_database(db_modal)
        
        persen_admin = float(input_admin.value) / 100 if input_admin.value else 0
        biaya_iklan = float(input_iklan.value) if input_iklan.value else 0
        
        potongan_admin = total_omset * persen_admin
        laba_bersih = total_omset - total_modal - potongan_admin - biaya_iklan
        
        label_omset.value = f"Omset Bersih: Rp {total_omset:,.0f}"
        label_laba_bersih.value = f"Rp {laba_bersih:,.0f}"
        if laba_bersih < 0:
            label_laba_bersih.color = "red"
        else:
            label_laba_bersih.color = "#2B3674"
            
        page.update()

    # UI Layout
    header = ft.Container(
        content=ft.Column([
            ft.Text("Selamat Datang,", size=12, color="#E0E5FF"),
            ft.Text("Shine Perabot", size=24, weight="bold", color="white"),
        ]),
        bgcolor="#4318FF", padding=ft.padding.only(left=20, top=40, right=20, bottom=40), width=float("inf"), border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20)
    )

    card_laba = ft.Container(
        content=ft.Column([
            ft.Text("Laba Bersih Laporan Ini", size=12, color="#A3AED0"),
            label_laba_bersih,
            label_omset
        ]),
        bgcolor="white", padding=20, border_radius=15, width=float("inf"), margin=ft.margin.only(top=-30, left=20, right=20, bottom=10),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color="#E2E8F0", offset=ft.Offset(0, 5))
    )
    
    main_content = ft.Container(
        content=ft.Column([
            ft.Text("Parameter Laporan", size=14, weight="bold", color="#2B3674"),
            ft.Row([
                ft.ElevatedButton("📂 Pilih Excel (.xlsx)", on_click=lambda _: file_picker.pick_files(allow_multiple=False), bgcolor="#E6F9F5", color="#05CD99"),
                file_path_terpilih
            ]),
            ft.Row([input_admin, input_iklan], spacing=10),
            ft.Divider(color="#E2E8F0", height=20),
            ft.Text("Database HPP (Otomatis Tersimpan)", size=14, weight="bold", color="#2B3674"),
            list_produk_ui,
            ft.Divider(color="transparent", height=10),
            ft.ElevatedButton("SINKRONISASI & HITUNG LABA", bgcolor="#4318FF", color="white", width=float("inf"), height=50, on_click=hitung_laba_kotor)
        ], scroll="auto"),
        padding=20, expand=True
    )
    
    page.add(header, card_laba, main_content)

if __name__ == "__main__":
    ft.app(target=main)
