from typing import Optional

from .models import SOSRecord
from .sample_data import get_sample_sos_records


class SOSRepository:
    # Only place the SOS panel's data source is decided. Today it returns
    # static sample data; once the mobile app and a persistence layer exist,
    # only this class needs to change (e.g. read from the FastAPI /api/sos
    # endpoints or a database) and render_sos_screen keeps working as-is.

    def __init__(self):
        self._records = get_sample_sos_records()

    def list_all(self) -> list[SOSRecord]:
        return list(self._records)

    def get_by_id(self, record_id: str) -> Optional[SOSRecord]:
        return next((record for record in self._records if record.id == record_id), None)
