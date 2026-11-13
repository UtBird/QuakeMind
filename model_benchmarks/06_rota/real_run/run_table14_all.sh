#!/bin/bash
# Tablo 14: 7 mimarinin EMSR648 kesim-duzeyi kapanma degerlendirmesi (tek komut).
# 1) --prefetch: 8 ornek karonun OSM grafi + yol maskesi onbellege (./cache, git'te yok).
#    Overpass reddederse 5 dk arayla yeniden dener (en fazla ~2 saat).
# 2) 8/8 karo onbellekteyse 7 model sirayla, AYNI karolarda degerlendirilir.
# Kullanim: CKPT_DIR=~/Downloads LOG_DIR=/tmp/t14 ./run_table14_all.sh
set -u
cd "$(dirname "$0")"
PY=${PY:-../../../backend/venv/bin/python}
D=${CKPT_DIR:-$HOME/Downloads}
L=${LOG_DIR:-/tmp/t14_logs}; mkdir -p "$L"
$PY table14_segformer_closure.py --prefetch > "$L/prefetch.log" 2>&1
if grep -q "EKSIK KALDI" "$L/prefetch.log" || ! grep -q "tur .*: 8/8" "$L/prefetch.log"; then
    echo "PREFETCH EKSIK -- $L/prefetch.log'a bak, Overpass acilinca tekrar calistir"; exit 1
fi
echo "PREFETCH TAMAM"
run() { $PY table14_segformer_closure.py --label "$1" --arch "$2" --encoder "$3" ${4:+--checkpoint "$4"} > "$L/$1.log" 2>&1
        echo "BITTI $1: $(grep -E 'Toplam .* basarili' "$L/$1.log")"; }
run segformer        Segformer     mit_b4                                        # uretim checkpoint'i (repoda)
run unet             Unet          mit_b4    "$D/unet_mitb4.pth"
run fpn              FPN           mit_b4    "$D/fpn_mitb4.pth"
run deeplabv3p_mitb4 DeepLabV3Plus mit_b4    "$D/deeplabv3plus_mitb4.pth"
run deeplabv3p_r101  DeepLabV3Plus resnet101 "$D/deeplabv3plus_resnet101.pth"
run linknet          Linknet       resnet34  "$D/linknet_r34_s42.pth"
run pspnet           PSPNet        resnet34  "$D/pspnet_r34_s42.pth"
echo "HEPSI BITTI -- sonuclar results/table14_*.json"
