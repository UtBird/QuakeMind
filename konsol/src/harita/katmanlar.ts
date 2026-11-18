import {
  IconLayer,
  ScatterplotLayer,
  PathLayer,
  PolygonLayer,
  BitmapLayer,
  SolidPolygonLayer,
  TextLayer,
} from '@deck.gl/layers'
import {
  CollisionFilterExtension,
  PathStyleExtension,
  type CollisionFilterExtensionProps,
} from '@deck.gl/extensions'
import type { Layer, PickingInfo } from '@deck.gl/core'
import type { KatmanId } from '@/durum/konsolDurumu'
import {
  KAYNAK_ADI,
  ONCELIK_ADI,
  sosEkBilgi,
  type HasarNoktasi,
  type SosCagrisi,
} from '@/veri/sorgular'
import { GOREV_DURUMU, gorevOzeti, kurumTur, uzaklikMetni, type Ekip } from '@/veri/gorev'
import type { Kutu, Nokta } from '@/durum/secimDurumu'
import type { Yol } from '@/veri/analiz'
import type { AltlikVerisi, Etiket } from '@/veri/altlik'
import { IHBAR_DURUMU, IHBAR_TURU, ihbarKonumu, type Ihbar, type IhbarTuru } from '@/veri/ihbar'
import type { BelirsizlikCemberi } from '@/veri/metin'
import { DEPREM_EN_AZ, type Deprem, type Fay, type Kapanma, type SaglikYeri, type ToplanmaAlani } from '@/veri/katman'
import { VARYANT_ADI, type SimGorev, type SimKenar } from '@/veri/simulasyon'
import { goruntuKatmani } from './goruntuKatmani'
import {
  simKatmanlari,
  simZeminKatmanlari,
  type GorevUcu,
  type RotaCizgisi,
  type SimHaritaGirdisi,
} from './simKatmanlari'
import { mesafe, sureMetni, tarihSaat, tarihSaatYilli } from '@/lib/bicim'
import { tokenPx, tokenRenk } from './tokenRenk'
import { ikon, simgeAdresi, type SimgeTuru } from './simgeler'

/* Yakınlaştırma eşikleri (J-172): harita her ölçekte yalnız o ölçekte işe
   yarayanı çizer. Olaylar (SOS, ihbar) ve ekipler her ölçekte; tek tek uydu
   noktaları, ekip adları ve sağlık tesisleri şehir ölçeğinde. */
export const HASAR_NOKTASI_EN_AZ_ZOOM = 13
export const EKIP_ADI_EN_AZ_ZOOM = 12
export const SAGLIK_EN_AZ_ZOOM = 12

/** IconLayer ortak ayarları: simge piksel boyutunda, renk simgenin kendisinde. */
const SIMGE_ORTAK = {
  sizeUnits: 'pixels' as const,
  getColor: [255, 255, 255, 255] as [number, number, number, number],
  alphaCutoff: 0.05,
  pickable: true,
}

/* Veri katmanları altlıktan belirgin şekilde ayrılır: altlık soğuk ve sönük,
   veri sıcak ve doygun (ARAYUZ §11). Hasar renkleri haritada ve panelde aynıdır. */

const KAYNAK_RENK: Record<HasarNoktasi['kaynak'], [number, number, number, number]> = {
  uydu: [69, 200, 224, 220],
  sos: [255, 92, 92, 220],
  kamera: [242, 193, 78, 220],
  metin: [176, 140, 255, 220],
}

/* Altlık yol hiyerarşisi (ARAYUZ §3, §11): renk token dosyasından, genişlik
   prototipte sınanan değerler (metre; en az 0,7 piksel). */
const YOL_RENGI = [
  '--color-map-motorway',
  '--color-map-primary',
  '--color-map-secondary',
  '--color-map-local',
  '--color-map-track',
] as const
const YOL_GENISLIGI_M = [7, 5, 3.4, 2, 1.4]

/* Adlar (J-41): çakışan ad yazılmaz, önceliği yüksek olan kalır (şehir >
   ilçe > köy > mahalle > büyük yol > sokak). Adlar veri katmanlarının üstünde,
   zemin renginde ince bir haleyle yazılır; yine de sönük tondadır (ARAYUZ §11). */
const CAKISMA = new CollisionFilterExtension()

/** Yakınlaştırmaya göre yazılan adlar: -1 yalnız bölge adları, 0 şehir/ilçe,
    1 +köy, 2 +mahalle, 3 +sokak. */
export type EtiketSeviyesi = -1 | 0 | 1 | 2 | 3

export function etiketKatmani(id: string, data: Etiket[], boy: number, renk: [number, number, number]) {
  return new TextLayer<Etiket, CollisionFilterExtensionProps<Etiket>>({
    id,
    data,
    getPosition: (d) => [d.lon, d.lat],
    getText: (d) => d.ad,
    getAngle: (d) => d.aci,
    getSize: boy,
    getColor: renk,
    fontFamily: 'IBM Plex Sans, sans-serif',
    fontWeight: 500,
    characterSet: 'auto',
    fontSettings: { sdf: true },
    outlineWidth: 3,
    outlineColor: [...tokenRenk('--color-ground'), 255],
    getTextAnchor: 'middle',
    getAlignmentBaseline: 'center',
    extensions: [CAKISMA],
    collisionGroup: 'adlar',
    getCollisionPriority: (d) => d.oncelik,
    // Çakışma sınaması adı biraz büyük sayar: adlar birbirine yapışmasın.
    collisionTestProps: { sizeScale: 1.3 },
  })
}

