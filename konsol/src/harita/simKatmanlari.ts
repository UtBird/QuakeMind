import { BitmapLayer, PathLayer, ScatterplotLayer, TextLayer } from '@deck.gl/layers'
import { PathStyleExtension } from '@deck.gl/extensions'
import type { Layer } from '@deck.gl/core'
import type { KatmanId } from '@/durum/konsolDurumu'
import type {
  LatLonCizgi,
  SimGorev,
  SimKameraKaydi,
  SimKenar,
  SimMetinKaydi,
  SimRota,
  SimSonuc,
  SimVaryantId,
} from '@/veri/simulasyon'
import { tokenPx, tokenRenk } from './tokenRenk'
import { goruntuKatmani, type GoruntuKarosu } from './goruntuKatmani'

/* ---------------------------------------------------------------------------
   Tatbikat katmanları (SIMULASYON_SOZLESMESI.md §5 madde 4).

   Sözleşmedeki çizgiler [lat, lon] sırasında; deck.gl [lon, lat] ister.
   Çevirme YALNIZ burada yapılır (`cevir`), başka hiçbir yerde koordinat
   sırası değiştirilmez.

   Renk kuralı (ARAYUZ §6): kırmızı, turuncu ve sarı yalnız hasar ve aciliyet
   içindir. Kapalı kenar kırmızı (geçilmez), cezalı kenar turuncu (hasara
   yakın), riskli rota sarı. Deprem öncesi rota sönük ve kesik: artık geçerli
   olmayan bir yolu gösterir. Seçilen rota vurgu renginde.
--------------------------------------------------------------------------- */

const KESIK = new PathStyleExtension({ dash: true })

const cevir = (cizgi: LatLonCizgi): [number, number][] => cizgi.map(([lat, lon]) => [lon, lat])

export type RotaCizgisi = { rota: SimRota; varyant: SimVaryantId; cizgi: [number, number][] }

/** Sözleşmedeki üç varyantın çizim düzeni: sönük olan altta kalsın. */
const VARYANT_STILI: Record<
  SimVaryantId,
  { renk: `--color-${string}`; alfa: number; genislik: number; kesik: boolean }
> = {
  depremOncesi: { renk: '--color-ink-3', alfa: 170, genislik: 2, kesik: true },
  riskli: { renk: '--color-mid', alfa: 210, genislik: 2.5, kesik: false },
  kapanmali: { renk: '--color-accent', alfa: 235, genislik: 3.5, kesik: false },
}

const CIZIM_SIRASI: SimVaryantId[] = ['depremOncesi', 'riskli', 'kapanmali']

export type SimHaritaGirdisi = {
  katmanlar: Record<KatmanId, boolean>
  sonuc?: SimSonuc | null
  /** Hasar maskesi; jetonla indirilip çözülmüş hâli (veri/simulasyon.ts). */
  maske?: ImageBitmap | null
  varyantlar: Record<SimVaryantId, boolean>
  /** Kolların fiilen sürdüğü yollar (uç: `izlenenYollar`). */
  izlenenYollar?: Record<string, LatLonCizgi[]> | null
  /** Bilmeyen ekibin sürdüğü yol görünsün mü (J-185). */
  izlenenGoster?: boolean
  /** Seçili görev: yalnız o ekip–afetzede çiftinin yolları ve uçları (J-185). */
  seciliGorev?: string | null
  /** Koşulan alanın görüntü kaynağı: tatbikatta zemine MODELİN BAKTIĞI
      görüntü serilir. Bu alanların çoğunda üretilmiş altlık paketi yok
      (ölçüldü, 26 Eylül: Nurdağı'nda zemin bomboş siyahtı) ve zaten doğru
      zemin de altlık değil, enkazın kendisidir — kapanmalar onun üstünde
      okunur. */
  goruntu?: GoruntuKarosu | null
}

/** Zemin katmanı: hasar maskesi. Sokak adlarının ALTINDA çizilir, yoksa
    maske adları örter. Ham raster; poligon çıkarma yükü arayüze bırakılmaz (§2). */
export function simZeminKatmanlari(g: SimHaritaGirdisi): Layer[] {
  const s = g.sonuc
  // Görüntü EN ALTTA: maske ve çizgiler onun üstünde okunur.
  const alt = g.goruntu ? goruntuKatmani(g.goruntu, true) : []
  if (!s?.hasar || !g.katmanlar.simHasar || !g.maske) return alt
  return [
    ...alt,
    new BitmapLayer({
      id: 'sim-hasar',
      image: g.maske,
      bounds: s.hasar.bbox,
      opacity: 0.72,
      textureParameters: { minFilter: 'linear', magFilter: 'linear' },
    }),
  ]
}

