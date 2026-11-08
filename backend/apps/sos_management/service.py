from typing import Iterable, Optional, Sequence

from .models import SOSPriority, SOSRecord, SOSStatus, SOSType


def filter_records(
    records: Sequence[SOSRecord],
    search_text: str = "",
    statuses: Optional[Iterable[SOSStatus]] = None,
    sos_types: Optional[Iterable[SOSType]] = None,
    priorities: Optional[Iterable[SOSPriority]] = None,
) -> list[SOSRecord]:
    status_set = set(statuses) if statuses else None
    type_set = set(sos_types) if sos_types else None
    priority_set = set(priorities) if priorities else None
    needle = _turkish_lower(search_text.strip())

    def matches(record: SOSRecord) -> bool:
        if status_set and record.status not in status_set:
            return False
        if type_set and record.sos_type not in type_set:
            return False
        if priority_set and record.priority not in priority_set:
            return False
        if needle and needle not in _searchable_text(record):
            return False
        return True

    return [record for record in records if matches(record)]


def _turkish_lower(text: str) -> str:
    # str.lower() turns "İ" into "i" + a combining dot above, which then
    # never matches a plain ASCII "i" typed by the user. Map the Turkish
    # dotted/dotless I pair explicitly before falling back to str.lower().
    return text.replace("İ", "i").replace("I", "ı").lower()


def _searchable_text(record: SOSRecord) -> str:
    return _turkish_lower(
        " ".join([record.user_name, record.description, record.location_label, record.sos_type.value])
    )


def sort_by_date(records: Sequence[SOSRecord], ascending: bool = False) -> list[SOSRecord]:
    return sorted(records, key=lambda record: record.created_at, reverse=not ascending)
