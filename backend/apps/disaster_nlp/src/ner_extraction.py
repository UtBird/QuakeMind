import json
import re
import threading
import unicodedata

from transformers import pipeline
import torch
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from pathlib import Path
from huggingface_hub import snapshot_download

from src.tr_locations import PROVINCES, PROVINCE_TO_DISTRICTS, PROVINCE_COORDS, DISTRICT_COORDS


PLACE_TYPES = {"city", "town", "village", "suburb", "quarter", "neighbourhood", "road", "square"}
POI_TYPES = {"university", "hospital", "college", "school", "amenity", "building"}
LOCATION_ENTITY_GROUPS = {"ADDR", "CITY"}
ADDRESS_HINTS = {
    "mah", "mahallesi", "mahalle", "sokak", "sk", "cadde", "caddesi", "cd",
    "bulvar", "bulvari", "bulvarı", "site", "sitesi", "apartman", "apartmani",
    "apartmanı", "apt", "blok", "no", "merkez", "ilce", "ilçe", "koy", "köy",
    "meydan", "meydanı", "yolu", "yol"
}
POI_HINTS = {"universitesi", "üniversitesi", "universite", "üniversite", "hastanesi", "hastane", "kampusu", "kampüsü"}
NOISE_WORDS = {
    "acil", "yardim", "yardım", "lutfen", "lütfen", "enkaz", "altinda", "altında",
    "ses", "geliyor", "var", "bina", "coktu", "çöktü", "yikildi", "yıkıldı",
    "kapali", "kapalı", "lazim", "lazım", "ihtiyaci", "ihtiyacı", "gerekiyor",
    "yardımedin", "yardimedin", "trapped", "help", "emergency"
}
STOP_FALLBACK_TOKENS = ADDRESS_HINTS | NOISE_WORDS

# J-13: Nominatim'e giden sorgu varyasyon sayisinin ust siniri (eskiden bir
# konum icin 23'e kadar cikabiliyordu -- her biri bir ag gidis-donusu, ilk
# (onbelleksiz) sorgu icin olculen 7-10 sn, en kotu durumda ~28 sn).
MAX_GEOCODE_QUERIES = 4


# Geocoding onbellegi -- olculdu: uctan uca process_tweet 7,28sn suruyordu ve
# bunun 6,45sn'si (%89) Nominatim'i beklemekti. Tek bir metin 23 sorgu adayi
# uretebiliyor ve her sorgu RateLimiter'in 1,2sn'lik gecikmesi ardinda canli
# HTTP yapiyor; hicbiri tutmazsa 23 x 1,2sn ~ 28sn. Onbellek olmadigi icin
# AYNI metin ikinci kez geldiginde bedel bastan odeniyordu.
#
# Onbellek sorgu METNINE gore anahtarlanir ve BASARISIZ sonuclari da saklar
# (asil maliyet zaten tutmayan sorgularin taranmasi). Diske yazildigi icin
# surec yeniden baslatildiginda da korunur. Sonuclar bit-bit ayni oldugu icin
# bu degisiklik NLP ciktilarini DEGISTIRMEZ -- yalnizca ayni sonuca daha hizli
# ulasir.
_GEOCACHE_PATH = Path(__file__).resolve().parents[1] / "data" / "geocode_cache.json"
_geocache_lock = threading.Lock()
_geocache: "dict | None" = None