/** Veri katmanları: kapanan kenarlar, üç rota, görev uçları. Adların üstünde. */
export function simKatmanlari(g: SimHaritaGirdisi): Layer[] {
  const L: Layer[] = []
  const s = g.sonuc
  if (!s) return L

  // Kapanmalar: cezalı kenarlar altta, kapalı olanlar üstte kalsın.
  if (g.katmanlar.simKapanma && s.kapanma) {
    L.push(
      new PathLayer<SimKenar>({
        id: 'sim-kapanma-cezali',
        data: s.kapanma.cezaliKenarlar ?? [],
        getPath: (d) => cevir(d.cizgi),
        getColor: [...tokenRenk('--color-high'), 200],
        getWidth: 3,
        widthUnits: 'pixels',
        widthMinPixels: 2,
        capRounded: true,
        pickable: true,
      }),
    )
    L.push(
      new PathLayer<SimKenar>({
        id: 'sim-kapanma-kapali',
        data: s.kapanma.kapaliKenarlar ?? [],
        getPath: (d) => cevir(d.cizgi),
        getColor: [...tokenRenk('--color-crit'), 245],
        getWidth: 5,
        widthUnits: 'pixels',
        widthMinPixels: 3,
        capRounded: true,
        pickable: true,
      }),
    )
  }

  // Seçili görev varsa yalnız o çift çizilir (J-185): 5 görevin bütün
  // çizgileri üst üste binince hangi yolun hangi ekibe ait olduğu okunmuyordu.
  const secili = g.seciliGorev ?? null
  const rotalar = (s.rotalar ?? []).filter((r) => !secili || r.gorevId === secili)

  // 3. Üç rota varyantı. Her varyant tek katman: 5 rota için 5 katman değil.
  if (g.katmanlar.simRota && rotalar.length) {
    for (const varyant of CIZIM_SIRASI) {
      if (!g.varyantlar[varyant]) continue
      const stil = VARYANT_STILI[varyant]
      const veri: RotaCizgisi[] = rotalar
        .map((rota) => ({ rota, varyant, cizgi: cevir(rota.varyantlar[varyant]?.cizgi ?? []) }))
        .filter((r) => r.cizgi.length > 1)
      if (!veri.length) continue
      L.push(
        new PathLayer<RotaCizgisi, { getDashArray?: [number, number] }>({
          id: `sim-rota-${varyant}`,
          data: veri,
          getPath: (d) => d.cizgi,
          getColor: [...tokenRenk(stil.renk), stil.alfa],
          getWidth: stil.genislik,
          widthUnits: 'pixels',
          widthMinPixels: 1.5,
          capRounded: true,
          jointRounded: true,
          pickable: true,
          ...(stil.kesik ? { getDashArray: [6, 4] as [number, number], extensions: [KESIK] } : {}),
        }),
      )
    }
  }

  // 3b. FİİLEN SÜRÜLEN yol. Üç varyant PLANLANAN yoldur; manşet sayı ise
  // kapanmayı bilmeyen ekibin gerçekten sürdüğü yoldan gelir (çıkmaza girip
  // geri dönmesi dahil) ve bu haritada hiç çizilmiyordu — kullanıcı hangi
  // çizginin "bilmeseydik" olduğunu soramıyordu (27 Eylül). Sönük ve kalın:
  // altta durur, planlanan güzergâhlar üstünde okunur.
  if (g.katmanlar.simRota && g.izlenenGoster !== false) {
    // Görev başına yol (J-185) varsa ondan; eski koşularda görev bilgisi yok.
    const kollar = s.gorevKollari?.['Kapanmayı bilmeyen ekip']
    const hatlar: LatLonCizgi[] = kollar
      ? kollar
          .filter((k) => (!secili || k.gorevId === secili) && (k.cizgi?.length ?? 0) > 1)
          .map((k) => k.cizgi!)
      : secili
        ? []
        : (s.izlenenYollar?.['Kapanmayı bilmeyen ekip'] ?? [])
    if (hatlar.length) {
      L.push(
        new PathLayer<LatLonCizgi>({
          id: 'sim-izlenen-bilmeyen',
          data: hatlar,
          getPath: (d) => cevir(d),
          getColor: [...tokenRenk('--color-crit'), 110],
          getWidth: 7,
          widthUnits: 'pixels',
          capRounded: true,
          jointRounded: true,
        }),
      )
    }
  }

  // 4. Görevler: ekip üssü gerçek bir tesis (dolu), afetzede üretilen senaryo
  // (içi boş halka). Ayrım renkle değil biçimle de yapılır (§6, ARAYUZ §12).
  if (g.katmanlar.simGorev && s.gorevler?.length && rotalar.length) {
    const uclar = eslestir(s.gorevler, rotalar)
    L.push(
      new ScatterplotLayer<GorevUcu>({
        id: 'sim-gorev-afetzede',
        data: uclar.filter((u) => u.tur === 'afetzede'),
        getPosition: (d) => [d.lon, d.lat],
        getRadius: 7,
        radiusUnits: 'pixels',
        filled: false,
        stroked: true,
        getLineColor: [...tokenRenk('--color-ihbar-sos'), 235],
        lineWidthUnits: 'pixels',
        getLineWidth: 2,
        pickable: true,
      }),
    )
    L.push(
      new ScatterplotLayer<GorevUcu>({
        id: 'sim-gorev-ekip',
        data: uclar.filter((u) => u.tur === 'ekip'),
        getPosition: (d) => [d.lon, d.lat],
        getRadius: 6,
        radiusUnits: 'pixels',
        getFillColor: [...tokenRenk('--color-accent'), 240],
        stroked: true,
        getLineColor: [...tokenRenk('--color-ground'), 220],
        lineWidthUnits: 'pixels',
        getLineWidth: 1.5,
        pickable: true,
      }),
    )
    L.push(
      new TextLayer<GorevUcu>({
        id: 'sim-gorev-adlari',
        data: uclar,
        getPosition: (d) => [d.lon, d.lat],
        // Kısa ad (J-185): "Ekip 4 · mahalle girişi · senaryo" etiketleri
        // birbirinin üstüne biniyordu. Ne olduğu gösterge ve bilgi kartında yazar.
        getText: (d) => d.ad.split(' · ')[0],
        getSize: tokenPx('--text-small'),
        getColor: [...tokenRenk('--color-ink'), 255],
        getPixelOffset: [0, -14],
        fontFamily: 'IBM Plex Sans, sans-serif',
        fontWeight: 600,
        characterSet: 'auto',
        fontSettings: { sdf: true },
        outlineWidth: 3,
        outlineColor: [...tokenRenk('--color-ground'), 255],
        getTextAnchor: 'middle',
        getAlignmentBaseline: 'bottom',
      }),
    )
  }

  /* Yer seviyesi kanallar (J-108). Ayrım renkten BAŞKA biçimle de yapılır
     (ARAYUZ §6): kamera tespiti dolu kare, metin ihbarı dolu üçgen. İkisinin
     de konumu ÜRETİLMİŞTİR; göstergede ve panelde öyle yazar. */
  if (g.katmanlar.simKamera && s.kanallar?.kamera?.kayitlar?.length) {
    L.push(
      new ScatterplotLayer<SimKameraKaydi>({
        id: 'sim-kanal-kamera',
        data: s.kanallar.kamera.kayitlar,
        getPosition: (d) => [d.lon, d.lat],
        // Kare görünsün diye: deck.gl daireyi köşe sayısıyla yaklaşır.
        getRadius: 6,
        radiusUnits: 'pixels',
        getFillColor: [...tokenRenk('--color-ch-cam'), 235],
        stroked: true,
        getLineColor: [...tokenRenk('--color-ground'), 230],
        lineWidthUnits: 'pixels',
        getLineWidth: 1.5,
        pickable: true,
      }),
    )
  }
  if (g.katmanlar.simMetin && s.kanallar?.metin?.kayitlar?.length) {
    L.push(
      new ScatterplotLayer<SimMetinKaydi>({
        id: 'sim-kanal-metin',
        data: s.kanallar.metin.kayitlar,
        getPosition: (d) => [d.lon, d.lat],
        // Aciliyet 1-5 -> yarıçap: acil ihbar gözle daha büyük.
        getRadius: (d) => 4 + d.aciliyet * 0.8,
        radiusUnits: 'pixels',
        getFillColor: [...tokenRenk('--color-ch-nlp'), 230],
        stroked: true,
        getLineColor: [...tokenRenk('--color-ground'), 230],
        lineWidthUnits: 'pixels',
        getLineWidth: 1.5,
        pickable: true,
      }),
    )
  }


  return L
}

