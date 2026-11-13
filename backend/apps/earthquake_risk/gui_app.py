import os
import platform
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from risk_engine import EarthquakeRiskEngine, haversine
from risk_engine import FAULT_LINES, FAULT_POINTS
from data_manager import fetch_and_update_data
from map_visualizer import generate_map

BASE_DIR = Path(__file__).resolve().parent
FAULT_MAPS_DIR = BASE_DIR / "data" / "fault_maps" / "fay_haritası"
CAMERA_ROOT = BASE_DIR.parent / "camera_detection"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Deprem Risk ve Tespit Paneli")
        self.root.geometry("900x600")
        
        if ctk:
            ctk.set_appearance_mode("Dark")
            ctk.set_default_color_theme("dark-blue")
            
            # Linux scaling fix
            if platform.system() == "Linux":
                ctk.set_widget_scaling(1.0)
                ctk.set_window_scaling(1.0)
            self.root.configure(bg="#1a1a1a")
        else:
            self.root.configure(bg="#0b1c2c")

        self.engine = EarthquakeRiskEngine()
        self.status_var = tk.StringVar(value="Hazır")

        # Canlı veri güncellemesi
        self._update_data_on_startup()

        self._build_layout()

    def _update_data_on_startup(self):
        def run():
            try:
                self.status_var.set("Veriler güncelleniyor...")
                msg = fetch_and_update_data()
                self.root.after(0, lambda: self._log(f"Veri Durumu: {msg}"))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"Veri güncelleme hatası: {e}"))
            finally:
                self.root.after(0, lambda: self.status_var.set("Hazır"))
        
        threading.Thread(target=run, daemon=True).start()

    def _build_layout(self):
        # Ana Container
        if ctk:
            self.main_frame = ctk.CTkFrame(self.root, corner_radius=0)
            self.main_frame.pack(fill="both", expand=True)
            
            # Sol Panel (Sidebar)
            self.sidebar = ctk.CTkFrame(self.main_frame, width=250, corner_radius=0)
            self.sidebar.pack(side="left", fill="y")
            
            logo_label = ctk.CTkLabel(
                self.sidebar, 
                text="Deprem Paneli", 
                font=ctk.CTkFont(family="Ubuntu", size=24, weight="bold")
            )
            logo_label.pack(padx=20, pady=(20, 10))
            
            # Butonlar
            self.camera_btn = ctk.CTkButton(
                self.sidebar,
                text="Kamera Tespiti",
                command=self._on_camera,
                height=40,
                font=("Ubuntu", 16, "bold"),
                fg_color="#1e88e5",
                hover_color="#1565c0",
                corner_radius=0
            )
            self.camera_btn.pack(padx=20, pady=10, fill="x")

            self.risk_btn = ctk.CTkButton(
                self.sidebar,
                text="Risk Hesapla",
                command=self._on_risk,
                height=40,
                font=("Ubuntu", 16, "bold"),
                fg_color="#d81b60",
                hover_color="#ad1457",
                corner_radius=0
            )
            self.risk_btn.pack(padx=20, pady=10, fill="x")

            self.map_btn = ctk.CTkButton(
                self.sidebar,
                text="Harita",
                command=self._on_map,
                height=40,
                font=("Ubuntu", 16, "bold"),
                fg_color="#fbc02d",
                text_color="black",
                hover_color="#f9a825",
                state="disabled",
                corner_radius=0
            )
            self.map_btn.pack(padx=20, pady=10, fill="x")
            
            # Sağ Panel (İçerik)
            self.content_frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="transparent")
            self.content_frame.pack(side="right", fill="both", expand=True)
            
            # Başlık
            header = ctk.CTkLabel(
                self.content_frame,
                text="Analiz Sonuçları",
                font=ctk.CTkFont(family="Ubuntu", size=20, weight="bold"),
                anchor="w"
            )
            header.pack(padx=20, pady=(20, 10), fill="x")
            
            # Çıktı Alanı
            self.output = ctk.CTkTextbox(
                self.content_frame,
                width=400,
                font=ctk.CTkFont(family="Ubuntu Mono", size=13)
            )
            self.output.pack(fill="both", expand=True, padx=20, pady=10)
            self.output.insert("end", "Paneli kullanmak için sol menüden işlem seçin.\n")
            self.output.configure(state="disabled")
            
            # Durum Çubuğu
            self.status_label = ctk.CTkLabel(
                self.content_frame,
                textvariable=self.status_var,
                anchor="w",
                text_color="gray"
            )
            self.status_label.pack(fill="x", padx=20, pady=10)

        else:
            # Fallback to standard tkinter if customtkinter is missing
            header = tk.Label(
                self.root,
                text="Şehir Bazlı Deprem Riski ve Kamera Tespiti",
                bg="#0b1c2c",
                fg="#f2f5f7",
                font=("Arial", 18, "bold"),
                pady=16,
            )
            header.pack(fill="x")

            btn_frame = tk.Frame(self.root, bg="#0b1c2c")
            btn_frame.pack(fill="x", padx=20, pady=10)

            self.camera_btn = tk.Button(
                btn_frame,
                text="📷 Kamerayı Aç ve Tespit Et",
                command=self._on_camera,
                bg="#1e88e5",
                fg="white",
                font=("Arial", 12, "bold"),
                relief="flat",
                padx=14,
                pady=10,
                width=24,
            )
            self.camera_btn.pack(side="left", expand=True, padx=8)

            self.risk_btn = tk.Button(
                btn_frame,
                text="🌍 Deprem Riskini Hesapla",
                command=self._on_risk,
                bg="#d81b60",
                fg="white",
                font=("Arial", 12, "bold"),
                relief="flat",
                padx=14,
                pady=10,
                width=24,
            )
            self.risk_btn.pack(side="left", expand=True, padx=8)

            self.map_btn = tk.Button(
                btn_frame,
                text="🗺️ Haritada Göster",
                command=self._on_map,
                bg="#fbc02d",
                fg="black",
                font=("Arial", 12, "bold"),
                relief="flat",
                padx=14,
                pady=10,
                width=24,
                state="disabled"
            )
            self.map_btn.pack(side="left", expand=True, padx=8)

            self.output = tk.Text(
                self.root,
                bg="#0f1f30",
                fg="#e5ecf0",
                bd=0,
                relief="flat",
                wrap="word",
                font=("Consolas", 11),
                height=15
            )
            self.output.pack(fill="both", expand=True, padx=20, pady=10)
            self.output.insert("end", "Paneli kullanmak için butonlardan birini seçin.\n")
            self.output.config(state="disabled")

            status_bar = tk.Label(
                self.root,
                textvariable=self.status_var,
                bg="#0b1c2c",
                fg="#9cc3d5",
                anchor="w",
                padx=12,
                pady=6,
            )
            status_bar.pack(fill="x")

    def _log(self, text):
        if ctk:
            self.output.configure(state="normal")
            self.output.insert("end", text + "\n")
            self.output.see("end")
            self.output.configure(state="disabled")
        else:
            self.output.config(state="normal")
            self.output.insert("end", text + "\n")
            self.output.see("end")
            self.output.config(state="disabled")

    def _set_busy(self, busy=True):
        state = "disabled" if busy else "normal"
        if ctk:
            self.camera_btn.configure(state=state)
            self.risk_btn.configure(state=state)
        else:
            self.camera_btn.config(state=state)
            self.risk_btn.config(state=state)
        
        self.status_var.set("İşleniyor..." if busy else "Hazır")

    def _on_camera(self):
        self._log("Kamera tespiti başlatılıyor...")

        def run():
            try:
                if str(CAMERA_ROOT) not in sys.path:
                    sys.path.insert(0, str(CAMERA_ROOT))
                from camera_manager import main as cam_main
                cam_main()
            except Exception as exc:
                messagebox.showerror("Hata", f"Kamera başlatılamadı: {exc}")
            finally:
                self._log("Kamera tespiti kapandı.")

        threading.Thread(target=run, daemon=True).start()

    def _on_risk(self):
        # CustomTkinter dialog
        if ctk:
            dialog = ctk.CTkInputDialog(text="Şehir ismi girin:", title="Şehir")
            city = dialog.get_input()
        else:
            city = simpledialog.askstring("Şehir", "Şehir ismi girin:", parent=self.root)
            
        if not city:
            return

        self._set_busy(True)
        self._log(f"{city} için risk hesaplanıyor...")

        def run():
            try:
                result = self.engine.predict_city_risk(city)
                self._log(result)
                
                # Şehre ait depremleri filtrele (150 km yarıçap)
                full_df = self.engine.df_full
                dists = haversine(
                    self.engine.last_lat, 
                    self.engine.last_lon, 
                    full_df["latitude"].values, 
                    full_df["longitude"].values
                )
                city_quakes = full_df[dists <= 150.0].copy()

                # Harita butonunu aktif et ve şehir bilgisini sakla
                self.last_city_data = {
                    "name": city,
                    "lat": self.engine.last_lat,
                    "lon": self.engine.last_lon,
                    "df": city_quakes
                }
                
                if ctk:
                    self.map_btn.configure(state="normal")
                else:
                    self.map_btn.config(state="normal")
                
            except Exception as exc:
                messagebox.showerror("Hata", str(exc))
            finally:
                self._set_busy(False)

        threading.Thread(target=run, daemon=True).start()

    def _on_map(self):
        if not hasattr(self, "last_city_data") or not self.last_city_data:
            messagebox.showinfo("Bilgi", "Önce bir şehir için risk hesaplamalısınız.")
            return
            
        try:
            data = self.last_city_data
            # GeoJSON dosyalarının yolları
            geojson_files = [
                str(FAULT_MAPS_DIR / "gem_active_faults.geojson"),
                str(FAULT_MAPS_DIR / "gem_active_faults_harmonized.geojson"),
            ]
            
            path = generate_map(
                data["name"], 
                data["lat"], 
                data["lon"], 
                FAULT_POINTS, 
                fault_lines=FAULT_LINES, 
                geojson_paths=geojson_files,
                all_quakes_df=data["df"]
            )
            self._log(f"Harita oluşturuldu: {path}")
        except ImportError as e:
             messagebox.showerror("Eksik Kütüphane", str(e))
        except Exception as e:
            messagebox.showerror("Hata", f"Harita oluşturulurken hata: {e}")
