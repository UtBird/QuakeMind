import { PathLayer, PolygonLayer, ScatterplotLayer, TextLayer } from '@deck.gl/layers'
import { PathStyleExtension } from '@deck.gl/extensions'
import type { Layer, PickingInfo } from '@deck.gl/core'
import type { KatmanId } from '@/durum/konsolDurumu'
import { adKatmanlari, altlikKatmanlari, ipucuKutusu, type EtiketSeviyesi } from '@/harita/katmanlar'
import { tokenPx, tokenRenk } from '@/harita/tokenRenk'
import type { AltlikVerisi, Etiket } from '@/veri/altlik'
import type { SosCagrisi } from '@/veri/sorgular'
import { GOREV_DURUMU, acikGorev, type Gorev } from '@/veri/gorev'
import { dogruluk, saatte, sureMetni, tarihSaat } from '@/lib/bicim'
import { mesafeMetni } from './konum'
import { ISLEM_DURUMU } from './etiketler'
import { YER_TURLERI, yerAdi } from './yerTurleri'
import type { CevreYaniti, HasarBolgesi, KapaliYol, YakinYer } from './veri'

/* ---------------------------------------------------------------------------
   Afetzede haritasının katmanları (J-50). Altlık konsolla aynı (kendi OSM
   verimiz); üstünde yalnız afetzedenin işine yarayanlar: konumu, yakındaki
   yerler, kendi çağrıları ve seçtiği yere yollar üzerinden yürüme rotası
   (J-44; rota yokken kuş uçuşu yön çizgisi). Başka afetzedenin çağrısı ve ekip konumu burada YOK (J-42).
   İstisna (J-54, kullanıcı kararı): afetzedenin KENDİ çağrısına giden ekip, görev açıkken ve
   ekip konumunu paylaştıysa görünür. Ekipten çağrıya araç rotası çizilir (J-55); yol ağı
   dışındaysa kesik düz çizgi (yön, yol değil).
--------------------------------------------------------------------------- */

const ALTLIK_ACIK = { yollar: true, yapilar: true } as Record<KatmanId, boolean>
const KESIK = new PathStyleExtension({ dash: true })

export type HaritaKonumu = {
  lon: number
  lat: number
  kaynak: 'gps' | 'mahalle'
  dogrulukM?: number
  ad?: string
}

export type AfetzedeKatmanGirdisi = {
  altlik: AltlikVerisi[]
  altlikYapiGorunur: boolean
  bolgeAdlari: Etiket[]
  adSeviyesi: EtiketSeviyesi
  yerler: YakinYer[]
  secili: YakinYer | null
  konum: HaritaKonumu | null
  cagrilar: SosCagrisi[]
  /** [lon, lat] dizisi: yürüme rotası (kendi yol ağımız ya da yedek dış servis). */
  rota: [number, number][] | null
  /** Çevredeki tehlike (J-180): kapalı yollar ve hasar bölgeleri; gizlenebilir. */
  cevre?: CevreYaniti | null
}

