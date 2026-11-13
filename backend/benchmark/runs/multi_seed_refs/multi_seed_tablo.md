# Çoklu tohum koşusu ve ara karşılaştırma referansları (E-06, M-25)

Tohumlar: 42, 43, 44, 45, 46, 47, 48, 49, 50, 51 · v_ort = 15,0 km/sa ve t_u = 20 dk (değişmedi) · üretici: `benchmark/multi_seed.py`.

Tohum afetzede yerleşimini (tüm kaynaklarda) ve sentetik kapanma kümesini (yalnız sentetikte) değiştirir; EMSR648 ve model kapanmaları sabittir. Süreler **aynı küme** üzerinden (klasik ekibin de ulaşabildiği görevler), tohum başına toplamların ortalama ± standart sapmasıdır.

## Tohum başına toplamlar

| Yapılandırma | Kapanma | Afetzede | Rotalanan | Klasik ulaşamadı | QuakeMind (dk) | Klasik (dk) | Kazanç (dk) | Kazanç %95 GA | Yol farkı (dk) | Klasik ek yol (%) | U-dönüşü sayısı | U-dönüşü payı |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v2-sentetik-8ilce | sentetik %18 | 18 | 17,8 ± 0,4 | 0,0 ± 0,0 | 203,5 ± 18,9 | 1 552,0 ± 252,0 | 1 348,5 ± 241,7 | [1 175,6; 1 521,4] | 54,5 ± 15,2 | 26,7 ± 6,9 | 64,7 ± 11,4 | %96 |
| v2-sentetik-4ilce | sentetik %18 | 13 | 13,0 ± 0,0 | 0,0 ± 0,0 | 153,4 ± 17,8 | 1 262,7 ± 219,9 | 1 109,3 ± 209,3 | [959,6; 1 259,0] | 35,3 ± 12,7 | 22,8 ± 6,7 | 53,7 ± 10,0 | %97 |
| v2-emsr-strict | EMSR648 strict | 13 | 13,0 ± 0,0 | 0,0 ± 0,0 | 144,3 ± 23,0 | 197,1 ± 59,9 | 52,8 ± 47,1 | [19,1; 86,5] | 0,8 ± 1,1 | 0,5 ± 0,8 | 2,6 ± 2,3 | %99 |
| v2-emsr-medium | EMSR648 medium | 13 | 13,0 ± 0,0 | 0,0 ± 0,0 | 154,0 ± 23,2 | 1 406,2 ± 589,7 | 1 252,2 ± 579,5 | [837,7; 1 666,8] | 50,2 ± 30,6 | 32,2 ± 18,5 | 60,1 ± 27,5 | %96 |
| v2-emsr-loose | EMSR648 loose | 13 | 13,0 ± 0,0 | 0,0 ± 0,0 | 154,1 ± 23,3 | 1 433,0 ± 607,8 | 1 278,9 ± 597,1 | [851,7; 1 706,1] | 50,9 ± 31,1 | 32,5 ± 18,7 | 61,4 ± 28,3 | %96 |
| drone-sentetik | sentetik %18 | 9 | 8,7 ± 0,9 | 0,0 ± 0,0 | 16,5 ± 2,9 | 81,3 ± 59,9 | 64,8 ± 58,4 | [23,1; 106,6] | 0,8 ± 0,8 | 5,3 ± 4,7 | 3,2 ± 2,9 | %98 |
| drone-emsr-loose | EMSR648 loose | 9 | 9,0 ± 0,0 | 0,0 ± 0,0 | 18,4 ± 1,4 | 58,7 ± 17,3 | 40,3 ± 16,4 | [28,5; 52,0] | 0,3 ± 0,1 | 1,5 ± 0,7 | 2,0 ± 0,8 | %99 |
| drone-model-z18-r0 | model -z18 r_h=0.0 | 9 | 9,0 ± 0,0 | 0,0 ± 0,0 | 16,7 ± 1,6 | 20,7 ± 8,1 | 4,0 ± 8,4 | [-2,0; 10,0] | 0,0 ± 0,0 | 0,0 ± 0,0 | 0,2 ± 0,4 | %100 |
| drone-model-z19-r15 | model -z19 r_h=15.0 | 9 | 2,1 ± 0,6 | 0,0 ± 0,0 | 1,9 ± 0,9 | 3,9 ± 6,3 | 2,0 ± 6,3 | [-2,5; 6,5] | 0,0 ± 0,0 | 0,0 ± 0,0 | 0,1 ± 0,3 | %100 |

## Görev düzeyi (tohumlar havuzlanmış)

