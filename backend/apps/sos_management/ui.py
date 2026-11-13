import pandas as pd
import streamlit as st

from .models import SOSPriority, SOSRecord, SOSStatus, SOSType
from .repository import SOSRepository
from .service import filter_records, sort_by_date


@st.cache_resource
def _get_repository() -> SOSRepository:
    return SOSRepository()


def render_sos_screen():
    st.markdown(
        """
        <style>
        .sos-panel {
            background: linear-gradient(180deg, #2c0b0b 0%, #3f1212 100%);
            color: #f2f5f7;
            border-radius: 16px;
            padding: 1rem 1.2rem;
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sos-panel"><h1>🆘 SOS Yönetimi</h1>'
        "<p>Mobil uygulamadan gelecek acil yardım çağrılarının listelendiği, "
        "filtrelendiği ve önceliklendirildiği yönetim modülü. Şu an örnek "
        "verilerle çalışıyor; mobil entegrasyon tamamlandığında bu ekran aynı "
        "yapıyla gerçek kayıtları gösterecek şekilde tasarlandı.</p></div>",
        unsafe_allow_html=True,
    )

    repository = _get_repository()
    all_records = repository.list_all()

    search_col, status_col, type_col, priority_col, sort_col = st.columns([2, 1.4, 1.6, 1.2, 1.2])
    search_text = search_col.text_input(
        "Ara", placeholder="Kullanıcı, açıklama veya konum ara...", key="sos_search"
    )
    status_filter = status_col.multiselect(
        "Durum", options=list(SOSStatus), format_func=lambda s: s.value, key="sos_status_filter"
    )
    type_filter = type_col.multiselect(
        "SOS Türü", options=list(SOSType), format_func=lambda t: t.value, key="sos_type_filter"
    )
    priority_filter = priority_col.multiselect(
        "Öncelik", options=list(SOSPriority), format_func=lambda p: p.value, key="sos_priority_filter"
    )
    sort_order = sort_col.selectbox(
        "Tarihe Göre Sırala", ["En Yeni", "En Eski"], key="sos_sort_order"
    )

    filtered = filter_records(
        all_records,
        search_text=search_text,
        statuses=status_filter,
        sos_types=type_filter,
        priorities=priority_filter,
    )
    filtered = sort_by_date(filtered, ascending=(sort_order == "En Eski"))

    metric_cols = st.columns(4)
    metric_cols[0].metric("Toplam Kayıt", len(all_records))
    metric_cols[1].metric("Filtrelenen", len(filtered))
    metric_cols[2].metric(
        "Kritik Öncelik", sum(1 for r in filtered if r.priority == SOSPriority.KRITIK)
    )
    metric_cols[3].metric(
        "Beklemede", sum(1 for r in filtered if r.status == SOSStatus.BEKLEMEDE)
    )

    st.markdown("---")

    if not filtered:
        st.info("Filtrelere uyan SOS kaydı bulunamadı.")
        return

    table_df = pd.DataFrame(
        [
            {
                "ID": record.id,
                "Kullanıcı": record.user_name,
                "SOS Türü": record.sos_type.value,
                "Öncelik": record.priority.value,
                "Durum": record.status.value,
                "Konum": record.location_label,
                "Oluşturulma Tarihi": record.created_at.strftime("%d.%m.%Y %H:%M"),
            }
            for record in filtered
        ]
    )

    selection = st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="sos_table",
    )

    selected_rows = selection.selection["rows"] if selection and selection.selection else []
    selected_record = filtered[selected_rows[0]] if selected_rows else filtered[0]

    st.subheader("Detay")
    detail_col, map_col = st.columns([1.3, 1])
    with detail_col:
        _render_detail(selected_record)
    with map_col:
        _render_map(filtered, selected_record)


def _render_detail(record: SOSRecord):
    detail_col1, detail_col2 = st.columns(2)
    with detail_col1:
        st.write(f"**ID:** {record.id}")
        st.write(f"**Kullanıcı:** {record.user_name}")
        st.write(f"**SOS Türü:** {record.sos_type.value}")
        st.write(f"**Konum:** {record.location_label}")
        if record.latitude is not None and record.longitude is not None:
            st.write(f"**Koordinat:** {record.latitude:.4f}, {record.longitude:.4f}")
    with detail_col2:
        st.write(f"**Oluşturulma Tarihi:** {record.created_at.strftime('%d.%m.%Y %H:%M')}")
        st.write(f"**Durum:** {record.status.value}")
        _render_priority_badge(record.priority)

    st.write("**Açıklama:**")
    st.write(record.description)


def _render_priority_badge(priority: SOSPriority):
    label = f"Öncelik: {priority.value}"
    if priority == SOSPriority.KRITIK:
        st.error(label)
    elif priority == SOSPriority.YUKSEK:
        st.warning(label)
    elif priority == SOSPriority.ORTA:
        st.info(label)
    else:
        st.success(label)


_PRIORITY_MARKER_COLORS = {
    SOSPriority.KRITIK: "red",
    SOSPriority.YUKSEK: "orange",
    SOSPriority.ORTA: "blue",
    SOSPriority.DUSUK: "green",
}


def _render_map(records: list[SOSRecord], selected_record: SOSRecord):
    geolocated = [r for r in records if r.latitude is not None and r.longitude is not None]
    if not geolocated:
        st.info("Haritada gösterilecek konum bilgisi bulunamadı.")
        return

    import folium
    from streamlit_folium import st_folium

    has_selected_coords = selected_record.latitude is not None and selected_record.longitude is not None
    center = (
        (selected_record.latitude, selected_record.longitude)
        if has_selected_coords
        else (geolocated[0].latitude, geolocated[0].longitude)
    )
    fmap = folium.Map(location=center, zoom_start=7, tiles="CartoDB dark_matter")

    for record in geolocated:
        is_selected = record.id == selected_record.id
        folium.Marker(
            location=(record.latitude, record.longitude),
            tooltip=f"{record.id} - {record.sos_type.value}",
            popup=folium.Popup(_marker_popup_html(record), max_width=260),
            icon=folium.Icon(
                color=_PRIORITY_MARKER_COLORS[record.priority],
                icon="exclamation-sign" if is_selected else "info-sign",
            ),
        ).add_to(fmap)
        if is_selected:
            folium.CircleMarker(
                location=(record.latitude, record.longitude),
                radius=16,
                color="#f2f5f7",
                weight=2,
                fill=False,
            ).add_to(fmap)

    st_folium(fmap, height=320, use_container_width=True, key="sos_map", returned_objects=[])


def _marker_popup_html(record: SOSRecord) -> str:
    return (
        f"<b>{record.id}</b><br>"
        f"{record.sos_type.value} - {record.priority.value}<br>"
        f"{record.user_name}<br>"
        f"{record.location_label}"
    )
