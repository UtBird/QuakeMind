# Kapanma yer gerçeği — insan etiketleyici kiti

Makale §4.3 / Tablo 13'teki kör etiketleme bugüne kadar **yalnız bir yapay zekâ modeli
(Claude)** tarafından yapıldı (`../etiketler_defne_elektrik.json`). Bu kit, aynı 33 kesiti
bir insanın etiketlemesi ve iki etiketleyici arasındaki uyumun ölçülmesi için hazırlandı.

**Durum (28 Eylül 2026):** bir yazar etiketledi (`../etiketler_insan_1.json`), uyum
`../uyum.json`'da. Makale artık insan etiketini esas alıyor (kesinlik 4/5, duyarlılık ≈%9);
Claude ikinci görüş (κ = 0,13). Yeni bir etiketleyici eklemek için aşağıdaki adımlar geçerli.

## Nasıl etiketlenir (yaklaşık 20 dakika)

1. `etiketle.html` dosyasını tarayıcıda açın (çift tıklayın). İnternet gerekmez.
2. Adınızı yazın. Her kesit için **kapalı / açık / kararsız** seçin:
   - **kapalı** — parçanın belirgin bir bölümünü moloz ya da enkaz kütlesi örtüyor
   - **açık** — boyunca sürekli ve geçilebilir bir koridor görülüyor (asfalt, toprak, araç)
   - **kararsız** — gölge, çözünürlük ya da çizgi görünür bir sokağı takip etmiyor
3. Seçimler tarayıcıda saklanır; sayfayı kapatıp sonra devam edebilirsiniz.
4. 33 kesitin hepsi bitince **İndir**'e basın. Çıkan `etiketler_<ad>.json` dosyasını bu
   klasörün bir üstüne (`benchmark/kapanma_yer_gercegi/`) koyun.

**Etiketleme bitmeden** `../anahtar_tam_defne_elektrik.json` dosyasını açmayın; içinde
modelin her kesit için ne dediği yazılı. Kör olmak ölçümün şartı: etiketleyici tahmini
bilirse etiketi ona doğru kayar.

## Ölçüm

`backend/` içinden:

```
python araclar_kapanma_uyum.py benchmark/kapanma_yer_gercegi/anahtar_tam_defne_elektrik.json \
    benchmark/kapanma_yer_gercegi/etiketler_defne_elektrik.json \
    benchmark/kapanma_yer_gercegi/etiketler_<ad>.json --cikti benchmark/kapanma_yer_gercegi/uyum.json
```

Betik her etiketleyici için kesinliği (Wilson %95 aralığıyla), duyarlılık kestirimini ve
yargılanamayan oranı, iki etiketleyici için de Cohen κ'yı (üç sınıflı ve kararsız hariç
ikili) yazar. Claude etiketleriyle makaledeki sayıları aynen üretir: 3/3, Wilson 0,44–1,00,
duyarlılık 0,110, yargılanamayan %30.

## Kaynak

Kesitler `araclar_kapanma_etiketle.py` ile tohum 7'den yeniden üretildi (28 Eylül 2026).
Aynı alan, aynı model (`unet_mitb4_p2_t42`), 118 aday parça, modelin kapalı dediği 5 parça,
açık dediklerinden %24,78 örneklem, 33 kesit.
