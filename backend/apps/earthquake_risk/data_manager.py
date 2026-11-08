import requests
import pandas as pd
from datetime import datetime
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data" / "query.csv"
# Kandilli's bare /live endpoint silently caps at 50 records — during an active
# sequence (aftershocks) that window can fill up in well under a day, so anything
# older than the 50 most recent events is lost forever between syncs. Asking for
# a much larger limit still only covers a rolling ~24-48h window (the API has no
# real historical pagination), which is why USGS is used below as a backfill for
# whatever gap remains.
API_URL = "https://api.orhanaydogdu.com.tr/deprem/kandilli/live"
KANDILLI_FETCH_LIMIT = 1000

# Fallback source to cover any gap Kandilli's rolling window can't reach (e.g. the
# backend was offline for a few days). USGS has real starttime/endtime pagination,
# but only catalogs earthquakes above roughly M4 in this region, so it's used only
# to recover significant events, not to mirror every small local tremor.
USGS_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
USGS_MIN_MAGNITUDE = 4.0
TURKEY_BBOX = {"minlatitude": 34.0, "maxlatitude": 43.5, "minlongitude": 24.5, "maxlongitude": 46.5}


def _fetch_usgs_gap(start_time_utc, end_time_utc):
    """Backfills significant (M>=4) events USGS recorded in [start, end] UTC."""
    if start_time_utc >= end_time_utc:
        return []

    params = {
        "format": "geojson",
        "starttime": start_time_utc.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime": end_time_utc.strftime("%Y-%m-%dT%H:%M:%S"),
        "minmagnitude": USGS_MIN_MAGNITUDE,
        **TURKEY_BBOX,
    }
    try:
        response = requests.get(USGS_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"USGS gap-fill sorgusu basarisiz: {e}")
        return []

    records = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates", [0, 0, 0])
        time_ms = props.get("time")
        if time_ms is None:
            continue
        records.append({
            "time": pd.to_datetime(time_ms, unit="ms", utc=True),
            "latitude": coords[1],
            "longitude": coords[0],
            "depth": coords[2] if len(coords) > 2 else None,
            "mag": props.get("mag"),
            "magType": props.get("magType") or "mw",
            "place": props.get("place"),
            "type": "earthquake",
            "status": "usgs_gapfill",
        })
    return records


def fetch_and_update_data():
    """
    Kandilli API'den son depremleri çeker ve data/query.csv dosyasına ekler.
    Sadece yeni depremleri ekler (tarih ve büyüklük kontrolü ile).
    Kandilli'nin döndürdüğü pencere son kaydedilen depreme kadar ulaşmıyorsa
    (ör. backend birkaç gün kapalıydı), aradaki büyük (M>=4) depremleri USGS'den
    tamamlayarak veri kaybını en aza indirir.
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

        # 2. API'den Veri Çek (buyuk limit: Kandilli'nin varsayilani sadece 50 kayit donduruyor)
        response = requests.get(API_URL, params={"limit": KANDILLI_FETCH_LIMIT}, timeout=15)
        if response.status_code != 200:
            print(f"API Hatası: {response.status_code}")
            return f"API Hatası: {response.status_code}"

        data = response.json()
        if not data.get("status"):
            print("API durumu başarısız.")
            return "API veri döndürmedi."

        earthquakes = data["result"]
        new_records = []
        parsed_times_utc = []

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

            parsed_times_utc.append(eq_time_utc)

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

        # 2b. Kandilli penceresi son kaydedilen depreme kadar ulaşmadıysa
        # (ör. backend birkaç gündür kapalıydı ve bu pencerede o kadar geriye
        # gidilemiyor), aradaki boşluğu USGS'den M>=4 depremlerle doldur.
        now_utc = pd.Timestamp.now(tz="UTC")
        oldest_fetched_time = min(parsed_times_utc) if parsed_times_utc else now_utc
        usgs_records = []
        if oldest_fetched_time > last_recorded_time:
            gap_start = last_recorded_time
            gap_end = min(oldest_fetched_time, now_utc)
            print(f"Kandilli penceresi {oldest_fetched_time} tarihine kadar geriye gidiyor; "
                  f"{gap_start} - {gap_end} arası USGS ile tamamlanacak.")
            usgs_records = _fetch_usgs_gap(gap_start, gap_end)
            if usgs_records:
                print(f"USGS'den {len(usgs_records)} tamamlayici (M>=4) kayit bulundu.")

        combined_new = new_records + usgs_records
        if not combined_new:
            print("Yeni deprem verisi yok.")
            return "Veriler güncel."

        # Aynı depreme iki kaynaktan (Kandilli + USGS) çift kayıt düşmesini önle:
        # zaman (10 dk içinde) + konum (~25 km) yakınlığına göre tekilleştir.
        deduped = []
        for record in combined_new:
            is_duplicate = False
            for existing in deduped:
                same_source_window = abs((record["time"] - existing["time"]).total_seconds()) <= 600
                if not same_source_window:
                    continue
                dlat = abs(record["latitude"] - existing["latitude"])
                dlon = abs(record["longitude"] - existing["longitude"])
                if dlat <= 0.25 and dlon <= 0.25:
                    is_duplicate = True
                    break
            if not is_duplicate:
                deduped.append(record)
        combined_new = deduped
        count = sum(1 for r in combined_new if r.get("status") != "usgs_gapfill")
        usgs_count = sum(1 for r in combined_new if r.get("status") == "usgs_gapfill")

        # 3. Yeni Kayıtları Ekle
        df_new = pd.DataFrame(combined_new)
        
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
        message = f"{count} yeni deprem eklendi (Kandilli)."
        if usgs_count:
            message += f" +{usgs_count} tamamlayici kayit (USGS gap-fill)."
        print(message)
        return message

    except Exception as e:
        print(f"Veri güncelleme hatası: {e}")
        return f"Hata: {e}"

if __name__ == "__main__":
    fetch_and_update_data()