export function afetzedeKatmanlari(g: AfetzedeKatmanGirdisi): Layer[] {
  const L: Layer[] = [...altlikKatmanlari(g.altlik, ALTLIK_ACIK, g.altlikYapiGorunur)]
  const zemin = tokenRenk('--color-ground')

  // Çevredeki tehlike (J-180): altlığın üstünde, adların ve rotanın altında.
  // Kırmızı ve turuncu burada hasar anlamında (ARAYUZ §6).
  if (g.cevre) {
    const kritik = tokenRenk('--color-crit')
    const yuksek = tokenRenk('--color-high')
    if (g.cevre.hasarBolgeleri.length) {
      L.push(
        new PolygonLayer<HasarBolgesi>({
          id: 'cevre-hasar',
          data: g.cevre.hasarBolgeleri,
          getPolygon: ({ kare: [s, w, n, e] }) => [
            [w, s],
            [e, s],
            [e, n],
            [w, n],
          ],
          getFillColor: (d) => (d.seviye === 3 ? [...kritik, 110] : d.seviye === 2 ? [...yuksek, 95] : [...yuksek, 55]),
          getLineColor: (d) => (d.seviye === 3 ? [...kritik, 220] : [...yuksek, 200]),
          lineWidthMinPixels: 1,
          stroked: true,
          pickable: true,
        }),
      )
    }
    const cizgili = g.cevre.kapaliYollar.filter((d) => (d.cizgi?.length ?? 0) >= 2)
    const noktali = g.cevre.kapaliYollar.filter((d) => (d.cizgi?.length ?? 0) < 2)
    const yol = (d: KapaliYol) => (d.cizgi ?? []).map(([enlem, boylam]) => [boylam, enlem] as [number, number])
    if (cizgili.length) {
      L.push(
        new PathLayer<KapaliYol>({
          id: 'cevre-kapali-zemin',
          data: cizgili,
          getPath: yol,
          getColor: [...zemin, 255],
          getWidth: 9,
          widthUnits: 'pixels',
          capRounded: true,
        }),
        new PathLayer<KapaliYol>({
          id: 'cevre-kapali',
          data: cizgili,
          getPath: yol,
          getColor: [...kritik, 255],
          getWidth: 5,
          widthUnits: 'pixels',
          capRounded: true,
          pickable: true,
        }),
      )
    }
    if (noktali.length) {
      L.push(
        new ScatterplotLayer<KapaliYol>({
          id: 'cevre-kapali',
          data: noktali,
          getPosition: (d) => [d.lon, d.lat],
          getRadius: 6,
          radiusUnits: 'pixels',
          getFillColor: [...kritik, 255],
          stroked: true,
          getLineColor: [...zemin, 255],
          lineWidthMinPixels: 2,
          pickable: true,
        }),
      )
    }
  }
  L.push(...adKatmanlari(g.altlik, g.bolgeAdlari, g.adSeviyesi))

  // Yürüme rotası yolların üstünden: zemin renginde kenar + vurgu rengi.
  if (g.rota && g.rota.length > 1) {
    const veri = [{ yol: g.rota }]
    L.push(
      new PathLayer<{ yol: [number, number][] }>({
        id: 'rota-kenari',
        data: veri,
        getPath: (d) => d.yol,
        getColor: zemin,
        getWidth: 9,
        widthUnits: 'pixels',
        capRounded: true,
        jointRounded: true,
      }),
      new PathLayer<{ yol: [number, number][] }>({
        id: 'sokak-rotasi',
        data: veri,
        getPath: (d) => d.yol,
        getColor: tokenRenk('--color-accent'),
        getWidth: 5,
        widthUnits: 'pixels',
        capRounded: true,
        jointRounded: true,
      }),
    )
  }

  // Rota yokken (hesaplanıyor ya da bölgenin yol ağı yok) seçili yere kuş
  // uçuşu kesikli çizgi: yol değil, yön ve uzaklık göstergesi.
  if (g.konum && g.secili && !(g.rota && g.rota.length > 1)) {
    L.push(
      new PathLayer<{ yol: [number, number][] }, { getDashArray: [number, number] }>({
        id: 'kus-ucusu',
        data: [{ yol: [[g.konum.lon, g.konum.lat], [g.secili.lon, g.secili.lat]] }],
        getPath: (d) => d.yol,
        getColor: tokenRenk('--color-ink-2'),
        getWidth: 2,
        widthUnits: 'pixels',
        getDashArray: [4, 3],
        extensions: [KESIK],
      }),
    )
  }

  L.push(
    new ScatterplotLayer<YakinYer>({
      id: 'yerler',
      data: g.yerler,
      getPosition: (d) => [d.lon, d.lat],
      getFillColor: (d) => tokenRenk(YER_TURLERI[d.tur].renk),
      getLineColor: zemin,
      getRadius: (d) => (g.secili?.id === d.id ? 12 : 9),
      radiusUnits: 'pixels',
      stroked: true,
      lineWidthUnits: 'pixels',
      getLineWidth: 2,
      pickable: true,
      updateTriggers: { getRadius: g.secili?.id },
    }),
    new TextLayer<YakinYer>({
      id: 'yer-harfleri',
      data: g.yerler,
      getPosition: (d) => [d.lon, d.lat],
      getText: (d) => YER_TURLERI[d.tur].harf,
      getSize: tokenPx('--text-micro'),
      getColor: zemin,
      fontFamily: 'IBM Plex Sans, sans-serif',
      fontWeight: 600,
      characterSet: 'auto',
      getTextAnchor: 'middle',
      getAlignmentBaseline: 'center',
    }),
  )

  if (g.secili) {
    L.push(
      new ScatterplotLayer<YakinYer>({
        id: 'secili-yer',
        data: [g.secili],
        getPosition: (d) => [d.lon, d.lat],
        getRadius: 17,
        radiusUnits: 'pixels',
        filled: false,
        stroked: true,
        getLineColor: tokenRenk('--color-ink'),
        lineWidthUnits: 'pixels',
        getLineWidth: 2,
      }),
    )
  }

  // Kendi çağrısına gelen ekip (J-54): ekibin son bildirdiği konum ve çağrıya
  // rotası (J-55). Rota yoksa kesik düz çizgi: yol değil, yöndür.
  const gelenler = gelenEkipler(g.cagrilar)
  if (gelenler.length) {
    const vurgu = tokenRenk('--color-accent')
    L.push(
      new PathLayer<GelenEkip>({
        id: 'gelen-ekip-rotasi',
        data: gelenler.filter((d) => d.gorev.rota?.length),
        getPath: (d) => d.gorev.rota!,
        getColor: [...vurgu, 230],
        getWidth: 3,
        widthUnits: 'pixels',
        capRounded: true,
        jointRounded: true,
      }),
      new PathLayer<GelenEkip, { getDashArray: [number, number] }>({
        id: 'gelen-ekip-cizgisi',
        data: gelenler.filter((d) => !d.gorev.rota?.length),
        getPath: (d) => [
          [d.lon, d.lat],
          [d.hedefLon, d.hedefLat],
        ],
        getColor: [...vurgu, 220],
        getWidth: 2,
        widthUnits: 'pixels',
        getDashArray: [4, 3],
        extensions: [KESIK],
      }),
      new ScatterplotLayer<GelenEkip>({
        id: 'gelen-ekip',
        data: gelenler,
        getPosition: (d) => [d.lon, d.lat],
        getFillColor: vurgu,
        getLineColor: tokenRenk('--color-ink'),
        getRadius: 8,
        radiusUnits: 'pixels',
        stroked: true,
        lineWidthUnits: 'pixels',
        getLineWidth: 2,
        pickable: true,
      }),
      new TextLayer<GelenEkip>({
        id: 'gelen-ekip-adi',
        data: gelenler,
        getPosition: (d) => [d.lon, d.lat],
        getText: (d) => d.gorev.ekip.ad,
        getSize: tokenPx('--text-small'),
        getColor: tokenRenk('--color-ink'),
        getPixelOffset: [0, -14],
        fontFamily: 'IBM Plex Sans, sans-serif',
        fontWeight: 600,
        characterSet: 'auto',
        fontSettings: { sdf: true },
        outlineWidth: 3,
        outlineColor: [...zemin, 255],
        getTextAnchor: 'middle',
        getAlignmentBaseline: 'bottom',
      }),
    )
  }

  // Kendi çağrıları: aciliyet rengi (kırmızı yalnız aciliyet için).
  L.push(
    new ScatterplotLayer<SosCagrisi>({
      id: 'cagrilarim',
      data: g.cagrilar,
      getPosition: (d) => [d.lon, d.lat],
      getFillColor: tokenRenk('--color-crit'),
      getLineColor: zemin,
      getRadius: 7,
      radiusUnits: 'pixels',
      stroked: true,
      lineWidthUnits: 'pixels',
      getLineWidth: 2,
      pickable: true,
    }),
  )

  if (g.konum) {
    const k = g.konum
    const vurgu = tokenRenk('--color-accent')
    if (k.kaynak === 'gps' && k.dogrulukM) {
      L.push(
        new ScatterplotLayer<HaritaKonumu>({
          id: 'konum-dogruluk',
          data: [k],
          getPosition: (d) => [d.lon, d.lat],
          getRadius: (d) => d.dogrulukM ?? 0,
          radiusUnits: 'meters',
          getFillColor: [...vurgu, 30],
          getLineColor: [...vurgu, 120],
          stroked: true,
          lineWidthUnits: 'pixels',
          getLineWidth: 1,
        }),
      )
    }
    L.push(
      new ScatterplotLayer<HaritaKonumu>({
        id: 'konum',
        data: [k],
        getPosition: (d) => [d.lon, d.lat],
        getRadius: 8,
        radiusUnits: 'pixels',
        // Mahalle merkezi yaklaşık konumdur: içi boş halka.
        filled: k.kaynak === 'gps',
        getFillColor: vurgu,
        stroked: true,
        getLineColor: k.kaynak === 'gps' ? tokenRenk('--color-ink') : vurgu,
        lineWidthUnits: 'pixels',
        getLineWidth: k.kaynak === 'gps' ? 2 : 3,
        pickable: true,
      }),
    )
  }
  return L
}

