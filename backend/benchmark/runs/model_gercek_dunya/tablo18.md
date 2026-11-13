# Model bilgili planlama, gerçek (EMSR648) dünyada yürüyüş — J-30 / Tablo 18

Dünya: EMSR648 loose kuralı, tampon 8 m. Sahneler: H-D1 (0/191 kesim gerçekte kapalı), H-D2 (0/221 kesim gerçekte kapalı), K-D1 (48/197 kesim gerçekte kapalı). Görevler: drone-emsr-loose koşularının atamaları, tohum 42–51. v_ort = 15,0 km/sa, t_u = 20 dk. Süreler görev başına ortalamanın tohumlar üzerinden ortalama ± ss'sidir. Üretici: `benchmark/model_in_real_world.py` (backend gerektirmez).

**Okuma.** Hücrelerdeki IoU / duyarlılık / kesinlik, piksel IoU_hasar DEĞİL; modelin kapattığı yol kesimleriyle EMSR648'in kapattığı kesimlerin **kesim düzeyinde** örtüşmesidir (üç sahne toplamı). "Kaçırılan" = gerçekte kapalı olup modelin açık bıraktığı kesim; "yanlış" = modelin kapattığı ama gerçekte açık kesim. "Model rota bulamadı" = yanlış alarmlar hedefi bağlantısız bıraktı, ekip modeli bırakıp klasik devam etti (süre bu davranışla hesaplandı). Yalnız SegFormer maskesi var; diğer beş model eğitilmedi.

## Tablo 18 (drone sahneleri, 10 tohum)

| Kapanma kümesi kaynağı | IoU (kesim) | Duyarlılık | Kesinlik | Kaçırılan kapanma (kesim) | Yanlış kapanma (kesim) | Ortalama ulaşım süresi (dk) | Model rota bulamadı (görev / tohum) | Keşif sayısı (tohum başına) | R0→R3 kazancının yakalanan payı |
|---|---|---|---|---|---|---|---|---|---|
| R3 — kusursuz bilgi (EMSR648) | — | — | — | 0 | 0 | 2,05 ± 0,15 | 0 | 0,0 ± 0,0 | %100 |
| SegFormer, z18, r_h = 0 m (uygulamanın kuralı) | 0,019 | 0,021 | 0,167 | 47 | 5 | 6,52 ± 1,92 | 0,0 ± 0,0 | 2,0 ± 0,8 | %-0 ± 0 |
| SegFormer, z18, r_h = 5 m | 0,029 | 0,042 | 0,083 | 46 | 22 | 6,52 ± 1,92 | 3,0 ± 0,0 | 2,0 ± 0,8 | %0 ± 0 |
| SegFormer, z18, r_h = 10 m | 0,034 | 0,062 | 0,068 | 45 | 41 | 6,52 ± 1,92 | 6,0 ± 0,0 | 2,0 ± 0,8 | %0 ± 0 |
| SegFormer, z18, r_h = 15 m | 0,029 | 0,062 | 0,051 | 45 | 56 | 6,97 ± 2,15 | 6,1 ± 0,3 | 2,2 ± 0,9 | %-11 ± 22 |
| SegFormer, z18, r_h = 25 m | 0,044 | 0,125 | 0,063 | 42 | 89 | 6,97 ± 2,15 | 6,1 ± 0,3 | 2,2 ± 0,9 | %-11 ± 22 |
| SegFormer, z19, r_h = 0 m | 0,053 | 0,083 | 0,125 | 44 | 28 | 6,53 ± 1,92 | 0,0 ± 0,0 | 2,0 ± 0,8 | %-0 ± 0 |
| SegFormer, z19, r_h = 5 m | 0,078 | 0,167 | 0,129 | 40 | 54 | 6,52 ± 1,92 | 5,7 ± 0,5 | 2,0 ± 0,8 | %0 ± 0 |
| SegFormer, z19, r_h = 10 m | 0,114 | 0,333 | 0,148 | 32 | 92 | 6,52 ± 1,92 | 8,7 ± 0,5 | 2,0 ± 0,8 | %0 ± 0 |
| SegFormer, z19, r_h = 15 m | 0,107 | 0,396 | 0,128 | 29 | 129 | 6,52 ± 1,92 | 8,7 ± 0,5 | 2,0 ± 0,8 | %0 ± 0 |
| SegFormer, z19, r_h = 25 m | 0,109 | 0,604 | 0,118 | 19 | 217 | 6,52 ± 1,92 | 8,9 ± 0,3 | 2,0 ± 0,8 | %0 ± 0 |
| SegFormer, z20, r_h = 0 m | 0,079 | 0,125 | 0,176 | 42 | 28 | 6,57 ± 1,92 | 0,0 ± 0,0 | 2,0 ± 0,8 | %-1 ± 1 |
| SegFormer, z20, r_h = 5 m | 0,078 | 0,271 | 0,098 | 35 | 119 | 6,53 ± 1,92 | 6,5 ± 0,7 | 2,0 ± 0,8 | %-0 ± 0 |
| SegFormer, z20, r_h = 10 m | 0,102 | 0,521 | 0,112 | 23 | 198 | 6,52 ± 1,92 | 8,9 ± 0,3 | 2,0 ± 0,8 | %0 ± 0 |
| SegFormer, z20, r_h = 15 m | 0,110 | 0,729 | 0,115 | 13 | 270 | 6,52 ± 1,92 | 8,9 ± 0,3 | 2,0 ± 0,8 | %0 ± 0 |
| SegFormer, z20, r_h = 25 m | 0,100 | 0,917 | 0,101 | 4 | 390 | 6,52 ± 1,92 | 9,0 ± 0,0 | 2,0 ± 0,8 | %0 ± 0 |
| R0 — naif ajan | — | 0,000 | — | 48 (tümü) | 0 | 6,52 ± 1,92 | 0 | 2,0 ± 0,8 | %0 |

