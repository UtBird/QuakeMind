# Çoklu tohum koşusu (E-06)

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