type GelenEkip = { gorev: Gorev; lon: number; lat: number; hedefLon: number; hedefLat: number }

/** Açık çağrılara giden ve konumunu paylaşan ekipler. */
function gelenEkipler(cagrilar: SosCagrisi[]): GelenEkip[] {
  return cagrilar.flatMap((c) =>
    (c.gorevler ?? [])
      .filter((x) => acikGorev(x) && x.ekipKonumu)
      .map((x) => ({ gorev: x, lon: x.ekipKonumu!.lon, lat: x.ekipKonumu!.lat, hedefLon: c.lon, hedefLat: c.lat })),
  )
}

/** Üstüne gelince bilgi: ne, ne kadar uzak, kaynak ne. */
export function afetzedeIpucu({ object, layer }: PickingInfo) {
  if (!object || !layer) return null
  if (layer.id === 'cevre-hasar') {
    const h = object as HasarBolgesi
    const k = h.kaynaklar
    return ipucuKutusu(
      h.seviye === 3 ? 'Çok hasar bildirilen bölge' : 'Hasar bildirilen bölge',
      [
        `${h.sayi} bildirim (yaklaşık 250 m'lik alan)`,
        [k.uydu && `uydu ${k.uydu}`, k.fotograf && `fotoğraf ${k.fotograf}`, k.metin && `yazılı ihbar ${k.metin}`]
          .filter(Boolean)
          .join(' · '),
        `Son bildirim ${tarihSaat(h.sonZaman)}`,
        'Binalara girme, yıkıntıdan uzak dur.',
      ],
    )
  }
  if (layer.id === 'cevre-kapali') {
    return ipucuKutusu('Kapalı yol', [
      'Uydu görüntüsünden hasar analiziyle bulundu',
      'Yürüme rotası bilinen kapalı yollardan kaçınır.',
    ])
  }
  if (layer.id === 'gelen-ekip') {
    const { gorev: x } = object as GelenEkip
    return ipucuKutusu(x.ekip.ad, [
      `${x.kisiSayisi} kişi · ${GOREV_DURUMU[x.durum].afetzede.toLocaleLowerCase('tr')}`,
      // Konum 10 dakikadan eskiyse süre yazılmaz (kartla aynı kural).
      x.yol && x.ekipKonumu?.zaman && Date.now() - x.ekipKonumu.zaman < 10 * 60_000
        ? `Çağrına yoldan ~${sureMetni(x.yol.sureDk)} (${mesafeMetni(x.yol.mesafeM)}), tahmini`
        : !x.yol && x.kalanM != null
          ? `Çağrına kuş uçuşu ${mesafeMetni(x.kalanM)}`
          : null,
      x.ekipKonumu?.zaman ? `Konumu ${saatte(x.ekipKonumu.zaman)} bildirildi` : null,
    ])
  }
  if (layer.id === 'yerler') {
    const y = object as YakinYer
    return ipucuKutusu(yerAdi(y), [
      YER_TURLERI[y.tur].ad,
      y.adres,
      `Kuş uçuşu ${mesafeMetni(y.mesafeM)}`,
      y.tur === 'toplanma' ? 'Kaynak: AFAD listesi' : 'Kaynak: OpenStreetMap',
      'Tıkla: seç',
    ])
  }
  if (layer.id === 'cagrilarim') {
    const c = object as SosCagrisi
    return ipucuKutusu('Çağrın', [ISLEM_DURUMU[c.durum].ad, tarihSaat(c.zaman)])
  }
  if (layer.id === 'konum') {
    const k = object as HaritaKonumu
    return ipucuKutusu(
      k.kaynak === 'gps' ? 'Konumun' : `${k.ad ?? 'Mahalle'} merkezi`,
      [k.kaynak === 'gps' && k.dogrulukM ? `${dogruluk(k.dogrulukM)} doğruluk` : 'Yaklaşık konum'],
    )
  }
  return null
}
