#!/usr/bin/env bash
# B0 is paketi: duzeltilmis kodla tatbikatin yeniden kosusu (makale/KALAN_ISLER_2026-09-27.md).
# Butun ciktilar tek klasore yazilir; her adimin suresi ve cikis kodu gunluge duser.
#
#   bash araclar_b0_kos.sh [cikti_klasoru]
#
# Onkosullar: apps/road_damage/models/*_p2_t42.pth (SHA-256 kunyelerle ayni),
# apps/road_damage/data/osm/roads.gpkg (araclar_yerel_osm_kur.py).
set -u
cd "$(dirname "$0")"
PY=venv/Scripts/python.exe
[ -x "$PY" ] || PY=venv/bin/python
OUT="${1:-benchmark/reports/tatbikat_b0}"
mkdir -p "$OUT"
LOG="$OUT/gunluk.txt"
ALANLAR=apps/road_damage/data/tatbikat_alanlari.json
SEC=("Defne - Elektrik" "Islahiye" "Nurdagi")
export PYTHONIOENCODING=utf-8

adim() {  # adim <ad> <komut...>
  local ad="$1"; shift
  local t0=$(date +%s)
  echo "=== $ad | $(date '+%F %T')" | tee -a "$LOG"
  "$@" >> "$LOG" 2>&1
  local rc=$?
  echo "=== $ad bitti: cikis $rc, $(( $(date +%s) - t0 )) sn" | tee -a "$LOG"
  return $rc
}

adim "sinama donus" "$PY" testler/test_donus.py || exit 1
adim "sinama siniflandirma" "$PY" testler/test_siniflandirma.py || exit 1

adim "b0" "$PY" araclar_tatbikat_kos.py --alanlar "$ALANLAR" --sec "${SEC[@]}" \
  --model segformer_mitb0_p2_t42 --tohum 42 43 44 45 46 --cikti "$OUT/sonuc_b0.json"
adim "b2" "$PY" araclar_tatbikat_kos.py --alanlar "$ALANLAR" --sec "${SEC[@]}" \
  --model segformer_mitb2_p2_t42 --tohum 42 43 44 45 46 --cikti "$OUT/sonuc_b2.json"
adim "unet" "$PY" araclar_tatbikat_kos.py --alanlar "$ALANLAR" --sec "${SEC[@]}" \
  --model unet_mitb4_p2_t42 --tohum 42 43 44 45 46 --rh 0 10 15 25 --cikti "$OUT/sonuc_unet.json"
adim "ozet" "$PY" araclar_tatbikat_ozet.py "$OUT/sonuc_b0.json" "$OUT/sonuc_b2.json" \
  "$OUT/sonuc_unet.json" --cikti "$OUT/tatbikat_ozet.json"

# Duyarlilik (Tablo 19): U-Net, tek tohum
adim "duy donussuz" "$PY" araclar_tatbikat_kos.py --alanlar "$ALANLAR" --sec "${SEC[@]}" \
  --model unet_mitb4_p2_t42 --tohum 42 --donussuz --cikti "$OUT/duy_donussuz.json"
for dk in 0.5 2.0 20; do
  adim "duy degerlendirme $dk" "$PY" araclar_tatbikat_kos.py --alanlar "$ALANLAR" --sec "${SEC[@]}" \
    --model unet_mitb4_p2_t42 --tohum 42 --degerlendirme-dk "$dk" --cikti "$OUT/duy_deg_${dk}.json"
done

# Sekiller (Sekil 10 ve 5)
adim "sekil uc kanal" "$PY" araclar_makale_uc_kanal.py --hepsi
adim "sekil tatbikat nurdagi" "$PY" araclar_makale_haritalari.py --alan Nurdagi

"$PY" -m pip freeze > "$OUT/pip_freeze.txt" 2>/dev/null
echo "=== HEPSI BITTI | $(date '+%F %T')" | tee -a "$LOG"