export function adKatmanlari(
  bolgeler: AltlikVerisi[],
  bolgeAdlari: Etiket[],
  seviye: EtiketSeviyesi,
): Layer[] {
  if (seviye < 0) {
    return [etiketKatmani('ad-bolgeler', bolgeAdlari, tokenPx('--text-title'), tokenRenk('--color-ink'))]
  }
  const L: Layer[] = []
  for (const b of bolgeler) {
    const yerSeviyesi = Math.min(seviye, 2) as 0 | 1 | 2
    L.push(
      etiketKatmani(
        `ad-${b.id}-yer-${yerSeviyesi}`,
        b.yerAdlari[yerSeviyesi],
        tokenPx(yerSeviyesi === 0 ? '--text-subtitle' : '--text-small'),
        tokenRenk(yerSeviyesi === 0 ? '--color-ink' : '--color-ink-2'),
      ),
    )
    if (seviye >= 3) {
      L.push(
        etiketKatmani(
          `ad-${b.id}-sokak`,
          b.sokakAdlari,
          tokenPx('--text-micro'),
          tokenRenk('--color-ink-3'),
        ),
      )
    }
  }
  return L
}

/** Kendi verimizden altlık: su, yapılar, nehirler, yollar — en altta çizilir.
    Yapılar yalnız `yapiGorunur` iken kurulur: uzak yakınlaştırmada seçilmezler,
    ama birkaç bölgenin 300 bini aşan çokgenini üçgenlemek arayüzü dondururdu. */
export function altlikKatmanlari(
  bolgeler: AltlikVerisi[],
  k: Record<KatmanId, boolean>,
  yapiGorunur: boolean,
): Layer[] {
  const L: Layer[] = []
  for (const b of bolgeler) {
    L.push(
      new SolidPolygonLayer({
        id: `altlik-${b.id}-su`,
        data: b.su,
        _normalize: false,
        getFillColor: tokenRenk('--color-map-water'),
      }),
    )
    if (k.yapilar && yapiGorunur) {
      L.push(
        new SolidPolygonLayer({
          id: `altlik-${b.id}-yapi`,
          data: b.yapilar,
          _normalize: false,
          getFillColor: tokenRenk('--color-map-building'),
        }),
      )
    }
    L.push(
      new PathLayer({
        id: `altlik-${b.id}-nehir`,
        data: b.nehirler,
        _pathType: 'open',
        getColor: tokenRenk('--color-map-water'),
        getWidth: 8,
        widthUnits: 'meters',
        widthMinPixels: 1.4,
      }),
    )
    if (k.yollar) {
      for (const y of b.yollar) {
        L.push(
          new PathLayer({
            id: `altlik-${b.id}-yol-${y.sinif}`,
            data: y.veri,
            _pathType: 'open',
            getColor: tokenRenk(YOL_RENGI[y.sinif]),
            getWidth: YOL_GENISLIGI_M[y.sinif],
            widthUnits: 'meters',
            widthMinPixels: 0.7,
            widthMaxPixels: 14,
            capRounded: true,
            jointRounded: true,
          }),
        )
      }
    }
  }
  return L
}

export type KatmanGirdisi = {
  katmanlar: Record<KatmanId, boolean>
  /** Görünen bölgelerin altlık paketleri. */
  altlik?: AltlikVerisi[]
  /** Yakınlaştırma yapıların seçilebileceği kadar mı (bkz. altlikKatmanlari). */
  altlikYapiGorunur?: boolean
  /** Toplanma alanları şehir ölçeğinde çizilir (TOPLANMA_EN_AZ_ZOOM). */
  toplanmaGorunur?: boolean
  /** Haritanın yakınlaştırması: yoğun katmanlar eşiğin altında çizilmez (J-172). */
  zoom?: number
  /** Hastane ve sağlık merkezleri (OSM). */
  saglik?: SaglikYeri[]
  /** Deprem riski modu (J-173): il merkezleri risk renginde, seçili ilin hesap alanı. */
  risk?: {
    iller: { il: string; lat: number; lon: number; skor: number; seviye: string; fayKm: number }[]
    secili: string | null
    halkalar: { lon: number; lat: number; kisaKm: number; uzunKm: number } | null
  } | null
  /** Uzak yakınlaştırmada yazılan bölge adları (altlık kataloğundan). */
  bolgeAdlari?: Etiket[]
  /** Isı katmanının örtücülüğü; yakınlaştıkça azalır (bkz. KatmanKopru). */
  isiOrtuculugu?: number
  etiketSeviyesi?: EtiketSeviyesi
  hasar: HasarNoktasi[]
  sos: SosCagrisi[]
  ekipler: Ekip[]
  seciliSos: string | null
  /** Afetzede ihbarları (J-51) ve modun gösterdiği türler. */
  ihbarlar?: Ihbar[]
  ihbarTurleri?: readonly IhbarTuru[]
  seciliIhbar?: string | null
  /** Seçili kaydın konum belirsizliği (J-170): metinden çözülen adresin ya da
      cihaz konumunun sapabileceği alan. `nokta`: kayıt haritada başka katmanda
      yoksa (konsoldaki deneme analizi) merkezi de çizilir. */
  belirsizlik?: KonumBelirsizligi | null
  /** Yol ve rota modu (J-171): seçilen rota, kaçınmadan kıyası, öteki adaylar ve uçlar. [boylam, enlem] */
  guzergah?: {
    ana: [number, number][] | null
    kiyas: [number, number][] | null
    adaylar: [number, number][][]
    bas: [number, number] | null
    hedef: [number, number] | null
  } | null
  /** Soldan seçilen görüntü kaynağının karosu (Hasar analizi modu). */
  goruntu?: { url: string; kunye: string; ortuculuk?: number } | null
  /** Bitmiş hasar analizinin yol geometrisi. */
  analiz?: { kapali: Yol[]; acik: Yol[] } | null
  /** Tatbikat koşusunun katmanları (SIMULASYON_SOZLESMESI.md §5). */
  simulasyon?: SimHaritaGirdisi
  /** Başvuru katmanları (J-56); her biri kendi ucundan gelir. */
  kapanmalar?: Kapanma[]
  depremler?: Deprem[]
  faylar?: Fay[]
  toplanma?: ToplanmaAlani[]
  /** Kanalların ağırlıklı karışımından çıkan ısı dokusu. */
  isi?: { goruntu: ImageData; sinirlar: [number, number, number, number] } | null
  /** Analiz alanı seçimi: kesinleşmiş şekil ve çizim sürerken taslak. */
  secim?: {
    kutu: Kutu | null
    cokgen: Nokta[] | null
    taslak: { kutu?: Kutu; nokta?: Nokta[] } | null
  }
}

