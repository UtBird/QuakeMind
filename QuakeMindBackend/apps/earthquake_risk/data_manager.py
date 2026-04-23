import requests
import pandas as pd
from datetime import datetime
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data" / "query.csv"
API_URL = "https://api.orhanaydogdu.com.tr/deprem/kandilli/live"

def fetch_and_update_data():
    """
    Kandilli API'den son depremleri çeker ve data/query.csv dosyasına ekler.
    Sadece yeni depremleri ekler (tarih ve büyüklük kontrolü ile).
    """
    print("Canlı veri kontrol ediliyor...")
    
    try:
        # 1. Mevcut CSV'yi Oku
        if CSV_PATH.exists():
            try:
                df_existing = pd.read_csv(CSV_PATH)
                # Tarih formatını datetime objesine çevir (UTC olarak)
                df_existing['time'] = pd.to_datetime(df_existing['time'], errors='coerce')
                # NaT olanları temizle
                df_existing = df_existing.dropna(subset=['time'])
                
                # Eğer timezone bilgisi yoksa UTC varsay
                if df_existing['time'].dt.tz is None:
                    df_existing['time'] = df_existing['time'].dt.tz_localize('UTC')
                else:
                    df_existing['time'] = df_existing['time'].dt.tz_convert('UTC')
                    
            except Exception as e:
                print(f"CSV okuma hatası: {e}")
                return "CSV okuma hatası."
        else:
            print("CSV dosyası bulunamadı, yeni oluşturulacak.")
            df_existing = pd.DataFrame(columns=[
                "time", "latitude", "longitude", "depth", "mag", "place", "type"
            ])

        # 2. API'den Veri Çek
        response = requests.get(API_URL, timeout=10)
        if response.status_code != 200:
            print(f"API Hatası: {response.status_code}")
            return f"API Hatası: {response.status_code}"
            
        data = response.json()
        if not data.get("status"):
            print("API durumu başarısız.")
            return "API veri döndürmedi."

        earthquakes = data["result"]
        new_records = []
        
        # En son kaydedilen deprem zamanını bul (eğer varsa)
        if not df_existing.empty:
            last_recorded_time = df_existing['time'].max()
        else:
            last_recorded_time = pd.Timestamp.min.tz_localize('UTC')

        print(f"Son kayıtlı deprem tarihi (UTC): {last_recorded_time}")

        count = 0
        for eq in earthquakes:
            # API Tarih formatı: "2024.11.22 14:15:00" -> ISO'ya çevirmemiz lazım
            # Genelde format: YYYY.MM.DD HH:MM:SS
            date_str = eq.get("date_time")
            if not date_str:
                continue
                
            try:
                # "." ları "-" yapıp parse edelim
                # Örnek format: 2024.11.22 14:15:00
                formatted_date_str = date_str.replace(".", "-")
                # Bu tarih Türkiye saati (Local) kabul ediyoruz.
                # Türkiye saati UTC+3
                eq_time_naive = pd.to_datetime(formatted_date_str)
                # Localize to Turkey time (Fixed offset +0300 for simplicity or use pytz if available, 
                # but let's assume +0300 for modern TRT)
                # Using pd.Timedelta for manual adjustment to UTC if timezone lib is issue, 
                # but pandas usually handles it. Let's try explicit offset.
                eq_time = eq_time_naive.tz_localize('Etc/GMT-3') # GMT-3 is UTC+3
                eq_time_utc = eq_time.tz_convert('UTC')
                
            except Exception as e:
                # print(f"Tarih parse hatası: {e}")
                continue

            # Eğer bu deprem son kaydedilenden daha yeniyse listeye al
            if eq_time_utc > last_recorded_time:
                # CSV formatına uygun kayıt oluştur
                
                record = {
                    "time": eq_time_utc, # Datetime objesi (UTC)
                    "latitude": eq.get("geojson", {}).get("coordinates", [0, 0])[1],
                    "longitude": eq.get("geojson", {}).get("coordinates", [0, 0])[0],
                    "depth": eq.get("depth"),
                    "mag": eq.get("mag"),
                    "magType": "ml", # Varsayılan
                    "place": eq.get("title"),
                    "type": "earthquake",
                    "status": "automatic" # API'den gelenler genelde otomatiktir
                }
                new_records.append(record)
                count += 1

        if not new_records:
            print("Yeni deprem verisi yok.")
            return "Veriler güncel."

        # 3. Yeni Kayıtları Ekle
        df_new = pd.DataFrame(new_records)
        
        # Mevcut sütun yapısına uydur (Eksik sütunları NaN yap)
        df_updated = pd.concat([df_existing, df_new], ignore_index=True)
        
        # Tarihe göre sırala (Yeniden eskiye)
        df_updated = df_updated.sort_values("time", ascending=False)

        # 4. Dosyayı Kaydet
        # Tarih formatını ISO 8601'e geri çevir (CSV uyumu için)
        # Orijinal CSV formatı: 2024-10-04T05:57:19.724Z
        # Pandas to_csv datetime'ı varsayılan olarak ISO formatında yazar ama Z eklemez.
        # Formatı manuel ayarlayalım:
        
        # UTC timezone bilgisini düşürüp string formatlayalım ki CSV temiz olsun
        # Ancak okurken tekrar UTC kabul edeceğiz.
        
        # df_updated['time'] datetime64[ns, UTC] tipinde.
        # Bunu string'e çevirirken formatlayalım.
        
        # Geçici bir kolon yapıp formatlayalım
        df_to_save = df_updated.copy()
        df_to_save['time'] = df_to_save['time'].dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        df_to_save.to_csv(CSV_PATH, index=False)
        print(f"{count} yeni deprem eklendi.")
        return f"{count} yeni deprem eklendi."

    except Exception as e:
        print(f"Veri güncelleme hatası: {e}")
        return f"Hata: {e}"

if __name__ == "__main__":
    fetch_and_update_data()