export type GorevUcu = {
  id: string
  tur: 'ekip' | 'afetzede'
  ad: string
  lon: number
  lat: number
  gorev: SimGorev
  /** Rotanın "kapanmalara göre" varyantından; yoksa görevdeki ETA. */
  etaDk: number
}

/** Görev kaydı ile rotanın uçlarını eşler: konum rotadan, ad ve ETA görevden. */
function eslestir(gorevler: SimGorev[], rotalar: SimRota[]): GorevUcu[] {
  const uclar: GorevUcu[] = []
  for (const gorev of gorevler) {
    const rota = rotalar.find((r) => r.gorevId === gorev.id)
    if (!rota) continue
    uclar.push({
      id: `${gorev.id}-ekip`,
      tur: 'ekip',
      ad: gorev.ekipAd || rota.baslangic.ad,
      lon: rota.baslangic.lon,
      lat: rota.baslangic.lat,
      gorev,
      etaDk: gorev.etaDk,
    })
    uclar.push({
      id: `${gorev.id}-afetzede`,
      tur: 'afetzede',
      ad: gorev.afetzedeAd || rota.hedef.ad,
      lon: rota.hedef.lon,
      lat: rota.hedef.lat,
      gorev,
      etaDk: gorev.etaDk,
    })
  }
  return uclar
}