type KonumBelirsizligi = BelirsizlikCemberi
type RiskIli = NonNullable<KatmanGirdisi['risk']>['iller'][number]

function kutuHalkasi(k: Kutu): Nokta[] {
  return [
    [k[0], k[1]],
    [k[2], k[1]],
    [k[2], k[3]],
    [k[0], k[3]],
  ]
}

export function katmanlariKur(g: KatmanGirdisi): Layer[] {
  const L: Layer[] = altlikKatmanlari(g.altlik ?? [], g.katmanlar, g.altlikYapiGorunur ?? false)

  // Seçilen uydu/drone görüntüsü: altlığın hemen ÜSTÜNDE, olay ve analiz
  // katmanlarının ALTINDA. Modelin ne gördüğü ekranda olsun (kural 1).
  L.push(...goruntuKatmani(g.goruntu ?? null, g.katmanlar.analizGoruntusu))

  // Fay hatları (J-56): jeolojik başvuru, bir olay değil. Bu yüzden altlığın
  // hemen üstünde, kesik ve sönük çizilir; aciliyet renkleri (kırmızı, turuncu,
  // sarı) hasara ayrılı olduğu için kendi token'ı var. GEM veri setinde ad alanı
  // boş olduğundan çizgilerin etiketi yazılmaz.
  if (g.katmanlar.faylar && g.faylar?.length) {
    L.push(
      new PathLayer<Fay, { getDashArray: [number, number] }>({
        id: 'faylar',
        data: g.faylar,
        getPath: (d) => d.cizgi,
        getColor: [...tokenRenk('--color-fay'), 205],
        getWidth: 2,
        widthUnits: 'pixels',
        widthMinPixels: 1.5,
        getDashArray: [7, 4],
        extensions: [KESIK],
        capRounded: true,
        pickable: true,
      }),
    )
  }

  // Isı haritası: kanal ızgaraları sunucudan gelir, karışım istemcide yapılır
  // ve doku olarak çizilir. İkinci bir bulanıklaştırma YOK (MIMARI §5).
  if (g.katmanlar.isi && g.isi) {
    L.push(
      new BitmapLayer({
        id: 'isi',
        image: g.isi.goruntu,
        bounds: g.isi.sinirlar,
        opacity: g.isiOrtuculugu ?? 0.72,
        textureParameters: { minFilter: 'linear', magFilter: 'linear' },
      }),
    )
  }


  // Analiz sonucu: önce açık yollar (sönük), sonra kapalı olanlar (kırmızı),
  // böylece kapalı segmentler her zaman üstte kalır.
  if (g.katmanlar.analizSonucu && g.analiz) {
    L.push(
      new PathLayer<Yol>({
        id: 'analiz-acik',
        data: g.analiz.acik,
        getPath: (d) => d,
        getColor: [92, 104, 126, 150],
        getWidth: 2,
        widthUnits: 'pixels',
        widthMinPixels: 1,
        capRounded: true,
        jointRounded: true,
      }),
    )
    L.push(
      new PathLayer<Yol>({
        id: 'analiz-kapali',
        data: g.analiz.kapali,
        getPath: (d) => d,
        // Kapalı yol = kritik durum rengi; panelde de aynı kırmızı kullanılır.
        getColor: [255, 92, 92, 255],
        getWidth: 5,
        widthUnits: 'pixels',
        widthMinPixels: 3,
        capRounded: true,
        jointRounded: true,
        pickable: true,
      }),
    )
  }

  // Yol kapanmaları (J-56): depoda duran kalıcı kayıtlar. Bunlar NOKTA, çünkü
  // analiz biterken kapalı yol parçasının yalnız orta noktası yazılıyor
  // (`cekirdek._kapanmalari_depoya_yaz`). Çizgi olarak gösterilseydi kapalı
  // parçanın uzunluğunu biliyormuş gibi olurduk. Renk hasar turuncusu.
  if (g.katmanlar.hasarliYollar && g.kapanmalar?.length) {
    // Çizgisi olan kapanma KIRMIZI ÇİZGİ olarak çizilir (J-58). Eski kayıtlarda
    // yalnız orta nokta var; onlar nokta kalır, yoksa harita kapanmaları nokta
    // tarlası gibi gösteriyordu.
    const cizgili = g.kapanmalar.filter((d) => (d.cizgi?.length ?? 0) >= 2)
    const noktali = g.kapanmalar.filter((d) => (d.cizgi?.length ?? 0) < 2)
    if (cizgili.length) {
      L.push(
        new PathLayer<Kapanma>({
          id: 'yol-kapanmalari-cizgi',
          data: cizgili,
          getPath: (d) =>
            (d.cizgi ?? []).map(([enlem, boylam]) => [boylam, enlem] as [number, number]),
          getColor: [...tokenRenk('--color-crit'), 235],
          getWidth: 4,
          widthUnits: 'pixels',
          widthMinPixels: 2.5,
          capRounded: true,
          jointRounded: true,
          pickable: true,
        }),
      )
    }
    L.push(
      new IconLayer<Kapanma>({
        ...SIMGE_ORTAK,
        id: 'yol-kapanmalari',
        data: noktali,
        getPosition: (d) => [d.lon, d.lat],
        getIcon: () => ikon('kapanma'),
        getSize: 18,
      }),
    )
  }

  // Tatbikatın hasar maskesi adların ALTINDA: raster, sokak adlarını örtmesin.
  if (g.simulasyon) L.push(...simZeminKatmanlari(g.simulasyon))

  // Adlar zeminin, ısının ve yolların üstünde, veri noktalarının altında:
  // bir sokak adı SOS noktasının üstüne binmesin (veri önde, ARAYUZ §11).
  L.push(...adKatmanlari(g.altlik ?? [], g.bolgeAdlari ?? [], g.etiketSeviyesi ?? -1))

  // Tatbikatın kenar, rota ve görev katmanları adların üstünde.
  if (g.simulasyon) L.push(...simKatmanlari(g.simulasyon))

  // Depremler (J-56): katalogdan gelen geçmiş kayıtlar, bugünün hasarı değil.
  // Bu yüzden içi boş halka çizilir; dolu nokta olsaydı canlı veriyle karışırdı.
  // Halkanın çapı büyüklüğe göre artar.
  if (g.katmanlar.depremler && g.depremler?.length) {
    L.push(
      new ScatterplotLayer<Deprem>({
        id: 'depremler',
        data: g.depremler,
        getPosition: (d) => [d.lon, d.lat],
        getRadius: (d) => 4 + Math.max(0, d.buyukluk - DEPREM_EN_AZ) * 2.6,
        radiusUnits: 'pixels',
        // İçi çok sönük dolu, kenarı belirgin: küçük halka koyu zeminde kaybolmasın.
        filled: true,
        getFillColor: [...tokenRenk('--color-deprem'), 45],
        stroked: true,
        getLineColor: [...tokenRenk('--color-deprem'), 230],
        lineWidthUnits: 'pixels',
        getLineWidth: 1.5,
        pickable: true,
      }),
    )
  }

  // Toplanma alanları (J-56): AFAD listesi; afetzede ekranıyla aynı veri ve aynı
  // renk. Kayıt alanın şu an açık ya da kullanılabilir olduğunu söylemez (kural 1);
  // ipucu bunu yazar. Bölge ölçeğinde 3.682 nokta haritayı kapattığı için
  // yalnız şehir ölçeğinde çizilir.
  if (g.katmanlar.toplanma && g.toplanmaGorunur && g.toplanma?.length) {
    L.push(
      new IconLayer<ToplanmaAlani>({
        ...SIMGE_ORTAK,
        id: 'toplanma',
        data: g.toplanma,
        getPosition: (d) => [d.lon, d.lat],
        getIcon: () => ikon('toplanma'),
        getSize: 18,
      }),
    )
  }

  // Hastane ve sağlık merkezi (J-172): OSM kaydı; şehir ölçeğinde. Hastane
  // sağlık merkezinden büyük çizilir.
  if (g.katmanlar.saglik && (g.zoom ?? 0) >= SAGLIK_EN_AZ_ZOOM && g.saglik?.length) {
    L.push(
      new IconLayer<SaglikYeri>({
        ...SIMGE_ORTAK,
        id: 'saglik',
        data: g.saglik,
        getPosition: (d) => [d.lon, d.lat],
        getIcon: (d) => ikon(d.tur === 'hastane' ? 'hastane' : 'saglik'),
        getSize: (d) => (d.tur === 'hastane' ? 22 : 16),
      }),
    )
  }

  // Deprem riski (J-173): seçili ilin hesap alanı (uzun vadeli 200 km, kısa
  // vadeli 150 km) ve 81 il merkezi risk renginde. Kırmızı-turuncu-sarı burada
  // aciliyet/tehlike anlamında (ARAYUZ §6).
  if (g.risk) {
    const h = g.risk.halkalar
    if (h) {
      const soluk = tokenRenk('--color-ink-3')
      L.push(
        new ScatterplotLayer<{ p: [number, number]; r: number; uzun: boolean }>({
          id: 'risk-halkalari',
          data: [
            { p: [h.lon, h.lat], r: h.uzunKm * 1000, uzun: true },
            { p: [h.lon, h.lat], r: h.kisaKm * 1000, uzun: false },
          ],
          getPosition: (d) => d.p,
          getRadius: (d) => d.r,
          radiusUnits: 'meters',
          filled: true,
          getFillColor: (d) => [...soluk, d.uzun ? 14 : 0],
          stroked: true,
          lineWidthMinPixels: 1.5,
          getLineColor: (d) => [...soluk, d.uzun ? 200 : 140],
        }),
      )
    }
    const renk = (s: number) =>
      tokenRenk(s >= 75 ? '--color-crit' : s >= 50 ? '--color-high' : s >= 25 ? '--color-mid' : '--color-ok')
    L.push(
      new ScatterplotLayer<RiskIli>({
        id: 'risk-illeri',
        data: g.risk.iller,
        getPosition: (d) => [d.lon, d.lat],
        getRadius: (d) => (d.il === g.risk!.secili ? 9 : 6),
        radiusUnits: 'pixels',
        getFillColor: (d) => [...renk(d.skor), 235],
        stroked: true,
        lineWidthMinPixels: 1.5,
        getLineColor: (d) => (d.il === g.risk!.secili ? [232, 236, 244, 255] : [...tokenRenk('--color-ground'), 255]),
        updateTriggers: { getRadius: g.risk.secili, getLineColor: g.risk.secili },
        pickable: true,
      }),
      new TextLayer<RiskIli>({
        id: 'risk-il-adlari',
        // Uzakta yalnız seçili il ve en riskli 10 il yazılır; yakında hepsi.
        data: (g.zoom ?? 0) >= 7.5 ? g.risk.iller : g.risk.iller.filter((d, i) => i < 10 || d.il === g.risk!.secili),
        getPosition: (d) => [d.lon, d.lat],
        getText: (d) => `${d.il} ${Math.round(d.skor)}`,
        getSize: tokenPx('--text-small'),
        getColor: [...tokenRenk('--color-ink'), 255],
        getPixelOffset: [0, -12],
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

  // Hasar noktaları birleşik ısının kaynağıdır; ısıyla birlikte açılır.
  // ("Yapılar" bayrağı artık altlıktaki yapıları çizer.)
  // Tek tek noktalar şehir ölçeğinde; uzakta yoğunluğu ısı zaten gösterir.
  if (g.katmanlar.isi && (g.zoom ?? 0) >= HASAR_NOKTASI_EN_AZ_ZOOM) {
    L.push(
      new ScatterplotLayer<HasarNoktasi>({
        id: 'hasar-noktalari',
        data: g.hasar,
        getPosition: (d) => [d.lon, d.lat],
        getRadius: (d) => 18 + d.skor * 22,
        radiusUnits: 'meters',
        radiusMinPixels: 2.5,
        radiusMaxPixels: 12,
        getFillColor: (d) => KAYNAK_RENK[d.kaynak],
        pickable: true,
      }),
    )
  }

  // Ekipler (J-54): müsait ekip vurgu renginde, görevdeki beyaz ve vurgu
  // kenarlı, hizmet dışı gri. Görevdeki ekipten olaya rotası çizilir (J-55:
  // araç ağında, tek yönlere uyarak); yol ağı dışındaki ekip için kesik düz
  // çizgi, çünkü o bir yol değil yöndür. Adı noktanın üstünde yazar.
  if (g.katmanlar.ekipler) {
    const ekipler = g.ekipler.filter(konumlu)
    const giden = ekipler.filter((e) => e.gorev?.hedef)
    const vurgu = tokenRenk('--color-accent')
    L.push(
      new PathLayer<KonumluEkip>({
        id: 'gorev-rotalari',
        data: giden.filter((e) => e.gorev!.rota?.length),
        getPath: (d) => d.gorev!.rota!,
        getColor: [...vurgu, 220],
        getWidth: 3,
        widthUnits: 'pixels',
        capRounded: true,
        jointRounded: true,
      }),
      new PathLayer<KonumluEkip, { getDashArray: [number, number] }>({
        id: 'gorev-cizgileri',
        data: giden.filter((e) => !e.gorev!.rota?.length),
        getPath: (d) => [
          [d.lon, d.lat],
          [d.gorev!.hedef!.lon, d.gorev!.hedef!.lat],
        ],
        getColor: [...vurgu, 180],
        getWidth: 2,
        widthUnits: 'pixels',
        getDashArray: [4, 3],
        extensions: [KESIK],
      }),
      new IconLayer<KonumluEkip>({
        ...SIMGE_ORTAK,
        id: 'ekipler',
        data: ekipler,
        getPosition: (d) => [d.lon, d.lat],
        getIcon: (d) => ikon(ekipSimgesi(d)),
        getSize: 24,
      }),
    )
  }
  if (g.katmanlar.ekipler && (g.zoom ?? 0) >= EKIP_ADI_EN_AZ_ZOOM) {
    L.push(
      new TextLayer<KonumluEkip>({
        id: 'ekip-adlari',
        data: g.ekipler.filter(konumlu),
        getPosition: (d) => [d.lon, d.lat],
        getText: (d) => d.ad,
        getSize: tokenPx('--text-small'),
        getColor: [...tokenRenk('--color-ink'), 255],
        getPixelOffset: [0, -15],
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

  // Konum belirsizliği (J-170): noktanın kesin yer olmadığını gösterir. İçi çok
  // soluk, kenarı vurgu renginde; ihbar noktalarının ALTINDA kalır.
  const b = g.belirsizlik
  if (b) {
    const vurgu = tokenRenk('--color-accent')
    L.push(
      new ScatterplotLayer<KonumBelirsizligi>({
        id: 'konum-belirsizligi',
        data: [b],
        getPosition: (d) => [d.lon, d.lat],
        getRadius: (d) => d.yaricapM,
        radiusUnits: 'meters',
        radiusMinPixels: 10,
        getFillColor: [...vurgu, 22],
        stroked: true,
        lineWidthMinPixels: 1.5,
        getLineColor: [...vurgu, 200],
        // Seçilmez: altındaki hasar noktalarının tıklamasını yutmasın.
        pickable: false,
      }),
    )
    if (b.nokta) {
      L.push(
        new ScatterplotLayer<KonumBelirsizligi>({
          id: 'konum-belirsizligi-merkez',
          data: [b],
          getPosition: (d) => [d.lon, d.lat],
          getRadius: 30,
          radiusUnits: 'meters',
          radiusMinPixels: 4,
          radiusMaxPixels: 9,
          getFillColor: [...tokenRenk('--color-ihbar-metin'), 235],
          stroked: true,
          lineWidthMinPixels: 1.5,
          getLineColor: [232, 236, 244, 255],
          pickable: true,
        }),
      )
    }
  }

  // Afetzede ihbarları: türün rengiyle (afetzede ekranındaki düğmeyle aynı).
  // Kapanan ihbar sönük kalır; SOS'un altında çizilir.
  if (g.katmanlar.ihbarlar && g.ihbarlar?.length) {
    const turler = g.ihbarTurleri
    const veri = turler ? g.ihbarlar.filter((i) => turler.includes(i.tur)) : g.ihbarlar
    L.push(
      new IconLayer<Ihbar>({
        ...SIMGE_ORTAK,
        id: 'ihbarlar',
        data: veri,
        getPosition: (d) => [d.lon, d.lat],
        getIcon: (d) => ikon(`ihbar-${d.tur}` as SimgeTuru, g.seciliIhbar === d.id),
        getSize: (d) => (g.seciliIhbar === d.id ? 30 : 22),
        // Kapanan ihbar sönük.
        getColor: (d) => [255, 255, 255, d.durum === 'kapandi' ? 110 : 255],
        updateTriggers: { getIcon: g.seciliIhbar, getSize: g.seciliIhbar },
      }),
    )
  }

  L.push(
    new IconLayer<SosCagrisi>({
      ...SIMGE_ORTAK,
      id: 'sos',
      data: g.sos,
      getPosition: (d) => [d.lon, d.lat],
      getIcon: (d) => ikon(`sos-${d.oncelik}` as SimgeTuru, g.seciliSos === d.id),
      getSize: (d) => (g.seciliSos === d.id ? 34 : 26),
      // Kapanan çağrı sönük; bekleyen tam renk.
      getColor: (d) => [255, 255, 255, d.durum === 'kapandi' ? 110 : 255],
      updateTriggers: { getIcon: g.seciliSos, getSize: g.seciliSos },
    }),
  )

  // Rota (J-171): kaçınmasız kıyas kesik ve sönük, öteki adaylar sönük, seçilen
  // rota koyu kenarlı vurgu çizgisi; uçlar en üstte.
  const gz = g.guzergah
  if (gz) {
    const vurgu = tokenRenk('--color-accent')
    const soluk = tokenRenk('--color-ink-3')
    const zemin = tokenRenk('--color-ground')
    if (gz.kiyas?.length) {
      L.push(
        new PathLayer<{ p: [number, number][] }, { getDashArray: [number, number] }>({
          id: 'guzergah-kiyas',
          data: [{ p: gz.kiyas }],
          getPath: (d) => d.p,
          getColor: [...soluk, 200],
          getWidth: 3,
          widthUnits: 'pixels',
          getDashArray: [5, 4],
          extensions: [KESIK],
        }),
      )
    }
    if (gz.adaylar.length) {
      L.push(
        new PathLayer<{ p: [number, number][] }>({
          id: 'guzergah-adaylar',
          data: gz.adaylar.map((p) => ({ p })),
          getPath: (d) => d.p,
          getColor: [...soluk, 150],
          getWidth: 3,
          widthUnits: 'pixels',
          capRounded: true,
          jointRounded: true,
        }),
      )
    }
    if (gz.ana?.length) {
      L.push(
        new PathLayer<{ p: [number, number][] }>({
          id: 'guzergah-kenar',
          data: [{ p: gz.ana }],
          getPath: (d) => d.p,
          getColor: [...zemin, 230],
          getWidth: 8,
          widthUnits: 'pixels',
          capRounded: true,
          jointRounded: true,
        }),
        new PathLayer<{ p: [number, number][] }>({
          id: 'guzergah',
          data: [{ p: gz.ana }],
          getPath: (d) => d.p,
          getColor: [...vurgu, 255],
          getWidth: 4.5,
          widthUnits: 'pixels',
          capRounded: true,
          jointRounded: true,
        }),
      )
    }
    const uclar = [
      ...(gz.bas ? [{ p: gz.bas, bas: true }] : []),
      ...(gz.hedef ? [{ p: gz.hedef, bas: false }] : []),
    ]
    if (uclar.length) {
      L.push(
        new ScatterplotLayer<{ p: [number, number]; bas: boolean }>({
          id: 'guzergah-uclari',
          data: uclar,
          getPosition: (d) => d.p,
          getRadius: 8,
          radiusUnits: 'pixels',
          getFillColor: (d) => (d.bas ? [...vurgu, 255] : [232, 236, 244, 255]),
          stroked: true,
          lineWidthMinPixels: 2,
          getLineColor: [...zemin, 255],
        }),
      )
    }
  }

  // Seçim şekilleri en üstte: veri katmanlarını gizlemesin diye içi çok soluk,
  // kenarı vurgu renginde.
  const secim = g.secim
  if (secim) {
    const taslakHalka = secim.taslak?.kutu
      ? kutuHalkasi(secim.taslak.kutu)
      : (secim.taslak?.nokta ?? null)
    const kesinHalka = secim.cokgen ?? (secim.kutu ? kutuHalkasi(secim.kutu) : null)
    const halka = taslakHalka ?? kesinHalka

    if (halka && halka.length >= 2) {
      L.push(
        new PolygonLayer<{ halka: Nokta[] }>({
          id: 'secim-alani',
          data: [{ halka }],
          getPolygon: (d) => d.halka,
          filled: true,
          stroked: true,
          getFillColor: [69, 200, 224, 26],
          getLineColor: [69, 200, 224, 235],
          getLineWidth: 2,
          lineWidthUnits: 'pixels',
          lineWidthMinPixels: 2,
        }),
      )
      L.push(
        new ScatterplotLayer<Nokta>({
          id: 'secim-koseleri',
          data: halka,
          getPosition: (d) => d,
          getRadius: 4,
          radiusUnits: 'pixels',
          getFillColor: [232, 236, 244, 255],
          stroked: true,
          lineWidthMinPixels: 1.5,
          getLineColor: [27, 108, 126, 255],
        }),
      )
    }
  }

  return L
}

/* ---- Üstüne gelince bilgi (J-41) -----------------------------------------
   Prototipteki gibi: nokta ne, ne zaman, ne kadar acil. Metin kullanıcıdan
   geldiği için HTML'e kaçırılarak yazılır. */

const KESIK = new PathStyleExtension({ dash: true })

type KonumluEkip = Ekip & { lon: number; lat: number }
const konumlu = (e: Ekip): e is KonumluEkip => e.lon != null && e.lat != null

/** Olayın ekip durumu: kim gidiyor, yoksa bekliyor mu kapandı mı. */
function sevkSatiri(durum: 'bekliyor' | 'atandi' | 'kapandi' | 'yeni' | 'goruldu', gorevler: Parameters<typeof gorevOzeti>[0]) {
  return gorevOzeti(gorevler) ?? (durum === 'kapandi' ? 'Kapandı' : 'Ekip gönderilmedi')
}

/** Ekibin durumu: görevdeyse nereye ve hangi aşamada. */
function ekipSatiri(e: Ekip): string {
  if (e.gorev) {
    const h = e.gorev.hedef
    const nereye = h ? `${h.tur === 'sos' ? 'SOS' : IHBAR_TURU[h.tur].ad}${h.mahalle ? ` · ${h.mahalle}` : ''}` : e.gorev.hedefId
    const uzaklik = e.gorev.durum !== 'olay-yerinde' ? uzaklikMetni(e.gorev.yol, e.gorev.kalanM) : null
    const kalan = uzaklik ? `, olaya ${uzaklik}` : ''
    return `Görevde: ${nereye} — ${GOREV_DURUMU[e.gorev.durum].kisa.toLocaleLowerCase('tr')}${kalan}`
  }
  return e.durum === 'hizmet-disi' ? 'Hizmet dışı' : 'Müsait'
}

const kacis = (m: string) =>
  m.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!)

export function ekipSimgesi(e: Ekip): SimgeTuru {
  return e.gorev ? 'ekip-gorevde' : e.durum === 'hizmet-disi' ? 'ekip-disi' : 'ekip-musait'
}

type KartSatiri = string | null | undefined | false | [string, string | null | undefined]

/** Üstüne gelince bilgi kartı (J-172): ne olduğu (tür ve simge), başlık,
    ad-değer satırları, kaynağı ve tıklayınca ne olacağı. Her nokta türü aynı
    düzende: koordinatör türü simgeden, ayrıntıyı karttan okur. */
export function ipucuKarti(k: {
  tur: string
  simge?: SimgeTuru
  baslik: string
  satirlar?: KartSatiri[]
  kaynak?: string | null
  eylem?: string | null
}) {
  const satirlar = (k.satirlar ?? [])
    .filter((x): x is string | [string, string] => !!x && (typeof x === 'string' || !!x[1]))
    .map((x) =>
      typeof x === 'string'
        ? `<div class="qm-ipucu-metin">${kacis(x)}</div>`
        : `<div class="qm-ipucu-satir"><span>${kacis(x[0])}</span><span>${kacis(x[1])}</span></div>`,
    )
    .join('')
  const simge = k.simge ? `<img alt="" src="${simgeAdresi(k.simge)}" width="18" height="18"/>` : ''
  return {
    html:
      `<div class="qm-ipucu"><div class="qm-ipucu-tur">${simge}<span>${kacis(k.tur)}</span></div>` +
      `<div class="qm-ipucu-baslik">${kacis(k.baslik)}</div>${satirlar}` +
      (k.kaynak ? `<div class="qm-ipucu-kaynak">${kacis(k.kaynak)}</div>` : '') +
      (k.eylem ? `<div class="qm-ipucu-eylem">${kacis(k.eylem)}</div>` : '') +
      `</div>`,
    style: { background: 'transparent', boxShadow: 'none', padding: '0', margin: '0' },
  }
}

export function ipucuKutusu(baslik: string, satirlar: Array<string | null | undefined | false>) {
  return ipucuKarti({ tur: 'Bilgi', baslik, satirlar })
}

const kisalt = (m: string | null | undefined, n = 140) => (m && m.length > n ? `${m.slice(0, n)}…` : m)

export function haritaIpucu({ object, layer }: PickingInfo) {
  if (!object || !layer) return null
  switch (layer.id) {
    case 'sos': {
      const c = object as SosCagrisi
      const ek = sosEkBilgi(c)
      return ipucuKarti({
        tur: 'SOS çağrısı',
        simge: `sos-${c.oncelik}` as SimgeTuru,
        baslik: `${ONCELIK_ADI[c.oncelik]} aciliyet${c.mahalle ? ` · ${c.mahalle}` : ''}`,
        satirlar: [
          ['Durum', sevkSatiri(c.durum, c.gorevler)],
          ['Kişi / ihtiyaç', ek.kisiIhtiyac],
          ['Geldi', tarihSaat(c.zaman)],
          kisalt(c.metin),
          ek.yaklasik && ek.konum,
        ],
        kaynak: 'Afetzede ekranından gelen acil çağrı',
        eylem: 'Tıkla: seç, ayrıntı ve ekip gönder',
      })
    }
    case 'ihbarlar': {
      const i = object as Ihbar
      return ipucuKarti({
        tur: IHBAR_TURU[i.tur].ad,
        simge: `ihbar-${i.tur}` as SimgeTuru,
        baslik: i.etiket ?? IHBAR_TURU[i.tur].ad,
        satirlar: [
          ['Durum', IHBAR_DURUMU[i.durum].ad],
          ['Ekip', gorevOzeti(i.gorevler)],
          ['Kişi', i.kisiSayisi ? `${i.kisiSayisi} kişi${i.tur === 'metin' ? ' (metinden)' : ''}` : null],
          ['Geldi', tarihSaat(i.zaman)],
          kisalt(i.metin),
          ihbarKonumu(i),
        ],
        kaynak: i.tur === 'fotograf' ? 'Fotoğraf: YOLO modelinin tahmini' : i.tur === 'metin' ? 'Yazı: BERTurk modelinin tahmini' : 'Afetzedenin ihtiyaç talebi',
        eylem: 'Tıkla: seç ve ayrıntıyı aç',
      })
    }
    case 'konum-belirsizligi':
    case 'konum-belirsizligi-merkez': {
      const b = object as KonumBelirsizligi
      return ipucuKarti({ tur: 'Konum payı', baslik: b.baslik, satirlar: [b.aciklama] })
    }
    case 'hasar-noktalari': {
      const h = object as HasarNoktasi
      return ipucuKarti({
        tur: 'Hasar noktası',
        baslik: KAYNAK_ADI[h.kaynak],
        satirlar: [
          ['Hasar skoru', `%${Math.round(h.skor * 100)}`],
          ['Model güveni', `%${Math.round(h.guven * 100)}`],
          ['Zaman', tarihSaat(h.zaman)],
        ],
        kaynak: 'Modelin tahmini; sahada doğrulanmadı. Isı haritası bu noktalardan çıkar.',
      })
    }
    case 'ekipler': {
      const e = object as Ekip
      return ipucuKarti({
        tur: 'Saha ekibi',
        simge: ekipSimgesi(e),
        baslik: e.ad,
        satirlar: [
          ['Tür', [kurumTur(e), e.kisiSayisi ? `${e.kisiSayisi} kişi` : null].filter(Boolean).join(' · ')],
          ['Durum', ekipSatiri(e)],
          ['Konum', e.konumZamani ? `${e.yerAdi ? `${e.yerAdi} yakını, ` : ''}${tarihSaat(e.konumZamani)}` : null],
        ],
        kaynak: 'Konum ekibin telefonundan',
        eylem: 'Tıkla: yakınlaş',
      })
    }
    case 'analiz-kapali':
      return ipucuKarti({
        tur: 'Kapalı yol',
        simge: 'kapanma',
        baslik: 'Bu analizde kapalı bulundu',
        kaynak: 'Uydu analizi: modelin tahmini, sahada doğrulanmadı',
      })
    case 'yol-kapanmalari':
    case 'yol-kapanmalari-cizgi': {
      const k = object as Kapanma
      return ipucuKarti({
        tur: 'Yol kapanması',
        simge: 'kapanma',
        baslik: k.kaynak === 'uydu' ? 'Uydu analizinde kapalı' : `Kapalı (${k.kaynak})`,
        satirlar: [
          ['Bulundu', tarihSaatYilli(k.zaman)],
          'Rotalar bu yoldan kaçınır; başka yol yoksa geçer ve uyarır.',
        ],
        kaynak: k.kaynak === 'uydu' ? 'Modelin tahmini; sahada doğrulanmadı' : null,
      })
    }
    case 'depremler': {
      const d = object as Deprem
      return ipucuKarti({
        tur: 'Geçmiş deprem',
        baslik: `M ${d.buyukluk.toFixed(1).replace('.', ',')} · ${d.yer ?? 'yer yok'}`,
        satirlar: [
          ['Derinlik', d.derinlikKm != null ? `${d.derinlikKm.toFixed(0)} km` : null],
          ['Zaman', tarihSaatYilli(d.zaman)],
        ],
        kaynak: 'Katalog kaydı (Kandilli, USGS); bugünün hasarı değil',
      })
    }
    case 'faylar':
      return ipucuKarti({
        tur: 'Fay hattı',
        baslik: 'Etkin fay',
        kaynak: 'GEM Global Active Faults; jeolojik başvuru, bugünkü hasar değil',
      })
    case 'toplanma': {
      const t = object as ToplanmaAlani
      return ipucuKarti({
        tur: 'Toplanma alanı',
        simge: 'toplanma',
        baslik: t.ad ?? 'Toplanma alanı',
        satirlar: [t.adres],
        kaynak: 'AFAD listesi; alanın şu an açık ya da güvenli olduğunu göstermez',
      })
    }
    case 'risk-illeri': {
      const r = object as RiskIli
      return ipucuKarti({
        tur: 'Deprem riski',
        baslik: `${r.il} · ${Math.round(r.skor)} / 100`,
        satirlar: [['Düzey', r.seviye], ['En yakın fay', `${r.fayKm.toFixed(1).replace('.', ',')} km`]],
        kaynak: 'İl merkezinde hesaplanır; tehlike göstergesidir, deprem tahmini değildir',
        eylem: 'Tıkla: seç ve bileşenleri gör',
      })
    }
    case 'saglik': {
      const y = object as SaglikYeri
      return ipucuKarti({
        tur: y.tur === 'hastane' ? 'Hastane' : 'Sağlık merkezi',
        simge: y.tur === 'hastane' ? 'hastane' : 'saglik',
        baslik: y.ad ?? (y.tur === 'hastane' ? 'Adsız hastane' : 'Adsız sağlık tesisi'),
        kaynak: 'OpenStreetMap kaydı; şu an açık olduğunu ya da hasta kabul ettiğini göstermez',
        eylem: 'Yol ve rota: en yakın hastaneye rota',
      })
    }
    case 'guzergah':
    case 'guzergah-kenar':
      return ipucuKarti({ tur: 'Rota', baslik: 'Seçilen rota', satirlar: ['Ayrıntı sağ panelde'] })
    // --- tatbikat (SIMULASYON_SOZLESMESI.md §5) ---
    case 'sim-kapanma-kapali':
      return ipucuKutusu('Tatbikat: kapalı yol', [
        'Modelin hasar maskesinden türetildi; sahada doğrulanmadı.',
        `Kenar: ${(object as SimKenar).id}`,
      ])
    case 'sim-kapanma-cezali': {
      const k = object as SimKenar
      return ipucuKutusu('Tatbikat: riskli yol', [
        k.carpan ? `Maliyet çarpanı ${k.carpan.toString().replace('.', ',')}` : null,
        'Kapalı değil; hasara yakın olduğu için cezalı.',
        `Kenar: ${k.id}`,
      ])
    }
    case 'sim-rota-depremOncesi':
    case 'sim-rota-kapanmali':
    case 'sim-rota-riskli': {
      const r = object as RotaCizgisi
      const v = r.rota.varyantlar[r.varyant]
      return ipucuKutusu(`Tatbikat rotası · ${VARYANT_ADI[r.varyant]}`, [
        `${r.rota.baslangic.ad} → ${r.rota.hedef.ad}`,
        v ? `${mesafe(v.uzunlukM)} · ${sureMetni(v.sureDk)}` : null,
        'Tatbikat: gerçek bir sevk değil.',
      ])
    }
    case 'sim-gorev-ekip':
    case 'sim-gorev-afetzede': {
      const u = object as GorevUcu
      const g2: SimGorev = u.gorev
      return ipucuKutusu(u.ad, [
        u.tur === 'ekip'
          ? g2.gercekTesis
            ? 'Ekip üssü · gerçek tesis (OpenStreetMap)'
            : 'Ekip üssü'
          : 'Afetzede konumu ÜRETİLDİ (senaryo), gerçek çağrı değil.',
        `Varış tahmini ${sureMetni(u.etaDk)}`,
      ])
    }
    default:
      return null
  }
}
