import webbrowser
import os
import json
import webbrowser
import os
import json
from pathlib import Path
import folium
from folium.plugins import MarkerCluster, HeatMap

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_FILE = BASE_DIR / "runtime" / "risk_map.html"

def generate_map(city_name, lat, lon, fault_points, fault_lines=None, geojson_paths=None, all_quakes_df=None, output_file=DEFAULT_OUTPUT_FILE):
    """
    Generates a focused map showing the city, its risk radius, and local earthquakes.
    Includes Heatmap, Fault Lines, and GeoJSON layers with improved aesthetics.
    """
    # 1. Temel Harita ve Katmanlar
    m = folium.Map(location=[lat, lon], zoom_start=8, tiles=None)
    
    # Farklı harita altlıkları ekle
    folium.TileLayer('CartoDB dark_matter', name='Koyu Mod (Varsayılan)').add_to(m)
    folium.TileLayer('OpenStreetMap', name='Aydınlık Mod').add_to(m)
    
    # 2. Hedef Şehir (Özel İkon)
    folium.Marker(
        [lat, lon],
        popup=f"<div style='font-size: 14px; font-weight: bold;'>{city_name}</div>",
        tooltip="Analiz Edilen Şehir",
        icon=folium.Icon(color="red", icon="info-sign", prefix='fa')
    ).add_to(m)

    # 3. Basit Fay Hatları Katmanı (Manuel Çizim)
    if fault_lines:
        fault_group = folium.FeatureGroup(name="Ana Fay Hatları (Basit)", show=False)
        for line in fault_lines:
            folium.PolyLine(
                line,
                color="#ff5722", # Daha canlı bir turuncu
                weight=2,
                opacity=0.6,
                tooltip="Ana Fay Hattı"
            ).add_to(fault_group)
        fault_group.add_to(m)

    # 4. Detaylı GeoJSON Fay Hatları
    if geojson_paths:
        for path in geojson_paths:
            if os.path.exists(path):
                name = os.path.basename(path).replace(".geojson", "").replace("_", " ").title()
                try:
                    # UTF-8 encoding ile oku
                    with open(path, "r", encoding="utf-8") as f:
                        geo_data = json.load(f)
                    
                    folium.GeoJson(
                        geo_data,
                        name=f"Detaylı Faylar: {name}",
                        zoom_on_click=False,
                        style_function=lambda x: {
                            'color': '#ff9800', 
                            'weight': 1.5, 
                            'opacity': 0.5
                        },
                        tooltip=folium.GeoJsonTooltip(fields=['name'], aliases=['Fay Adı:'], localize=True) if 'name' in str(geo_data).lower() else None
                    ).add_to(m)
                except Exception as e:
                    print(f"GeoJSON yüklenemedi ({path}): {e}")

    if all_quakes_df is not None and not all_quakes_df.empty:
        # 5. Isı Haritası (Heatmap) Katmanı
        heat_data = all_quakes_df[['latitude', 'longitude', 'mag']].values.tolist()
        HeatMap(
            heat_data,
            name="Deprem Yoğunluğu (Isı Haritası)",
            radius=15,
            max_zoom=10,
            min_opacity=0.4,
            gradient={0.4: 'blue', 0.65: 'lime', 1: 'red'}
        ).add_to(m)

        # 6. Geçmiş Depremler (Marker Cluster ile Gruplanmış)
        # MarkerCluster kullanarak kalabalığı önlüyoruz
        quake_cluster = MarkerCluster(name="Bölgesel Depremler (Kümelenmiş)").add_to(m)
        
        # Sadece 3.0 ve üzeri depremleri gösterelim (daha temiz görüntü için)
        significant_quakes = all_quakes_df[all_quakes_df['mag'] >= 3.0]
        
        for _, row in significant_quakes.iterrows():
            mag = row['mag']
            
            # Renk belirle
            color = "green"
            if mag >= 4.0: color = "orange"
            if mag >= 5.0: color = "red"
            if mag >= 6.0: color = "darkred"
            
            # Etki alanı yarıçapı
            impact_radius_km = int(10**(0.5 * mag - 1))
            impact_radius_m = impact_radius_km * 1000
            
            # Popup içeriği
            popup_html = f"""
            <div style="font-family: Arial; font-size: 12px;">
                <b>Tarih:</b> {row['time']}<br>
                <b>Büyüklük:</b> <span style="color: {color}; font-weight: bold;">{mag}</span><br>
                <b>Derinlik:</b> {row['depth']} km<br>
                <b>Tahmini Etki Yarıçapı:</b> ~{impact_radius_km} km
                <span id="impact_radius_m" hidden>{int(impact_radius_m)}</span>
            </div>
            """

            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=5,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(quake_cluster)

    # Katman Kontrolü
    folium.LayerControl(collapsed=False).add_to(m)

    # --- Custom JS: Tıklanan depremin etki alanını göster ---
    map_id = m.get_name()
    js_script = f"""
    <script>
    var currentImpactCircle = null;
    
    window.addEventListener('load', function() {{
        var map = {map_id};
        
        map.on('popupopen', function(e) {{
            if (currentImpactCircle) {{
                map.removeLayer(currentImpactCircle);
                currentImpactCircle = null;
            }}
            
            var content = e.popup.getContent();
            if (typeof content === 'string') {{
                var match = content.match(/id="impact_radius_m" hidden>(\\d+)</);
                if (match) {{
                    var radius = parseInt(match[1]);
                    var latlng = e.popup.getLatLng();
                    
                    currentImpactCircle = L.circle(latlng, {{
                        radius: radius,
                        color: 'red',
                        weight: 1,
                        fillColor: 'red',
                        fillOpacity: 0.1,
                        interactive: false
                    }}).addTo(map);
                }}
            }}
        }});

        map.on('popupclose', function(e) {{
            if (currentImpactCircle) {{
                map.removeLayer(currentImpactCircle);
                currentImpactCircle = null;
            }}
        }});
    }});
    </script>
    """
    m.get_root().html.add_child(folium.Element(js_script))

    # Haritayı kaydet
    output_path = Path(output_file)
    if not output_path.is_absolute():
        output_path = BASE_DIR / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    m.save(output_path)
    
    # Tarayıcıda aç
    webbrowser.open("file://" + os.path.realpath(output_path))
    return os.path.realpath(output_path)