Klasik ekip yalnız açık yollarda yürüdüğü için yolu, kapanmaları bilen en kısa yoldan kısa **olamaz**: fark yapı gereği ≥ 0 (tabloda "Yol farkı < 0" her yerde %0). Bu yüzden işaretli sıra testi her zaman anlamlı ve etki büyüklüğü r = 1 çıkar; bilgi taşımadıkları için tabloda yoklar (JSON'da duruyor). Anlamlı olan büyüklük ve sıklıktır. Görevler aynı ekip ve karargâhları paylaştığı için tam bağımsız değildir; birincil birim yukarıdaki tohum başına toplamdır.

| Yapılandırma | Görev | Kapanmaya çarpılan görev | Kazanç medyan [Ç1; Ç3] (dk) | Kazanç > 0 | Yol farkı medyan [Ç1; Ç3] (dk) | Yol farkı > 0 | Yol farkı < 0 | Klasik ek yol % medyan [Ç1; Ç3] |
|---|---|---|---|---|---|---|---|---|
| v2-sentetik-8ilce | 178 | %79 | 60,3 [20,0; 104,8] | %79 | 1,0 [0,0; 4,3] | %72 | %0 | 9,0 [0,0; 30,7] |
| v2-sentetik-4ilce | 130 | %82 | 61,2 [20,3; 123,7] | %82 | 1,0 [0,1; 3,7] | %75 | %0 | 9,5 [0,7; 30,5] |
| v2-emsr-strict | 130 | %6 | 0,0 [0,0; 0,0] | %6 | 0,0 [0,0; 0,0] | %5 | %0 | 0,0 [0,0; 0,0] |
| v2-emsr-medium | 130 | %40 | 0,0 [0,0; 142,3] | %40 | 0,0 [0,0; 2,3] | %39 | %0 | 0,0 [0,0; 18,0] |
| v2-emsr-loose | 130 | %43 | 0,0 [0,0; 142,3] | %43 | 0,0 [0,0; 2,3] | %42 | %0 | 0,0 [0,0; 18,7] |
| drone-sentetik | 87 | %25 | 0,0 [0,0; 10,0] | %25 | 0,0 [0,0; 0,0] | %20 | %0 | 0,0 [0,0; 0,0] |
| drone-emsr-loose | 90 | %22 | 0,0 [0,0; 0,0] | %22 | 0,0 [0,0; 0,0] | %22 | %0 | 0,0 [0,0; 0,0] |
| drone-model-z18-r0 | 90 | %2 | 0,0 [0,0; 0,0] | %2 | 0,0 [0,0; 0,0] | %0 | %0 | 0,0 [0,0; 0,0] |
| drone-model-z19-r15 | 21 | %5 | 0,0 [0,0; 0,0] | %5 | 0,0 [0,0; 0,0] | %0 | %0 | 0,0 [0,0; 0,0] |

## U-dönüşlerinin dağılımı (10 tohum toplamı)

| Yapılandırma | Toplam keşif | Görev başına en çok | En çok keşifli %10 görevin payı | Bölgelere göre keşif |
|---|---|---|---|---|
| v2-sentetik-8ilce | 647 | 16 | %30 | H-Z1: 100 · H-Z2: 61 · H-Z3: 24 · H-Z4: 22 · H-Z5: 7 · K-Z1: 400 · K-Z2: 19 · K-Z3: 14 |
| v2-sentetik-4ilce | 537 | 16 | %29 | H-Z1: 100 · H-Z3: 18 · K-Z1: 400 · K-Z2: 19 |
| v2-emsr-strict | 26 | 6 | %100 | H-Z1: 26 |
| v2-emsr-medium | 601 | 38 | %60 | H-Z1: 54 · K-Z1: 545 · K-Z2: 2 |
| v2-emsr-loose | 614 | 38 | %59 | H-Z1: 54 · H-Z3: 13 · K-Z1: 545 · K-Z2: 2 |
| drone-sentetik | 32 | 3 | %56 | H-D1: 16 · H-D2: 8 · K-D1: 8 |
| drone-emsr-loose | 20 | 1 | %45 | K-D1: 20 |
| drone-model-z18-r0 | 2 | 1 | %100 | H-D1: 2 |
| drone-model-z19-r15 | 1 | 1 | %100 | K-D1: 1 |

## Aynı tohumda kaynak farkı (eşleştirilmiş)

Fark = bu yapılandırma − referans, aynı tohumda. Karşılaştırılan görev sayıları farklıysa fark kazanç farkı değil küme farkıdır.

| Yapılandırma | Referans | Eşleşen tohum | Görev (bu / ref.) | Kazanç farkı (dk) | Yol farkı farkı (dk) | Aynı yerleşim |
|---|---|---|---|---|---|---|
| v2-emsr-strict | v2-sentetik-4ilce | 10 | 13,0 / 13,0 | -1 056,5 ± 195,3 | -34,5 ± 12,4 | %87 |
| v2-emsr-medium | v2-sentetik-4ilce | 10 | 13,0 / 13,0 | 142,9 ± 573,4 | 14,9 ± 29,7 | %88 |
| v2-emsr-loose | v2-sentetik-4ilce | 10 | 13,0 / 13,0 | 169,6 ± 586,8 | 15,6 ± 30,3 | %88 |
| drone-emsr-loose | drone-sentetik | 10 | 9,0 / 8,7 | -24,6 ± 56,8 | -0,6 ± 0,8 | %78 |
| drone-model-z18-r0 | drone-sentetik | 10 | 9,0 / 8,7 | -60,9 ± 58,5 | -0,8 ± 0,8 | %94 |
| drone-model-z19-r15 | drone-sentetik | 10 | 2,1 / 8,7 | -62,9 ± 60,3 | -0,8 ± 0,8 | %2 |

## U-dönüşü cezasına duyarlılık (aynı koşulardan)

Kazanç = yol farkı + t_u × keşif sayısı; tohum başına toplamların ortalama ± ss'si (dk). Raporlanan değer t_u = 20 dk.

| Yapılandırma | t_u = 0 dk | t_u = 5 dk | t_u = 10 dk | t_u = 20 dk | t_u = 30 dk |
|---|---|---|---|---|---|
| v2-sentetik-8ilce | 54,5 ± 15,2 | 378,0 ± 71,4 | 701,5 ± 128,1 | 1 348,5 ± 241,7 | 1 995,5 ± 355,4 |
| v2-sentetik-4ilce | 35,3 ± 12,7 | 303,8 ± 60,0 | 572,3 ± 109,6 | 1 109,3 ± 209,3 | 1 646,3 ± 309,0 |
| v2-emsr-strict | 0,8 ± 1,1 | 13,8 ± 12,4 | 26,8 ± 23,9 | 52,8 ± 47,1 | 78,8 ± 70,3 |
| v2-emsr-medium | 50,2 ± 30,6 | 350,7 ± 167,4 | 651,2 ± 304,7 | 1 252,2 ± 579,5 | 1 853,2 ± 854,4 |
| v2-emsr-loose | 50,9 ± 31,1 | 357,9 ± 172,1 | 664,9 ± 313,8 | 1 278,9 ± 597,1 | 1 892,9 ± 880,5 |
| drone-sentetik | 0,8 ± 0,8 | 16,9 ± 14,9 | 32,9 ± 29,4 | 64,8 ± 58,4 | 96,8 ± 87,4 |
| drone-emsr-loose | 0,3 ± 0,1 | 10,3 ± 4,2 | 20,3 ± 8,3 | 40,3 ± 16,4 | 60,3 ± 24,6 |
| drone-model-z18-r0 | 0,0 ± 0,0 | 1,0 ± 2,1 | 2,0 ± 4,2 | 4,0 ± 8,4 | 6,0 ± 12,6 |
| drone-model-z19-r15 | 0,0 ± 0,0 | 0,5 ± 1,6 | 1,0 ± 3,2 | 2,0 ± 6,3 | 3,0 ± 9,5 |

## Bölge başına kapalı kenar oranı (%)

| Yapılandırma | Bölge: ortalama ± ss |
|---|---|
| v2-sentetik-8ilce | H-Z1: 2,13 ± 0,36 · H-Z2: 3,82 ± 1,09 · H-Z3: 1,34 ± 0,47 · H-Z4: 1,80 ± 0,58 · H-Z5: 0,55 ± 0,00 · K-Z1: 4,50 ± 0,00 · K-Z2: 4,27 ± 0,71 · K-Z3: 1,79 ± 0,58 |
| v2-sentetik-4ilce | H-Z1: 2,13 ± 0,36 · H-Z3: 1,79 ± 0,58 · K-Z1: 4,50 ± 0,00 · K-Z2: 4,27 ± 0,71 |
| v2-emsr-strict | H-Z1: 0,30 ± 0,00 · H-Z3: 0,00 ± 0,00 · K-Z1: 0,00 ± 0,00 · K-Z2: 0,00 ± 0,00 |
| v2-emsr-medium | H-Z1: 0,84 ± 0,00 · H-Z3: 0,00 ± 0,00 · K-Z1: 1,80 ± 0,00 · K-Z2: 0,45 ± 0,00 |
| v2-emsr-loose | H-Z1: 0,84 ± 0,00 · H-Z3: 0,32 ± 0,00 · K-Z1: 1,80 ± 0,00 · K-Z2: 0,53 ± 0,00 |
| drone-sentetik | H-D1: 6,54 ± 2,48 · H-D2: 3,08 ± 1,31 · K-D1: 4,37 ± 2,43 |
| drone-emsr-loose | H-D1: 0,00 ± 0,00 · H-D2: 0,00 ± 0,00 · K-D1: 24,37 ± 0,00 |
| drone-model-z18-r0 | H-D1: 2,09 ± 0,00 · H-D2: 0,00 ± 0,00 · K-D1: 1,02 ± 0,00 |
| drone-model-z19-r15 | H-D1: 25,65 ± 0,00 · H-D2: 18,10 ± 0,00 · K-D1: 29,95 ± 0,00 |

## Tek tohumlu koşuyla (J-28, tohum 42) tekrar kontrolü

| Yapılandırma | Birebir aynı | J-28 (bizim / klasik / U-dön.) | Bu tarama, tohum 42 |
|---|---|---|---|
| v2-sentetik-8ilce | evet | 222,2 / 1 744,8 / 73 | 222,2 / 1 744,8 / 73 |
| v2-sentetik-4ilce | evet | 180,3 / 1 600,3 / 68 | 180,3 / 1 600,3 / 68 |
| v2-emsr-strict | evet | 177,6 / 238,0 / 3 | 177,6 / 238,0 / 3 |
| v2-emsr-medium | evet | 189,1 / 1 924,7 / 83 | 189,1 / 1 924,7 / 83 |
| v2-emsr-loose | evet | 189,5 / 2 006,7 / 87 | 189,5 / 2 006,7 / 87 |
| drone-sentetik | evet | 20,4 / 161,8 / 7 | 20,4 / 161,8 / 7 |
| drone-emsr-loose | evet | 20,7 / 60,9 / 2 | 20,7 / 60,9 / 2 |
| drone-model-z18-r0 | evet | 19,5 / 19,5 / 0 | 19,5 / 19,5 / 0 |
| drone-model-z19-r15 | evet | 0,2 / 0,2 / 0 | 0,2 / 0,2 / 0 |

## Ara karşılaştırma referansları (Tablo 16, M-25)

Aynı oturum, aynı kapanma kümesi, aynı atamalar; değişen yalnız ekibin kapanmayı nasıl öğrendiği. Küme: klasik ajanın ve tüm referansların her t_u değerinde ulaşabildiği görevler. t_u = 20 dk; tohum başına toplamların ortalama ± ss'si. **R0**: kapanmayı kavşakta, girmeden öğrenir; her keşif bir t_u (Algoritma 1). **R1**: her kavşakta planlı yolun önündeki 100 m'yi görür (yol boyunca; köşe dönüşleri görüşü kesmez — R1 için iyimser); aynı kavşaktaki gözlemler tek t_u. **R2**: bölgedeki ekipler aynı anda yola çıkar; bir ekibin öğrendiği kapanma o anda telsizle tüm ekiplere yayılır; telsizle öğrenilen kapanma cezasız yeniden planlanır, kendi keşfi R0 gibi cezalıdır. Aynı karargâhtan çıkan ekipler ortak yol başında kafile halinde ilerler: kapanmayı öndeki keşfeder, arkadakiler cezasız yön değiştirir ("anında yayılır"). **R2e** bu kafile kuralının duyarlılığıdır: aynı anda varan her ekip kendisi keşfeder. **R1 + R2** ikisini birleştirir (ek). Fark = referans − QuakeMind; kazanç % = fark / referans süresi (Tablo 16'nın paydası).

| Yapılandırma | Yaklaşım | Toplam süre (dk) | Fark (dk) | Kazanç (%) | Yalnız yol farkı (dk) | Ceza olayı | Görülen/keşfedilen kapanma | Telsizle yeniden planlama |
|---|---|---|---|---|---|---|---|---|
| v2-sentetik-8ilce | QuakeMind (kusursuz bilgi, R3) — 17,8 görev | 203,5 ± 18,9 | — | — | — | — | — | — |
| | R0 — naif ajan | 1 552,0 ± 252,0 | 1 348,5 ± 241,7 | 86,7 ± 1,8 | 54,5 ± 15,2 | 64,7 ± 11,4 | 64,7 ± 11,4 | — |
| | ↳ R0, aynı kavşaktaki keşifler tek ceza (R1'in sayımı) | 1 532,0 ± 264,8 | 1 328,5 ± 254,7 | 86,5 ± 2,0 | 54,5 ± 15,2 | 63,7 ± 12,0 | 64,7 ± 11,4 | — |
| | R1 — görüş mesafeli (d_g = 100 m) | 1 357,1 ± 185,2 | 1 153,7 ± 171,5 | 84,9 ± 1,5 | 33,7 ± 10,5 | 56,0 ± 8,2 | 65,1 ± 10,6 | — |
| | R2 — bilgi paylaşan filo | 1 409,5 ± 251,0 | 1 206,0 ± 237,3 | 85,3 ± 1,7 | 52,0 ± 14,1 | 57,7 ± 11,3 | 57,7 ± 11,3 | 4,9 ± 3,2 |
| | ↳ R2, aynı anda varan her ekip kendisi keşfeder (duyarlılık) | 1 474,5 ± 246,0 | 1 271,1 ± 234,8 | 86,0 ± 1,8 | 53,1 ± 14,6 | 60,9 ± 11,1 | 60,9 ± 11,1 | 2,6 ± 2,8 |
| | R1 + R2 (ek, makalede tanımlı değil) | 1 264,1 ± 203,2 | 1 060,7 ± 189,3 | 83,7 ± 1,6 | 32,7 ± 10,6 | 51,4 ± 9,0 | 58,9 ± 11,9 | 5,2 ± 3,2 |
| v2-sentetik-4ilce | QuakeMind (kusursuz bilgi, R3) — 13,0 görev | 153,4 ± 17,8 | — | — | — | — | — | — |
| | R0 — naif ajan | 1 262,7 ± 219,9 | 1 109,3 ± 209,3 | 87,7 ± 1,7 | 35,3 ± 12,7 | 53,7 ± 10,0 | 53,7 ± 10,0 | — |
| | ↳ R0, aynı kavşaktaki keşifler tek ceza (R1'in sayımı) | 1 248,7 ± 230,8 | 1 095,3 ± 220,2 | 87,5 ± 1,8 | 35,3 ± 12,7 | 53,0 ± 10,5 | 53,7 ± 10,0 | — |
| | R1 — görüş mesafeli (d_g = 100 m) | 1 116,7 ± 181,1 | 963,3 ± 168,8 | 86,1 ± 1,6 | 21,3 ± 9,7 | 47,1 ± 8,1 | 55,0 ± 8,7 | — |
| | R2 — bilgi paylaşan filo | 1 126,3 ± 277,2 | 972,8 ± 264,5 | 85,9 ± 2,3 | 32,8 ± 14,4 | 47,0 ± 12,6 | 47,0 ± 12,6 | 4,9 ± 3,2 |
| | ↳ R2, aynı anda varan her ekip kendisi keşfeder (duyarlılık) | 1 189,3 ± 227,0 | 1 035,9 ± 215,7 | 86,9 ± 1,7 | 33,9 ± 12,5 | 50,1 ± 10,3 | 50,1 ± 10,3 | 2,6 ± 2,8 |
| | R1 + R2 (ek, makalede tanımlı değil) | 1 027,7 ± 215,2 | 874,2 ± 202,7 | 84,8 ± 2,0 | 20,3 ± 9,9 | 42,7 ± 9,7 | 49,1 ± 11,2 | 5,2 ± 3,2 |
| v2-emsr-strict | QuakeMind (kusursuz bilgi, R3) — 13,0 görev | 144,3 ± 23,0 | — | — | — | — | — | — |
| | R0 — naif ajan | 197,1 ± 59,9 | 52,8 ± 47,1 | 22,3 ± 18,2 | 0,8 ± 1,1 | 2,6 ± 2,3 | 2,6 ± 2,3 | — |
| | ↳ R0, aynı kavşaktaki keşifler tek ceza (R1'in sayımı) | 179,1 ± 43,2 | 34,8 ± 29,3 | 17,0 ± 13,6 | 0,8 ± 1,1 | 1,7 ± 1,4 | 2,6 ± 2,3 | — |
| | R1 — görüş mesafeli (d_g = 100 m) | 182,7 ± 50,6 | 38,4 ± 35,2 | 17,9 ± 14,6 | 0,4 ± 0,8 | 1,9 ± 1,7 | 3,3 ± 3,0 | — |
| | R2 — bilgi paylaşan filo | 199,2 ± 62,1 | 54,9 ± 50,9 | 22,7 ± 18,9 | 0,9 ± 1,2 | 2,7 ± 2,5 | 2,7 ± 2,5 | 0,2 ± 0,6 |
| | ↳ R2, aynı anda varan her ekip kendisi keşfeder (duyarlılık) | 199,2 ± 62,1 | 54,9 ± 50,9 | 22,7 ± 18,9 | 0,9 ± 1,2 | 2,7 ± 2,5 | 2,7 ± 2,5 | 0,2 ± 0,6 |
| | R1 + R2 (ek, makalede tanımlı değil) | 182,7 ± 50,6 | 38,4 ± 35,2 | 17,9 ± 14,6 | 0,4 ± 0,8 | 1,9 ± 1,7 | 3,6 ± 3,5 | 0,2 ± 0,6 |
| v2-emsr-medium | QuakeMind (kusursuz bilgi, R3) — 13,0 görev | 154,0 ± 23,2 | — | — | — | — | — | — |
| | R0 — naif ajan | 1 406,2 ± 589,7 | 1 252,2 ± 579,5 | 86,6 ± 8,0 | 50,2 ± 30,6 | 60,1 ± 27,5 | 60,1 ± 27,5 | — |
| | ↳ R0, aynı kavşaktaki keşifler tek ceza (R1'in sayımı) | 1 144,2 ± 472,2 | 990,2 ± 462,3 | 83,8 ± 9,1 | 50,2 ± 30,6 | 47,0 ± 21,6 | 60,1 ± 27,5 | — |
| | R1 — görüş mesafeli (d_g = 100 m) | 925,9 ± 330,8 | 771,9 ± 321,0 | 81,3 ± 7,7 | 33,9 ± 21,2 | 36,9 ± 15,0 | 85,7 ± 41,3 | — |
| | R2 — bilgi paylaşan filo | 1 035,8 ± 288,9 | 881,8 ± 281,5 | 83,7 ± 6,9 | 41,8 ± 19,5 | 42,0 ± 13,2 | 42,0 ± 13,2 | 7,2 ± 6,2 |
| | ↳ R2, aynı anda varan her ekip kendisi keşfeder (duyarlılık) | 1 032,3 ± 274,7 | 878,3 ± 267,2 | 83,8 ± 6,7 | 40,3 ± 17,3 | 41,9 ± 12,6 | 41,9 ± 12,6 | 5,4 ± 3,7 |
| | R1 + R2 (ek, makalede tanımlı değil) | 747,4 ± 166,4 | 593,4 ± 158,6 | 78,4 ± 6,8 | 33,4 ± 15,3 | 28,0 ± 7,4 | 73,6 ± 25,4 | 7,9 ± 5,3 |
| v2-emsr-loose | QuakeMind (kusursuz bilgi, R3) — 13,0 görev | 154,1 ± 23,3 | — | — | — | — | — | — |
| | R0 — naif ajan | 1 433,0 ± 607,8 | 1 278,9 ± 597,1 | 86,8 ± 8,0 | 50,9 ± 31,1 | 61,4 ± 28,3 | 61,4 ± 28,3 | — |
| | ↳ R0, aynı kavşaktaki keşifler tek ceza (R1'in sayımı) | 1 161,0 ± 482,5 | 1 006,9 ± 472,2 | 84,0 ± 9,0 | 50,9 ± 31,1 | 47,8 ± 22,1 | 61,4 ± 28,3 | — |
| | R1 — görüş mesafeli (d_g = 100 m) | 942,4 ± 340,5 | 788,2 ± 330,3 | 81,6 ± 7,7 | 34,2 ± 21,4 | 37,7 ± 15,5 | 86,9 ± 41,9 | — |
| | R2 — bilgi paylaşan filo | 1 062,6 ± 297,5 | 908,5 ± 288,9 | 84,1 ± 6,9 | 42,5 ± 19,8 | 43,3 ± 13,6 | 43,3 ± 13,6 | 7,2 ± 6,2 |
| | ↳ R2, aynı anda varan her ekip kendisi keşfeder (duyarlılık) | 1 059,0 ± 282,5 | 904,9 ± 273,7 | 84,1 ± 6,7 | 40,9 ± 17,6 | 43,2 ± 12,9 | 43,2 ± 12,9 | 5,4 ± 3,7 |
| | R1 + R2 (ek, makalede tanımlı değil) | 763,8 ± 175,0 | 609,7 ± 166,1 | 78,7 ± 6,8 | 33,7 ± 15,5 | 28,8 ± 7,7 | 74,8 ± 26,0 | 7,9 ± 5,3 |
| drone-sentetik | QuakeMind (kusursuz bilgi, R3) — 8,7 görev | 16,5 ± 2,9 | — | — | — | — | — | — |
| | R0 — naif ajan | 81,3 ± 59,9 | 64,8 ± 58,4 | 66,9 ± 27,3 | 0,9 ± 0,8 | 3,2 ± 2,9 | 3,2 ± 2,9 | — |
| | ↳ R0, aynı kavşaktaki keşifler tek ceza (R1'in sayımı) | 77,3 ± 51,8 | 60,9 ± 50,3 | 66,7 ± 27,1 | 0,9 ± 0,8 | 3,0 ± 2,5 | 3,2 ± 2,9 | — |
| | R1 — görüş mesafeli (d_g = 100 m) | 74,7 ± 48,2 | 58,2 ± 46,7 | 66,3 ± 26,9 | 0,2 ± 0,3 | 2,9 ± 2,3 | 3,3 ± 3,1 | — |
| | R2 — bilgi paylaşan filo | 59,3 ± 32,4 | 42,9 ± 31,0 | 63,2 ± 24,9 | 0,9 ± 0,8 | 2,1 ± 1,5 | 2,1 ± 1,5 | 1,0 ± 1,3 |
| | ↳ R2, aynı anda varan her ekip kendisi keşfeder (duyarlılık) | 79,3 ± 55,7 | 62,9 ± 54,1 | 66,8 ± 27,2 | 0,9 ± 0,8 | 3,1 ± 2,7 | 3,1 ± 2,7 | 0,0 ± 0,0 |
| | R1 + R2 (ek, makalede tanımlı değil) | 54,7 ± 25,3 | 38,2 ± 24,0 | 62,1 ± 24,2 | 0,2 ± 0,3 | 1,9 ± 1,2 | 2,1 ± 1,5 | 0,8 ± 1,3 |
| drone-emsr-loose | QuakeMind (kusursuz bilgi, R3) — 9,0 görev | 18,4 ± 1,4 | — | — | — | — | — | — |
| | R0 — naif ajan | 58,7 ± 17,3 | 40,3 ± 16,4 | 63,2 ± 22,4 | 0,3 ± 0,1 | 2,0 ± 0,8 | 2,0 ± 0,8 | — |
| | ↳ R0, aynı kavşaktaki keşifler tek ceza (R1'in sayımı) | 58,7 ± 17,3 | 40,3 ± 16,4 | 63,2 ± 22,4 | 0,3 ± 0,1 | 2,0 ± 0,8 | 2,0 ± 0,8 | — |
| | R1 — görüş mesafeli (d_g = 100 m) | 58,4 ± 17,2 | 40,0 ± 16,3 | 63,0 ± 22,4 | 0,0 ± 0,0 | 2,0 ± 0,8 | 2,0 ± 0,8 | — |
| | R2 — bilgi paylaşan filo | 36,7 ± 7,3 | 18,3 ± 6,4 | 46,9 ± 16,6 | 0,3 ± 0,1 | 0,9 ± 0,3 | 0,9 ± 0,3 | 1,1 ± 0,6 |
| | ↳ R2, aynı anda varan her ekip kendisi keşfeder (duyarlılık) | 58,7 ± 17,3 | 40,3 ± 16,4 | 63,2 ± 22,4 | 0,3 ± 0,1 | 2,0 ± 0,8 | 2,0 ± 0,8 | 0,0 ± 0,0 |
| | R1 + R2 (ek, makalede tanımlı değil) | 36,4 ± 7,2 | 18,0 ± 6,3 | 46,6 ± 16,4 | 0,0 ± 0,0 | 0,9 ± 0,3 | 0,9 ± 0,3 | 1,1 ± 0,6 |
| drone-model-z18-r0 | QuakeMind (kusursuz bilgi, R3) — 9,0 görev | 16,7 ± 1,6 | — | — | — | — | — | — |
| | R0 — naif ajan | 20,7 ± 8,1 | 4,0 ± 8,4 | 11,2 ± 23,5 | 0,0 ± 0,0 | 0,2 ± 0,4 | 0,2 ± 0,4 | — |
| | ↳ R0, aynı kavşaktaki keşifler tek ceza (R1'in sayımı) | 20,7 ± 8,1 | 4,0 ± 8,4 | 11,2 ± 23,5 | 0,0 ± 0,0 | 0,2 ± 0,4 | 0,2 ± 0,4 | — |
| | R1 — görüş mesafeli (d_g = 100 m) | 20,7 ± 8,1 | 4,0 ± 8,4 | 11,2 ± 23,5 | 0,0 ± 0,0 | 0,2 ± 0,4 | 0,3 ± 0,7 | — |
| | R2 — bilgi paylaşan filo | 20,7 ± 8,1 | 4,0 ± 8,4 | 11,2 ± 23,5 | 0,0 ± 0,0 | 0,2 ± 0,4 | 0,2 ± 0,4 | 0,0 ± 0,0 |
| | ↳ R2, aynı anda varan her ekip kendisi keşfeder (duyarlılık) | 20,7 ± 8,1 | 4,0 ± 8,4 | 11,2 ± 23,5 | 0,0 ± 0,0 | 0,2 ± 0,4 | 0,2 ± 0,4 | 0,0 ± 0,0 |
| | R1 + R2 (ek, makalede tanımlı değil) | 20,7 ± 8,1 | 4,0 ± 8,4 | 11,2 ± 23,5 | 0,0 ± 0,0 | 0,2 ± 0,4 | 0,3 ± 0,7 | 0,0 ± 0,0 |
| drone-model-z19-r15 | QuakeMind (kusursuz bilgi, R3) — 2,1 görev | 1,9 ± 0,9 | — | — | — | — | — | — |
| | R0 — naif ajan | 3,9 ± 6,3 | 2,0 ± 6,3 | 9,3 ± 29,3 | 0,0 ± 0,0 | 0,1 ± 0,3 | 0,1 ± 0,3 | — |
| | ↳ R0, aynı kavşaktaki keşifler tek ceza (R1'in sayımı) | 3,9 ± 6,3 | 2,0 ± 6,3 | 9,3 ± 29,3 | 0,0 ± 0,0 | 0,1 ± 0,3 | 0,1 ± 0,3 | — |
| | R1 — görüş mesafeli (d_g = 100 m) | 3,9 ± 6,3 | 2,0 ± 6,3 | 9,3 ± 29,3 | 0,0 ± 0,0 | 0,1 ± 0,3 | 0,2 ± 0,6 | — |
| | R2 — bilgi paylaşan filo | 3,9 ± 6,3 | 2,0 ± 6,3 | 9,3 ± 29,3 | 0,0 ± 0,0 | 0,1 ± 0,3 | 0,1 ± 0,3 | 0,0 ± 0,0 |
| | ↳ R2, aynı anda varan her ekip kendisi keşfeder (duyarlılık) | 3,9 ± 6,3 | 2,0 ± 6,3 | 9,3 ± 29,3 | 0,0 ± 0,0 | 0,1 ± 0,3 | 0,1 ± 0,3 | 0,0 ± 0,0 |
| | R1 + R2 (ek, makalede tanımlı değil) | 3,9 ± 6,3 | 2,0 ± 6,3 | 9,3 ± 29,3 | 0,0 ± 0,0 | 0,1 ± 0,3 | 0,2 ± 0,6 | 0,0 ± 0,0 |

## Referansların R0'a göre farkı (aynı tohum)

Süre farkı = referans − R0 (negatif: R0'dan hızlı). "Kalan pay" = (referans − QuakeMind) / (R0 − QuakeMind): R0'a karşı ölçülen kazancın o referansa karşı ne kadarının kaldığı.

| Yapılandırma | R1 − R0 (dk) | R2 − R0 (dk) | R2e − R0 (dk) | R1+R2 − R0 (dk) | Kalan pay R1 | Kalan pay R2 | Kalan pay R2e | Kalan pay R1+R2 |
|---|---|---|---|---|---|---|---|---|
| v2-sentetik-8ilce | -194,8 ± 125,8 | -142,5 ± 149,0 | -77,4 ± 66,7 | -287,9 ± 187,5 | %86 ± 7 | %90 ± 9 | %94 ± 5 | %80 ± 11 |
| v2-sentetik-4ilce | -146,0 ± 91,6 | -136,5 ± 147,0 | -73,4 ± 65,6 | -235,1 ± 133,8 | %87 ± 7 | %87 ± 13 | %93 ± 6 | %79 ± 11 |
| v2-emsr-strict | -14,4 ± 19,2 | 2,1 ± 6,7 | 2,1 ± 6,7 | -14,4 ± 19,1 | %76 ± 19 | %102 ± 7 | %102 ± 7 | %76 ± 19 |
| v2-emsr-medium | -480,3 ± 266,8 | -370,4 ± 364,7 | -374,0 ± 414,7 | -658,8 ± 503,7 | %64 ± 9 | %77 ± 17 | %78 ± 19 | %55 ± 21 |
| v2-emsr-loose | -490,6 ± 274,6 | -370,4 ± 364,7 | -374,0 ± 414,7 | -669,2 ± 510,0 | %64 ± 9 | %77 ± 16 | %78 ± 19 | %55 ± 20 |
| drone-sentetik | -6,7 ± 19,2 | -22,0 ± 30,5 | -2,0 ± 6,3 | -26,7 ± 40,3 | %95 ± 11 | %79 ± 25 | %99 ± 4 | %76 ± 27 |
| drone-emsr-loose | -0,3 ± 0,1 | -22,0 ± 11,4 | 0,0 ± 0,0 | -22,3 ± 11,4 | %99 ± 0 | %47 ± 7 | %100 ± 0 | %46 ± 7 |
| drone-model-z18-r0 | 0,0 ± 0,0 | 0,0 ± 0,0 | 0,0 ± 0,0 | 0,0 ± 0,0 | %100 ± 0 | %100 ± 0 | %100 ± 0 | %100 ± 0 |
| drone-model-z19-r15 | 0,0 ± 0,0 | 0,0 ± 0,0 | 0,0 ± 0,0 | 0,0 ± 0,0 | %100 ± 0 | %100 ± 0 | %100 ± 0 | %100 ± 0 |

## Referanslarda t_u duyarlılığı (kazanç, dk ve %)

R0 ve R1'de olaylar t_u'dan bağımsızdır (yeniden hesap); R2'de kimin önce öğrendiği t_u'ya bağlı olduğu için her t_u ayrıca simüle edildi.

| Yapılandırma | Yaklaşım | t_u = 0 dk | t_u = 5 dk | t_u = 10 dk | t_u = 20 dk | t_u = 30 dk |
|---|---|---|---|---|---|---|
| v2-sentetik-8ilce | R0 — naif ajan | 54,5 ± 15,2 (%21) | 378,0 ± 71,4 (%65) | 701,5 ± 128,2 (%77) | 1 348,5 ± 241,7 (%87) | 1 995,5 ± 355,4 (%91) |
|  | R1 — görüş mesafeli (d_g = 100 m) | 33,7 ± 10,5 (%14) | 313,7 ± 48,5 (%60) | 593,7 ± 89,3 (%74) | 1 153,7 ± 171,5 (%85) | 1 713,7 ± 253,7 (%89) |
|  | R2 — bilgi paylaşan filo | 52,8 ± 15,0 (%20) | 339,7 ± 69,1 (%62) | 629,0 ± 124,8 (%75) | 1 206,0 ± 237,3 (%85) | 1 783,0 ± 349,8 (%90) |
|  | ↳ R2, aynı anda varan her ekip kendisi keşfeder (duyarlılık) | 52,8 ± 15,0 (%20) | 356,8 ± 69,3 (%63) | 662,1 ± 124,3 (%76) | 1 271,1 ± 234,8 (%86) | 1 880,1 ± 345,4 (%90) |
|  | R1 + R2 (ek, makalede tanımlı değil) | 32,6 ± 9,9 (%14) | 288,6 ± 53,2 (%58) | 546,6 ± 99,3 (%73) | 1 060,7 ± 189,3 (%84) | 1 574,7 ± 279,4 (%88) |
| v2-sentetik-4ilce | R0 — naif ajan | 35,3 ± 12,7 (%18) | 303,8 ± 60,0 (%66) | 572,3 ± 109,6 (%79) | 1 109,3 ± 209,3 (%88) | 1 646,3 ± 309,0 (%91) |
|  | R1 — görüş mesafeli (d_g = 100 m) | 21,3 ± 9,7 (%12) | 256,8 ± 47,7 (%62) | 492,3 ± 87,9 (%76) | 963,3 ± 168,8 (%86) | 1 434,3 ± 249,8 (%90) |
|  | R2 — bilgi paylaşan filo | 33,6 ± 12,1 (%18) | 267,0 ± 76,6 (%63) | 502,8 ± 138,9 (%76) | 972,8 ± 264,5 (%86) | 1 442,8 ± 390,2 (%90) |
|  | ↳ R2, aynı anda varan her ekip kendisi keşfeder (duyarlılık) | 33,6 ± 12,1 (%18) | 283,6 ± 62,4 (%64) | 534,9 ± 113,1 (%77) | 1 035,9 ± 215,7 (%87) | 1 536,9 ± 318,4 (%91) |
|  | R1 + R2 (ek, makalede tanımlı değil) | 20,2 ± 9,3 (%11) | 232,7 ± 56,7 (%60) | 447,2 ± 105,8 (%74) | 874,2 ± 202,7 (%85) | 1 301,2 ± 299,6 (%89) |
| v2-emsr-strict | R0 — naif ajan | 0,8 ± 1,1 (%1) | 13,8 ± 12,4 (%8) | 26,8 ± 23,9 (%14) | 52,8 ± 47,1 (%22) | 78,8 ± 70,3 (%28) |
|  | R1 — görüş mesafeli (d_g = 100 m) | 0,4 ± 0,8 (%0) | 9,9 ± 9,3 (%6) | 19,4 ± 17,9 (%11) | 38,4 ± 35,2 (%18) | 57,4 ± 52,5 (%24) |
|  | R2 — bilgi paylaşan filo | 0,8 ± 1,1 (%1) | 14,4 ± 13,4 (%8) | 27,9 ± 25,9 (%14) | 54,9 ± 50,9 (%23) | 81,9 ± 75,8 (%29) |
|  | ↳ R2, aynı anda varan her ekip kendisi keşfeder (duyarlılık) | 0,8 ± 1,1 (%1) | 14,4 ± 13,4 (%8) | 27,9 ± 25,9 (%14) | 54,9 ± 50,9 (%23) | 81,9 ± 75,8 (%29) |
|  | R1 + R2 (ek, makalede tanımlı değil) | 0,6 ± 1,0 (%0) | 9,9 ± 9,3 (%6) | 19,4 ± 17,9 (%11) | 38,4 ± 35,2 (%18) | 57,4 ± 52,5 (%24) |
| v2-emsr-medium | R0 — naif ajan | 50,2 ± 30,6 (%23) | 350,7 ± 167,4 (%66) | 651,2 ± 304,7 (%78) | 1 252,2 ± 579,5 (%87) | 1 853,2 ± 854,4 (%90) |
|  | R1 — görüş mesafeli (d_g = 100 m) | 33,9 ± 21,2 (%17) | 218,4 ± 95,5 (%56) | 402,9 ± 170,6 (%70) | 771,9 ± 321,0 (%81) | 1 140,9 ± 471,4 (%86) |
|  | R2 — bilgi paylaşan filo | 44,7 ± 22,2 (%22) | 244,8 ± 79,6 (%60) | 461,8 ± 149,4 (%73) | 881,8 ± 281,5 (%84) | 1 301,8 ± 413,7 (%88) |
|  | ↳ R2, aynı anda varan her ekip kendisi keşfeder (duyarlılık) | 44,7 ± 22,2 (%22) | 249,8 ± 78,4 (%60) | 459,3 ± 141,3 (%73) | 878,3 ± 267,2 (%84) | 1 297,3 ± 393,3 (%88) |
|  | R1 + R2 (ek, makalede tanımlı değil) | 32,6 ± 17,5 (%17) | 171,4 ± 46,4 (%52) | 311,3 ± 82,5 (%66) | 593,4 ± 158,6 (%78) | 873,4 ± 232,3 (%84) |
| v2-emsr-loose | R0 — naif ajan | 50,9 ± 31,1 (%23) | 357,9 ± 172,2 (%66) | 664,9 ± 313,8 (%78) | 1 278,9 ± 597,1 (%87) | 1 892,9 ± 880,5 (%91) |
|  | R1 — görüş mesafeli (d_g = 100 m) | 34,2 ± 21,4 (%17) | 222,7 ± 98,0 (%57) | 411,2 ± 175,4 (%70) | 788,2 ± 330,3 (%82) | 1 165,2 ± 485,2 (%87) |
|  | R2 — bilgi paylaşan filo | 45,4 ± 22,6 (%22) | 252,0 ± 81,1 (%61) | 475,5 ± 153,4 (%74) | 908,5 ± 288,9 (%84) | 1 341,5 ± 424,5 (%89) |
|  | ↳ R2, aynı anda varan her ekip kendisi keşfeder (duyarlılık) | 45,4 ± 22,6 (%22) | 256,9 ± 80,4 (%61) | 472,9 ± 144,7 (%74) | 904,9 ± 273,7 (%84) | 1 336,9 ± 402,7 (%89) |
|  | R1 + R2 (ek, makalede tanımlı değil) | 32,9 ± 17,7 (%17) | 175,7 ± 48,6 (%52) | 319,6 ± 86,4 (%66) | 609,7 ± 166,1 (%79) | 897,7 ± 243,2 (%84) |
| drone-sentetik | R0 — naif ajan | 0,9 ± 0,8 (%5) | 16,9 ± 14,9 (%42) | 32,9 ± 29,4 (%55) | 64,8 ± 58,4 (%67) | 96,8 ± 87,4 (%73) |
|  | R1 — görüş mesafeli (d_g = 100 m) | 0,2 ± 0,3 (%1) | 14,7 ± 11,7 (%40) | 29,2 ± 23,3 (%54) | 58,2 ± 46,7 (%66) | 87,2 ± 70,0 (%72) |
|  | R2 — bilgi paylaşan filo | 0,9 ± 0,8 (%5) | 11,3 ± 8,2 (%37) | 21,9 ± 15,8 (%50) | 42,9 ± 31,0 (%63) | 63,9 ± 46,3 (%70) |
|  | ↳ R2, aynı anda varan her ekip kendisi keşfeder (duyarlılık) | 0,9 ± 0,8 (%5) | 16,4 ± 13,8 (%42) | 31,9 ± 27,3 (%55) | 62,9 ± 54,1 (%67) | 93,8 ± 81,0 (%72) |
|  | R1 + R2 (ek, makalede tanımlı değil) | 0,2 ± 0,3 (%1) | 9,7 ± 6,1 (%34) | 19,2 ± 12,1 (%48) | 38,2 ± 24,0 (%62) | 57,2 ± 36,0 (%69) |
| drone-emsr-loose | R0 — naif ajan | 0,3 ± 0,1 (%1) | 10,3 ± 4,2 (%34) | 20,3 ± 8,3 (%49) | 40,3 ± 16,4 (%63) | 60,3 ± 24,6 (%70) |
|  | R1 — görüş mesafeli (d_g = 100 m) | 0,0 ± 0,0 (%0) | 10,0 ± 4,1 (%33) | 20,0 ± 8,2 (%49) | 40,0 ± 16,3 (%63) | 60,0 ± 24,5 (%70) |
|  | R2 — bilgi paylaşan filo | 0,3 ± 0,1 (%1) | 4,8 ± 1,7 (%20) | 9,3 ± 3,3 (%32) | 18,3 ± 6,4 (%47) | 27,3 ± 9,6 (%56) |
|  | ↳ R2, aynı anda varan her ekip kendisi keşfeder (duyarlılık) | 0,3 ± 0,1 (%1) | 10,3 ± 4,2 (%34) | 20,3 ± 8,3 (%49) | 40,3 ± 16,4 (%63) | 60,3 ± 24,6 (%70) |
|  | R1 + R2 (ek, makalede tanımlı değil) | 0,0 ± 0,0 (%0) | 4,5 ± 1,6 (%19) | 9,0 ± 3,2 (%31) | 18,0 ± 6,3 (%47) | 27,0 ± 9,5 (%56) |
| drone-model-z18-r0 | R0 — naif ajan | 0,0 ± 0,0 (%0) | 1,0 ± 2,1 (%5) | 2,0 ± 4,2 (%8) | 4,0 ± 8,4 (%11) | 6,0 ± 12,6 (%13) |
|  | R1 — görüş mesafeli (d_g = 100 m) | 0,0 ± 0,0 (%0) | 1,0 ± 2,1 (%5) | 2,0 ± 4,2 (%8) | 4,0 ± 8,4 (%11) | 6,0 ± 12,6 (%13) |
|  | R2 — bilgi paylaşan filo | 0,0 ± 0,0 (%0) | 1,0 ± 2,1 (%5) | 2,0 ± 4,2 (%8) | 4,0 ± 8,4 (%11) | 6,0 ± 12,6 (%13) |
|  | ↳ R2, aynı anda varan her ekip kendisi keşfeder (duyarlılık) | 0,0 ± 0,0 (%0) | 1,0 ± 2,1 (%5) | 2,0 ± 4,2 (%8) | 4,0 ± 8,4 (%11) | 6,0 ± 12,6 (%13) |
|  | R1 + R2 (ek, makalede tanımlı değil) | 0,0 ± 0,0 (%0) | 1,0 ± 2,1 (%5) | 2,0 ± 4,2 (%8) | 4,0 ± 8,4 (%11) | 6,0 ± 12,6 (%13) |
| drone-model-z19-r15 | R0 — naif ajan | 0,0 ± 0,0 (%0) | 0,5 ± 1,6 (%8) | 1,0 ± 3,2 (%9) | 2,0 ± 6,3 (%9) | 3,0 ± 9,5 (%9) |
|  | R1 — görüş mesafeli (d_g = 100 m) | 0,0 ± 0,0 (%0) | 0,5 ± 1,6 (%8) | 1,0 ± 3,2 (%9) | 2,0 ± 6,3 (%9) | 3,0 ± 9,5 (%9) |
|  | R2 — bilgi paylaşan filo | 0,0 ± 0,0 (%0) | 0,5 ± 1,6 (%8) | 1,0 ± 3,2 (%9) | 2,0 ± 6,3 (%9) | 3,0 ± 9,5 (%9) |
|  | ↳ R2, aynı anda varan her ekip kendisi keşfeder (duyarlılık) | 0,0 ± 0,0 (%0) | 0,5 ± 1,6 (%8) | 1,0 ± 3,2 (%9) | 2,0 ± 6,3 (%9) | 3,0 ± 9,5 (%9) |
|  | R1 + R2 (ek, makalede tanımlı değil) | 0,0 ± 0,0 (%0) | 0,5 ± 1,6 (%8) | 1,0 ± 3,2 (%9) | 2,0 ± 6,3 (%9) | 3,0 ± 9,5 (%9) |

## Doğrulama

"R0 = naive_compare": yeni simülatörün R0 modu, mevcut klasik ajanın sonucunu görev görev (mesafe ve keşif sayısı) birebir verdi mi. "Eski tarama": bu taramanın QuakeMind/R0 toplamları ve afetzede yerleşimleri, referanssız taramayla tohum tohum aynı mı.

| Yapılandırma | R0 = naive_compare (görev) | Eski taramayla aynı (tohum) | Referans hesabı (sn / tohum) |
|---|---|---|---|
| v2-sentetik-8ilce | 178 / 178 | 10 / 10 (multi_seed) | 18,6 ± 6,4 |
| v2-sentetik-4ilce | 130 / 130 | 10 / 10 (multi_seed) | 16,6 ± 5,3 |
| v2-emsr-strict | 130 / 130 | 10 / 10 (multi_seed) | 6,2 ± 1,2 |
| v2-emsr-medium | 130 / 130 | 10 / 10 (multi_seed) | 21,0 ± 7,1 |
| v2-emsr-loose | 130 / 130 | 10 / 10 (multi_seed) | 30,3 ± 23,1 |
| drone-sentetik | 87 / 87 | 10 / 10 (multi_seed) | 0,3 ± 0,1 |
| drone-emsr-loose | 90 / 90 | 10 / 10 (multi_seed) | 0,2 ± 0,1 |
| drone-model-z18-r0 | 90 / 90 | 10 / 10 (multi_seed) | 0,2 ± 0,1 |
| drone-model-z19-r15 | 21 / 21 | 10 / 10 (multi_seed) | 0,1 ± 0,1 |