def _load_geocache():
    global _geocache
    if _geocache is None:
        try:
            _geocache = json.loads(_GEOCACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            _geocache = {}
    return _geocache


def _geocache_get(query):
    with _geocache_lock:
        cache = _load_geocache()
        return cache.get(query, "__MISS__")


def _geocache_put(query, value):
    with _geocache_lock:
        cache = _load_geocache()
        cache[query] = value
        try:
            _GEOCACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            _GEOCACHE_PATH.write_text(
                json.dumps(cache, ensure_ascii=False), encoding="utf-8"
            )
        except Exception:
            # Onbellek yazilamiyorsa (salt-okunur kurulum, disk dolu) bellekte
            # tutmaya devam et -- geocoding'in kendisi calismaya devam etmeli.
            pass


class LocationExtractor:
    def __init__(self, model_name="yhaslan/turkish-earthquake-tweets-ner"):
        device = 0 if torch.cuda.is_available() else -1
        
        import os
        os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
        
        try:
            # Önce modelin lokal cache'de (daha önce indirilmiş) olup olmadığını kontrol et
            model_path = snapshot_download(repo_id=model_name, local_files_only=True)
        except Exception:
            try:
                # Eğer lokalde yoksa, o zaman internetten indirmeyi dene
                local_dir = Path(__file__).resolve().parents[2] / "models" / "ner"
                local_dir.mkdir(parents=True, exist_ok=True)
                snapshot_download(
                    repo_id=model_name,
                    local_dir=str(local_dir),
                    allow_patterns=["config.json", "pytorch_model.bin", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "vocab.txt"],
                    local_files_only=False
                )
                model_path = str(local_dir)
            except Exception as e:
                print(f"Warning: Failed to snapshot_download NER model from network: {e}")
                model_path = model_name

        # Pipeline'ı her zaman lokal modda (internete çıkmadan) başlat ki timeoutlara takılmasın
        try:
            self.ner = pipeline("token-classification", model=model_path, aggregation_strategy="simple", device=device, model_kwargs={"use_safetensors": False, "local_files_only": True})
        except Exception:
            # En kötü senaryo, normal başlat
            self.ner = pipeline("token-classification", model=model_path, aggregation_strategy="simple", device=device, model_kwargs={"use_safetensors": False})
        
        # Geopy setup with OpenStreetMap
        self.geolocator = Nominatim(user_agent="disaster_nlp_app", timeout=5)
        self.geocode = RateLimiter(self.geolocator.geocode, min_delay_seconds=1.2)
        
    def extract_entities(self, text):
        """
        Extracts named entities from the text (Location, Organization, etc.)
        """
        if not text:
            return []
            
        try:
            return self.ner(text[:512])
        except Exception:
            return []

    def _normalize_location_text(self, text):
        if not text:
            return ""

        text = re.sub(r"\s+", " ", str(text)).strip(" ,.-")
        text = re.sub(r"\bno\s*[:.]?\s*\d+\b", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\b\d{5}\b", "", text)
        return re.sub(r"\s+", " ", text).strip(" ,.-")

    def _tokenize(self, text):
        # J-13 yan-duzeltmesi: Turkce noktasiz 'ı' (U+0131) NFKD altinda 'i'ye
        # AYRISMAZ (bilesik bir aksanli harf degil, ayri bir temel harf) --
        # bu yuzden ASCII yazilmis "pazarcik" ile dogru yazilmis "Pazarcık"
        # asla eslesmiyordu (_extract_admin_hints ilce/il eslestirmesini
        # kirıyordu, hem eski Nominatim-sorgu yolu hem yeni yerel geocode
        # icin). Digerleri (ç,ğ,ö,ş,ü) zaten NFKD ile dogru katlaniyor.
        normalized_text = str(text).casefold().replace("ı", "i")
        normalized_text = unicodedata.normalize("NFKD", normalized_text)
        normalized_text = "".join(char for char in normalized_text if not unicodedata.combining(char))
        normalized_text = re.sub(r"[^\w\s]", " ", normalized_text)
        return [token for token in re.split(r"\s+", normalized_text) if token]

    def _normalize_for_match(self, text):
        return " ".join(self._tokenize(text))

    def _ascii_fallback_text(self, text):
        normalized_text = unicodedata.normalize("NFKD", str(text))
        normalized_text = "".join(char for char in normalized_text if not unicodedata.combining(char))
        return re.sub(r"\s+", " ", normalized_text).strip()

    def _meaningful_tokens(self, text):
        tokens = self._tokenize(text)
        return [token for token in tokens if token not in STOP_FALLBACK_TOKENS and len(token) > 1]

    def _contains_phrase(self, haystack, phrase):
        haystack_tokens = self._tokenize(haystack)
        phrase_tokens = self._tokenize(phrase)
        if not haystack_tokens or not phrase_tokens:
            return False

        haystack_joined = " ".join(haystack_tokens)
        phrase_joined = " ".join(phrase_tokens)
        pattern = rf"(?<!\w){re.escape(phrase_joined)}(?!\w)"
        return re.search(pattern, haystack_joined) is not None

    def _extract_admin_hints(self, text):
        province = None
        district = None

        for province_name in sorted(PROVINCES, key=len, reverse=True):
            if self._contains_phrase(text, province_name):
                province = province_name
                break

        if province:
            district_names = PROVINCE_TO_DISTRICTS.get(province, [])
            for district_name in sorted(district_names, key=len, reverse=True):
                if self._contains_phrase(text, district_name):
                    district = district_name
                    break
        else:
            for province_name, district_names in PROVINCE_TO_DISTRICTS.items():
                for district_name in sorted(district_names, key=len, reverse=True):
                    if self._contains_phrase(text, district_name):
                        district = district_name
                        province = province_name
                        break
                if district:
                    break

        return {
            "province": province,
            "district": district,
        }

    def _looks_like_poi_query(self, text):
        tokens = set(self._tokenize(text))
        return any(token in tokens for token in self._tokenize(" ".join(POI_HINTS)))

    def _sanitize_candidate(self, candidate):
        candidate = self._normalize_location_text(candidate)
        raw_tokens = [token for token in re.split(r"\s+", candidate) if token]
        normalized_tokens = [self._normalize_for_match(token) for token in raw_tokens]

        while normalized_tokens and normalized_tokens[-1] in NOISE_WORDS:
            normalized_tokens.pop()
            raw_tokens.pop()

        sanitized_raw_tokens = []
        for raw_token, normalized_token in zip(raw_tokens, normalized_tokens):
            if normalized_token in NOISE_WORDS and sanitized_raw_tokens:
                break
            sanitized_raw_tokens.append(raw_token)

        return self._normalize_location_text(" ".join(sanitized_raw_tokens))

    def _is_low_quality_candidate(self, candidate):
        candidate = self._sanitize_candidate(candidate)
        tokens = self._tokenize(candidate)
        if not tokens:
            return True

        useful_tokens = self._meaningful_tokens(candidate)
        if not useful_tokens:
            return True

        return False

    def extract_location_candidates(self, text, entities=None):
        if entities is None:
            entities = self.extract_entities(text)

        location_entities = [
            ent for ent in entities
            if ent.get("entity_group") in LOCATION_ENTITY_GROUPS and ent.get("word")
        ]
        if not location_entities:
            return []

        location_entities = sorted(location_entities, key=lambda ent: ent.get("start", 0))

        city_parts = []
        addr_parts = []
        ordered_parts = []
        for entity in location_entities:
            normalized = self._normalize_location_text(entity["word"])
            if not normalized:
                continue
            ordered_parts.append(normalized)
            if entity["entity_group"] == "CITY":
                city_parts.append(normalized)
            else:
                addr_parts.append(normalized)

        city_text = self._normalize_location_text(" ".join(city_parts))
        addr_text = self._normalize_location_text(" ".join(addr_parts))
        joined_text = self._normalize_location_text(" ".join(ordered_parts))
        admin_hints = self._extract_admin_hints(text)
        province_hint = admin_hints["province"]
        district_hint = admin_hints["district"]

        candidates = []
        for candidate in [
            f"{addr_text}, {district_hint}, {province_hint}" if addr_text and district_hint and province_hint else "",
            f"{district_hint}, {province_hint}" if district_hint and province_hint else "",
            f"{addr_text}, {province_hint}" if addr_text and province_hint else "",
            f"{addr_text}, {city_text}" if addr_text and city_text else "",
            f"{city_text} {addr_text}" if addr_text and city_text else "",
            joined_text,
            addr_text,
            district_hint,
            province_hint,
            city_text,
        ]:
            candidate = self._sanitize_candidate(candidate)
            if candidate and candidate not in candidates and not self._is_low_quality_candidate(candidate):
                candidates.append(candidate)

        return candidates

    def _is_valid_location_match(self, location, query):
        raw = location.raw or {}
        display_name = self._normalize_for_match(raw.get("display_name") or "")
        query_tokens = self._meaningful_tokens(query)

        if not query_tokens:
            return False

        matched_tokens = [token for token in query_tokens if token in display_name]
        if not matched_tokens:
            return False

        required_matches = 1 if len(query_tokens) == 1 else min(2, len(query_tokens))
        if len(matched_tokens) < required_matches:
            return False

        raw_type = raw.get("type")
        raw_address_type = raw.get("addresstype")
        if self._looks_like_poi_query(query) and (raw_type in POI_TYPES or raw_address_type in POI_TYPES):
            return True

        if raw_type not in PLACE_TYPES and raw_address_type not in PLACE_TYPES and len(matched_tokens) < len(query_tokens):
            return False

        return True

    def _score_location(self, location, query):
        score = 0
        raw = location.raw or {}

        if raw.get("type") in PLACE_TYPES:
            score += 5
        if raw.get("addresstype") in PLACE_TYPES:
            score += 4
        if raw.get("type") in POI_TYPES:
            score += 4
        if raw.get("addresstype") in POI_TYPES:
            score += 3
        if raw.get("address", {}).get("country_code") == "tr":
            score += 3

        display_name = self._normalize_for_match(raw.get("display_name") or "")
        query_tokens = [token for token in self._tokenize(query) if token not in {"turkey", "türkiye"}]
        score += sum(1 for token in query_tokens if token in display_name)

        return score

    def _pick_best_location(self, locations, query):
        if not locations:
            return None

        ranked_locations = sorted(
            locations,
            key=lambda location: self._score_location(location, query),
            reverse=True,
        )
        return ranked_locations[0]

    def _query_location(self, query):
        try:
            locations = self.geocode(
                query,
                exactly_one=False,
                limit=5,
                addressdetails=True,
                country_codes="tr",
                language="tr",
            )
        except Exception:
            return None

        if not locations:
            return None

        best_location = self._pick_best_location(locations, query)
        if not best_location or not self._is_valid_location_match(best_location, query):
            return None

        return best_location

    def _query_latlon(self, query):
        """_query_location'in onbellekli sarmalayicisi. Onbellek geopy
        Location nesnesini degil, cagiranin zaten kullandigi tek seyi
        (enlem/boylam ciftini) saklar; BASARISIZLIK da saklanir cunku asil
        maliyet tutmayan sorgulari taramaktir."""
        cached = _geocache_get(query)
        if cached != "__MISS__":
            return cached

        location = self._query_location(query)
        value = [location.latitude, location.longitude] if location else None
        _geocache_put(query, value)
        return value

    def _build_queries(self, location_text, raw_text=None):
        queries = []
        normalized = self._normalize_location_text(location_text)
        if not normalized:
            return queries

        admin_hints = self._extract_admin_hints(raw_text or location_text)
        province_hint = admin_hints["province"]
        normalized_raw_text = (raw_text or "").lower()
        if "merkez" in normalized_raw_text and "merkez" not in normalized.lower():
            queries.append(f"{normalized} merkez, Turkey")

        queries.append(f"{normalized}, Turkey")

        if province_hint and normalized.startswith(province_hint):
            remainder = normalized[len(province_hint):].strip(" ,-")
            if remainder:
                queries.append(f"{remainder}, {province_hint}, Turkey")

        if province_hint and province_hint not in normalized:
            queries.append(f"{normalized}, {province_hint}, Turkey")

        words = normalized.split()
        while len(words) > 1:
            words.pop()
            reduced = " ".join(words).strip()
            if reduced:
                queries.append(f"{reduced}, Turkey")

        # J-13: en oncelikli MAX_GEOCODE_QUERIES varyasyonu tut (siralama
        # zaten en-spesifikten en-genele dogru); ascii yedeklerini de
        # yalniz bu kesilmis kumeye ekle, tum listeye degil.
        seen = []
        for query in queries:
            if query not in seen:
                seen.append(query)
        seen = seen[:MAX_GEOCODE_QUERIES]

        ascii_queries = []
        for query in seen:
            ascii_query = self._ascii_fallback_text(query)
            if ascii_query and ascii_query != query and ascii_query not in seen:
                ascii_queries.append(ascii_query)

        seen.extend(ascii_queries)
        return seen[:MAX_GEOCODE_QUERIES]

    def _local_geocode(self, raw_text):
        """J-13: Nominatim'e hic gitmeden yerel il/ilce koordinat sozlugunden
        aninda sonuc dondurur. Il merkezi/ilce merkezi hassasiyetinde --
        sokak duzeyinde degil, ama offline modda ya da Nominatim'in yavas/
        ban riskli oldugu durumlarda "konum bulunamadi" yerine kaba da olsa
        bir bolge dondurmeyi saglar. `_extract_admin_hints` zaten aksan-
        duyarsiz ifade eslestirmesi yapiyor, burada tekrar kullanilir."""
        if not raw_text:
            return None
        hints = self._extract_admin_hints(raw_text)
        province, district = hints.get("province"), hints.get("district")
        if province and district:
            coords = DISTRICT_COORDS.get((province, district))
            if coords:
                return coords
        if province:
            coords = PROVINCE_COORDS.get(province)
            if coords:
                return coords
        return None

    def get_coordinates(self, location_text, raw_text=None):
        """
        Converts a location string (e.g., "Hatay Antakya") to GPS coordinates.

        J-13 duzeltmesi: yerel il/ilce sozlugu ONCE denenir (ag gerektirmez,
        aninda doner); Nominatim yalniz yerel sozlukte eslesme yoksa (ör.
        bilinmeyen/kucuk bir mahalle) son care olarak devreye girer.
        """
        candidates = location_text if isinstance(location_text, list) else [location_text]
        first_candidate = candidates[0] if candidates else None

        local_coords = self._local_geocode(raw_text or first_candidate)
        if local_coords:
            return list(local_coords), first_candidate

        # Adaylar buyuk olcude ortusen sorgular uretiyor ("Antakya, Turkey"
        # yedi adaydan besinde cikiyor) ve dedupe eskiden yalnizca TEK bir
        # adayin sorgu listesi icinde yapiliyordu -- yani ayni basarisiz sorgu
        # ayni metin icinde defalarca aga gidiyordu. Sorgu ADAYLAR ARASINDA da
        # tekrarlanmaz. Sonuc degismez: tutan bir sorgu zaten aninda donerdi,
        # dolayisiyla atlanan her sorgu daha once BASARISIZ olmus bir sorgudur.
        tried = set()
        for candidate in candidates:
            for query in self._build_queries(candidate, raw_text=raw_text):
                if query in tried:
                    continue
                tried.add(query)
                latlon = self._query_latlon(query)
                if latlon:
                    return latlon, candidate

        return None, None

if __name__ == "__main__":
    extractor = LocationExtractor()
    sample = "Hatay antakya cumhuriyet caddesi bina yıkıldı acil yardım"
    entities = extractor.extract_entities(sample)
    print("Entities:", entities)
    
    # Extract just the locations (if model labels them as LOC)
    locs = [ent['word'] for ent in entities if 'LOC' in ent['entity_group']]
    if locs:
        full_loc = " ".join(locs)
        coords = extractor.get_coordinates(full_loc)
        print(f"Address: {full_loc} -> Coords: {coords}")
