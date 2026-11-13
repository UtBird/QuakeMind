from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class SOSType(str, Enum):
    """Extend with new members as new SOS categories are defined; no other code needs to change."""

    ENKAZ_ALTINDA = "Enkaz Altındayım"
    ACIL_SAGLIK = "Acil Sağlık"
    GIDA_IHTIYACI = "Gıda İhtiyacı"
    SU_IHTIYACI = "Su İhtiyacı"
    BARINMA = "Barınma"
    KURTARMA_TALEBI = "Kurtarma Talebi"
    DIGER = "Diğer"


class SOSPriority(str, Enum):
    KRITIK = "Kritik"
    YUKSEK = "Yüksek"
    ORTA = "Orta"
    DUSUK = "Düşük"


class SOSStatus(str, Enum):
    BEKLEMEDE = "Beklemede"
    INCELENIYOR = "İnceleniyor"
    YONLENDIRILDI = "Yönlendirildi"
    COZULDU = "Çözüldü"
    IPTAL_EDILDI = "İptal Edildi"


@dataclass
class SOSRecord:
    # Field names mirror what the mobile app's SOS payload already carries
    # (userId, message, latitude/longitude, receivedAt in fastapi_app.py) so a
    # future real data source can populate this model without renaming fields.
    id: str
    user_name: str
    sos_type: SOSType
    description: str
    location_label: str
    priority: SOSPriority
    status: SOSStatus
    created_at: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