## Modelin kapanmalarını yumuşak ceza olarak kullanmak (duyarlılık)

Bugünkü sistem modelin kapattığı kenarı çizgeden siler (yukarıdaki tablo). Burada kenar silinmez; planlamada uzunluğu ×3 (Denklem 9'un en yüksek çarpanı) ya da ×10 pahalılaşır, böylece yanlış alarm ağı koparamaz. Dünya ve görevler aynı.

| Kaynak | Ortalama ulaşım süresi (dk) | K-D1 süre (dk) | H-D1+H-D2 süre (dk) | Keşif sayısı (tohum başına) | R0→R3 kazancının yakalanan payı |
|---|---|---|---|---|---|
| R3 — kusursuz bilgi (EMSR648) | 2,05 ± 0,15 | 2,46 ± 0,55 | 1,84 ± 0,14 | 0,0 ± 0,0 | %100 ± 0 |
| SegFormer, z18, r_h = 0 m, yumuşak ×3 | 6,52 ± 1,92 | 15,88 ± 5,83 | 1,84 ± 0,14 | 2,0 ± 0,8 | %0 ± 0 |
| SegFormer, z18, r_h = 5 m, yumuşak ×3 | 6,59 ± 1,92 | 15,88 ± 5,83 | 1,94 ± 0,15 | 2,0 ± 0,8 | %-1 ± 0 |
| SegFormer, z18, r_h = 10 m, yumuşak ×3 | 6,59 ± 1,92 | 15,88 ± 5,83 | 1,95 ± 0,16 | 2,0 ± 0,8 | %-2 ± 0 |
| SegFormer, z18, r_h = 15 m, yumuşak ×3 | 6,98 ± 2,15 | 17,24 ± 6,61 | 1,84 ± 0,14 | 2,2 ± 0,9 | %-11 ± 22 |
| SegFormer, z18, r_h = 25 m, yumuşak ×3 | 6,97 ± 2,15 | 17,24 ± 6,61 | 1,84 ± 0,14 | 2,2 ± 0,9 | %-11 ± 22 |
| SegFormer, z19, r_h = 0 m, yumuşak ×3 | 6,52 ± 1,92 | 15,89 ± 5,83 | 1,84 ± 0,14 | 2,0 ± 0,8 | %-0 ± 0 |
| SegFormer, z19, r_h = 5 m, yumuşak ×3 | 6,59 ± 1,92 | 15,89 ± 5,83 | 1,95 ± 0,16 | 2,0 ± 0,8 | %-2 ± 0 |
| SegFormer, z19, r_h = 10 m, yumuşak ×3 | 6,53 ± 1,91 | 15,89 ± 5,83 | 1,86 ± 0,15 | 2,0 ± 0,8 | %-0 ± 1 |
| SegFormer, z19, r_h = 15 m, yumuşak ×3 | 5,67 ± 1,66 | 13,22 ± 5,14 | 1,89 ± 0,16 | 1,6 ± 0,7 | %18 ± 23 |
| SegFormer, z19, r_h = 25 m, yumuşak ×3 | 6,81 ± 2,04 | 16,62 ± 6,30 | 1,90 ± 0,16 | 2,1 ± 0,9 | %-9 ± 26 |
| SegFormer, z20, r_h = 0 m, yumuşak ×3 | 6,56 ± 1,92 | 15,89 ± 5,83 | 1,90 ± 0,15 | 2,0 ± 0,8 | %-1 ± 0 |
| SegFormer, z20, r_h = 5 m, yumuşak ×3 | 7,10 ± 2,14 | 17,23 ± 6,60 | 2,04 ± 0,17 | 2,2 ± 0,9 | %-14 ± 22 |
| SegFormer, z20, r_h = 10 m, yumuşak ×3 | 7,62 ± 1,67 | 18,70 ± 5,20 | 2,08 ± 0,17 | 2,4 ± 0,7 | %-21 ± 25 |
| SegFormer, z20, r_h = 15 m, yumuşak ×3 | 7,03 ± 2,14 | 17,25 ± 6,61 | 1,92 ± 0,18 | 2,2 ± 0,9 | %-12 ± 22 |
| SegFormer, z20, r_h = 25 m, yumuşak ×3 | 5,66 ± 1,66 | 13,29 ± 5,14 | 1,85 ± 0,15 | 1,6 ± 0,7 | %18 ± 23 |
| SegFormer, z18, r_h = 0 m, yumuşak ×10 | 6,52 ± 1,92 | 15,88 ± 5,83 | 1,84 ± 0,13 | 2,0 ± 0,8 | %-0 ± 0 |
| SegFormer, z18, r_h = 5 m, yumuşak ×10 | 6,59 ± 1,92 | 15,88 ± 5,83 | 1,94 ± 0,16 | 2,0 ± 0,8 | %-1 ± 0 |
| SegFormer, z18, r_h = 10 m, yumuşak ×10 | 6,60 ± 1,93 | 15,88 ± 5,83 | 1,96 ± 0,13 | 2,0 ± 0,8 | %-2 ± 0 |
| SegFormer, z18, r_h = 15 m, yumuşak ×10 | 7,29 ± 2,20 | 17,24 ± 6,61 | 2,31 ± 0,22 | 2,2 ± 0,9 | %-18 ± 22 |
| SegFormer, z18, r_h = 25 m, yumuşak ×10 | 7,01 ± 2,17 | 17,24 ± 6,61 | 1,90 ± 0,17 | 2,2 ± 0,9 | %-12 ± 22 |
| SegFormer, z19, r_h = 0 m, yumuşak ×10 | 6,53 ± 1,92 | 15,89 ± 5,83 | 1,85 ± 0,12 | 2,0 ± 0,8 | %-0 ± 0 |
| SegFormer, z19, r_h = 5 m, yumuşak ×10 | 6,59 ± 1,92 | 15,89 ± 5,83 | 1,95 ± 0,16 | 2,0 ± 0,8 | %-2 ± 0 |
| SegFormer, z19, r_h = 10 m, yumuşak ×10 | 7,51 ± 1,68 | 18,58 ± 5,19 | 1,98 ± 0,18 | 2,4 ± 0,7 | %-19 ± 25 |
| SegFormer, z19, r_h = 15 m, yumuşak ×10 | 6,48 ± 1,78 | 15,43 ± 5,40 | 2,01 ± 0,17 | 1,9 ± 0,7 | %-0 ± 11 |
| SegFormer, z19, r_h = 25 m, yumuşak ×10 | 6,97 ± 2,18 | 16,05 ± 6,84 | 2,42 ± 0,22 | 2,0 ± 0,9 | %-11 ± 33 |
| SegFormer, z20, r_h = 0 m, yumuşak ×10 | 6,57 ± 1,92 | 15,89 ± 5,83 | 1,91 ± 0,13 | 2,0 ± 0,8 | %-1 ± 1 |
| SegFormer, z20, r_h = 5 m, yumuşak ×10 | 7,53 ± 2,28 | 18,33 ± 6,95 | 2,13 ± 0,22 | 2,3 ± 0,9 | %-24 ± 26 |
| SegFormer, z20, r_h = 10 m, yumuşak ×10 | 7,84 ± 1,74 | 19,18 ± 5,37 | 2,17 ± 0,19 | 2,4 ± 0,7 | %-26 ± 26 |
| SegFormer, z20, r_h = 15 m, yumuşak ×10 | 7,43 ± 2,22 | 18,31 ± 6,94 | 1,99 ± 0,18 | 2,3 ± 0,9 | %-22 ± 26 |
| SegFormer, z20, r_h = 25 m, yumuşak ×10 | 6,36 ± 1,74 | 15,35 ± 5,30 | 1,87 ± 0,17 | 1,9 ± 0,7 | %2 ± 11 |
| R0 — naif ajan | 6,52 ± 1,92 | 15,88 ± 5,83 | 1,84 ± 0,14 | 2,0 ± 0,8 | %0 ± 0 |

## Gerçek hasarlı sahne (K-D1) ve hasarsız sahneler (H-D1, H-D2) ayrı

H-D1 ve H-D2'de EMSR648 hiç yol hasarı işaretlememiş: orada modelin her kapanması yanlış alarmdır ve maliyeti yalnız dolanmadır. K-D1'de hem kaçırma hem yanlış alarm vardır.

| Kaynak | K-D1: süre (dk) | K-D1: keşif | K-D1: kesinlik / duyarlılık | H-D1+H-D2: süre (dk) | H-D1+H-D2: yanlış kapanma (kesim) | H-D1+H-D2: model rota bulamadı |
|---|---|---|---|---|---|---|
| R3 — kusursuz bilgi (EMSR648) | 2,46 ± 0,55 | 0,0 ± 0,0 | — | 1,84 ± 0,14 | 0 | 0,0 ± 0,0 |
| SegFormer, z18, r_h = 0 m (uygulamanın kuralı) | 15,88 ± 5,83 | 2,0 ± 0,8 | 0,50 / 0,02 | 1,84 ± 0,13 | 4 | 0,0 ± 0,0 |
| SegFormer, z18, r_h = 5 m | 15,88 ± 5,83 | 2,0 ± 0,8 | 0,67 / 0,04 | 1,84 ± 0,14 | 21 | 3,0 ± 0,0 |
| SegFormer, z18, r_h = 10 m | 15,88 ± 5,83 | 2,0 ± 0,8 | 0,75 / 0,06 | 1,84 ± 0,14 | 40 | 6,0 ± 0,0 |
| SegFormer, z18, r_h = 15 m | 17,24 ± 6,61 | 2,2 ± 0,9 | 0,38 / 0,06 | 1,84 ± 0,14 | 51 | 6,0 ± 0,0 |
| SegFormer, z18, r_h = 25 m | 17,24 ± 6,61 | 2,2 ± 0,9 | 0,43 / 0,12 | 1,84 ± 0,14 | 81 | 6,0 ± 0,0 |
| SegFormer, z19, r_h = 0 m | 15,89 ± 5,83 | 2,0 ± 0,8 | 0,29 / 0,08 | 1,85 ± 0,12 | 18 | 0,0 ± 0,0 |
| SegFormer, z19, r_h = 5 m | 15,88 ± 5,83 | 2,0 ± 0,8 | 0,28 / 0,17 | 1,84 ± 0,14 | 33 | 3,0 ± 0,0 |
| SegFormer, z19, r_h = 10 m | 15,88 ± 5,83 | 2,0 ± 0,8 | 0,33 / 0,33 | 1,84 ± 0,14 | 59 | 6,0 ± 0,0 |
| SegFormer, z19, r_h = 15 m | 15,88 ± 5,83 | 2,0 ± 0,8 | 0,32 / 0,40 | 1,84 ± 0,14 | 89 | 6,0 ± 0,0 |
| SegFormer, z19, r_h = 25 m | 15,88 ± 5,83 | 2,0 ± 0,8 | 0,29 / 0,60 | 1,84 ± 0,14 | 145 | 6,0 ± 0,0 |
| SegFormer, z20, r_h = 0 m | 15,89 ± 5,83 | 2,0 ± 0,8 | 0,40 / 0,12 | 1,91 ± 0,13 | 19 | 0,0 ± 0,0 |
| SegFormer, z20, r_h = 5 m | 15,88 ± 5,83 | 2,0 ± 0,8 | 0,22 / 0,27 | 1,85 ± 0,13 | 74 | 3,6 ± 0,7 |
| SegFormer, z20, r_h = 10 m | 15,88 ± 5,83 | 2,0 ± 0,8 | 0,28 / 0,52 | 1,84 ± 0,14 | 133 | 6,0 ± 0,0 |
| SegFormer, z20, r_h = 15 m | 15,88 ± 5,83 | 2,0 ± 0,8 | 0,30 / 0,73 | 1,84 ± 0,14 | 189 | 6,0 ± 0,0 |
| SegFormer, z20, r_h = 25 m | 15,88 ± 5,83 | 2,0 ± 0,8 | 0,28 / 0,92 | 1,84 ± 0,14 | 277 | 6,0 ± 0,0 |
| R0 — naif ajan | 15,88 ± 5,83 | 2,0 ± 0,8 | — | 1,84 ± 0,14 | 0 | 0,0 ± 0,0 |

## t_u duyarlılığı (görev başına ortalama süre, dk)

| Kaynak | t_u = 0 dk | t_u = 5 dk | t_u = 10 dk | t_u = 20 dk | t_u = 30 dk |
|---|---|---|---|---|---|
| R3 — kusursuz bilgi (EMSR648) | 2,05 ± 0,15 | 2,05 ± 0,15 | 2,05 ± 0,15 | 2,05 ± 0,15 | 2,05 ± 0,15 |
| SegFormer, z18, r_h = 0 m (uygulamanın kuralı) | 2,08 ± 0,16 | 3,19 ± 0,57 | 4,30 ± 1,01 | 6,52 ± 1,92 | 8,75 ± 2,82 |
| SegFormer, z18, r_h = 5 m | 2,08 ± 0,16 | 3,19 ± 0,57 | 4,30 ± 1,01 | 6,52 ± 1,92 | 8,74 ± 2,82 |
| SegFormer, z18, r_h = 10 m | 2,08 ± 0,16 | 3,19 ± 0,57 | 4,30 ± 1,01 | 6,52 ± 1,92 | 8,74 ± 2,82 |
| SegFormer, z18, r_h = 15 m | 2,08 ± 0,16 | 3,30 ± 0,63 | 4,53 ± 1,13 | 6,97 ± 2,15 | 9,42 ± 3,17 |
| SegFormer, z18, r_h = 25 m | 2,08 ± 0,16 | 3,30 ± 0,63 | 4,53 ± 1,13 | 6,97 ± 2,15 | 9,42 ± 3,17 |
| SegFormer, z19, r_h = 0 m | 2,08 ± 0,16 | 3,19 ± 0,57 | 4,31 ± 1,01 | 6,53 ± 1,92 | 8,75 ± 2,82 |
| SegFormer, z19, r_h = 5 m | 2,08 ± 0,16 | 3,19 ± 0,57 | 4,30 ± 1,01 | 6,52 ± 1,92 | 8,74 ± 2,82 |
| SegFormer, z19, r_h = 10 m | 2,08 ± 0,16 | 3,19 ± 0,57 | 4,30 ± 1,01 | 6,52 ± 1,92 | 8,74 ± 2,82 |
| SegFormer, z19, r_h = 15 m | 2,08 ± 0,16 | 3,19 ± 0,57 | 4,30 ± 1,01 | 6,52 ± 1,92 | 8,74 ± 2,82 |
| SegFormer, z19, r_h = 25 m | 2,08 ± 0,16 | 3,19 ± 0,57 | 4,30 ± 1,01 | 6,52 ± 1,92 | 8,74 ± 2,82 |
| SegFormer, z20, r_h = 0 m | 2,12 ± 0,16 | 3,24 ± 0,57 | 4,35 ± 1,02 | 6,57 ± 1,92 | 8,79 ± 2,83 |
| SegFormer, z20, r_h = 5 m | 2,09 ± 0,16 | 3,20 ± 0,57 | 4,31 ± 1,02 | 6,53 ± 1,92 | 8,75 ± 2,83 |
| SegFormer, z20, r_h = 10 m | 2,08 ± 0,16 | 3,19 ± 0,57 | 4,30 ± 1,01 | 6,52 ± 1,92 | 8,74 ± 2,82 |
| SegFormer, z20, r_h = 15 m | 2,08 ± 0,16 | 3,19 ± 0,57 | 4,30 ± 1,01 | 6,52 ± 1,92 | 8,74 ± 2,82 |
| SegFormer, z20, r_h = 25 m | 2,08 ± 0,16 | 3,19 ± 0,57 | 4,30 ± 1,01 | 6,52 ± 1,92 | 8,74 ± 2,82 |
| R0 — naif ajan | 2,08 ± 0,16 | 3,19 ± 0,57 | 4,30 ± 1,01 | 6,52 ± 1,92 | 8,74 ± 2,82 |

## Doğrulama

- R0 (yeni simülatör) = önceki koşunun naive_compare sonucu: 90 / 90 görev birebir.
- R3 mesafesi = önceki koşunun QuakeMind rotası (A*): 90 görev, en büyük fark 0,00 m.
- EMSR dünyası kapanma sayısı koşularla uyuşmayan: 0; model kapanma sayısı (z18 r0, z19 r15) koşularla uyuşmayan: 0.
