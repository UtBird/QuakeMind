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
import {
  DEPREM_EN_AZ,
  KAPANMA_DURUM_ADI,
  type Deprem,
  type Fay,
  type Kapanma,
  type SaglikYeri,
  type ToplanmaAlani,
} from '@/veri/katman'
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
import { ikon, kumeIkonu, simgeAdresi, type SimgeTuru } from './simgeler'
import { kumele, kumeSayisi, type Kume } from './kumeleme'
import { paylarMetni, type IsiDokusu } from './isiDokusu'

/* Yakınlaştırma eşikleri (J-172): harita her ölçekte yalnız o ölçekte işe
   yarayanı çizer. Olaylar (SOS, ihbar) ve ekipler her ölçekte; tek tek uydu
   noktaları, ekip adları ve sağlık tesisleri şehir ölçeğinde. */
export const HASAR_NOKTASI_EN_AZ_ZOOM = 13
export const EKIP_ADI_EN_AZ_ZOOM = 12
/* Kümeleme (J-191): bu yakınlığın üstünde her tür tek tek çizilir. Ekip adları
   EKIP_ADI_EN_AZ_ZOOM'da yazıldığı için ekipler ondan önce açılır. */
const KUME_EN_COK_ZOOM = { toplanma: 14, saglik: 13, ekipler: 11, ihbarlar: 13, sos: 13 } as const
const SOS_ONCELIK = { kritik: 3, yuksek: 2, orta: 1 } as const

/** Küme simgesi + sayısı. Simge tıklanır (KonsolKabugu: genişleme yakınlığına uçar). */
function kumeKatmanlari(id: string, kumeler: Kume[], simge: (k: Kume) => SimgeTuru, yazi: (k: Kume) => [number, number, number]): Layer[] {
  if (!kumeler.length) return []
  const boy = (k: Kume) => 30 + Math.min(18, Math.log2(k.sayi) * 3.4)
  return [
    new IconLayer<Kume>({
      ...SIMGE_ORTAK,
      id: `kume-${id}`,
      data: kumeler,
      getPosition: (k) => [k.lon, k.lat],
      getIcon: (k) => kumeIkonu(simge(k)),
      getSize: boy,
    }),
    new TextLayer<Kume>({
      id: `kume-${id}-sayi`,
      data: kumeler,
      getPosition: (k) => [k.lon, k.lat],
      getText: (k) => kumeSayisi(k.sayi),
      getSize: tokenPx('--text-small'),
      getColor: (k) => [...yazi(k), 255],
      fontFamily: 'IBM Plex Sans, sans-serif',
      fontWeight: 700,
      characterSet: '0123456789, B',
      getTextAnchor: 'middle',
      getAlignmentBaseline: 'center',
    }),
  ]
}

function baskinTur(k: Kume): string {
  let en = ''
  let n = -1
  for (const [t, v] of Object.entries(k.ozet.turler)) if (v > n) [en, n] = [t, v]
  return en
}

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
   zemin renginde kalın bir haleyle yazılır.

   Okunurluk (J-178, kullanıcı: "mahalle, sokak, cadde adları hiç okunmuyor"):
   sokak adları en küçük boy ve en sönük griyle (micro, ink-3), mahalleler
   small ve ink-2 ile yazılıyordu; hale de yazı atlasının dar boşluğu yüzünden
   inceydi (outlineWidth 3 / radius 12). Şimdi sokak body + ink-2, mahalle ve
   köy body + ink + kalın, şehir ve ilçe subtitle + kalın; atlas boşluğu ve
   hale kalın. Büyüyen ad daha çok yer kapladığı için çakışma süzgeci biraz daha az
   sokak adı yazar: okunur az ad, okunmayan çok addan iyidir. */
const CAKISMA = new CollisionFilterExtension()

/** Yakınlaştırmaya göre yazılan adlar: -1 yalnız bölge adları, 0 şehir/ilçe,
    1 +köy, 2 +mahalle, 3 +sokak. */
export type EtiketSeviyesi = -1 | 0 | 1 | 2 | 3

/** Yazı atlası: hale kalınlığı atlastaki boşlukla sınırlı (deck.gl: outlineWidth / radius). */
const AD_YAZISI = { sdf: true, fontSize: 64, buffer: 8, radius: 16 } as const
const AD_HALESI = 6

export function etiketKatmani(
  id: string,
  data: Etiket[],
  boy: number,
  renk: [number, number, number],
  kalinlik: 500 | 600 = 500,
) {
  return new TextLayer<Etiket, CollisionFilterExtensionProps<Etiket>>({
    id,
    data,
    getPosition: (d) => [d.lon, d.lat],
    getText: (d) => d.ad,
    getAngle: (d) => d.aci,
    getSize: boy,
    getColor: renk,
    fontFamily: 'IBM Plex Sans, sans-serif',
    fontWeight: kalinlik,
    characterSet: 'auto',
    fontSettings: AD_YAZISI,
    outlineWidth: AD_HALESI,
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
    return [etiketKatmani('ad-bolgeler', bolgeAdlari, tokenPx('--text-title'), tokenRenk('--color-ink'), 600)]
  }
  const L: Layer[] = []
  for (const b of bolgeler) {
    const yerSeviyesi = Math.min(seviye, 2) as 0 | 1 | 2
    L.push(
      etiketKatmani(
        `ad-${b.id}-yer-${yerSeviyesi}`,
        b.yerAdlari[yerSeviyesi],
        tokenPx(yerSeviyesi === 0 ? '--text-subtitle' : '--text-body'),
        tokenRenk('--color-ink'),
        600,
      ),
    )
    if (seviye >= 3) {
      L.push(
        etiketKatmani(
          `ad-${b.id}-sokak`,
          b.sokakAdlari,
          tokenPx('--text-body'),
          tokenRenk('--color-ink-2'),
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
    /** Seçili ilin merkezi ve hesap alanı (uzun vadeli, km). */
    alan: { lon: number; lat: number; km: number } | null
    /** İl seçiliyse o ilin 200 km'sindeki, değilse ülkenin M≥6 ana şokları. */
    anaSoklar: RiskDepremi[]
    /** Seçili ilin son bir yılı (150 km). */
    sonYil: RiskDepremi[]
    seciliDeprem: string | null
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
    /** Çok duraklı rota: sırayla numaralanır. */
    duraklar?: [number, number][]
  } | null
  /** Soldan seçilen görüntü kaynağının karosu (Hasar analizi modu). */
  goruntu?: { url: string; kunye: string; ortuculuk?: number } | null
  /** Bitmiş hasar analizinin yol geometrisi. */
  analiz?: { kapali: Yol[]; acik: Yol[] } | null
  /** Tatbikat koşusunun katmanları (SIMULASYON_SOZLESMESI.md §5). */
  simulasyon?: SimHaritaGirdisi
  /** Başvuru katmanları (J-56); her biri kendi ucundan gelir. */
  kapanmalar?: Kapanma[]
  /** Kapanma yönetiminde seçili kapanma (vurgulanır). */
  seciliKapanma?: string | null
  depremler?: Deprem[]
  faylar?: Fay[]
  toplanma?: ToplanmaAlani[]
  /** Kanalların ağırlıklı karışımından çıkan ısı dokusu. */
  isi?: IsiDokusu | null
  /** Analiz alanı seçimi: kesinleşmiş şekil ve çizim sürerken taslak. */
  secim?: {
    kutu: Kutu | null
    cokgen: Nokta[] | null
    taslak: { kutu?: Kutu; nokta?: Nokta[] } | null
  }
}

type KonumBelirsizligi = BelirsizlikCemberi
type RiskIli = NonNullable<KatmanGirdisi['risk']>['iller'][number]
/** Risk ekranının depremi (J-191); `id` panel listesiyle aynı. */
export type RiskDepremi = { id: string; lon: number; lat: number; m: number; yil: string; zaman: string; yer: string; km?: number }

/** Merkezden km yarıçaplı çember (büyük daire; harita izdüşümünde doğru çizilir). */
function cember(lon: number, lat: number, km: number, n = 128): [number, number][] {
  const r = km / 6371
  const f1 = (lat * Math.PI) / 180
  const l1 = (lon * Math.PI) / 180
  const sonuc: [number, number][] = []
  for (let i = 0; i <= n; i++) {
    const a = (2 * Math.PI * i) / n
    const f2 = Math.asin(Math.sin(f1) * Math.cos(r) + Math.cos(f1) * Math.sin(r) * Math.cos(a))
    const l2 = l1 + Math.atan2(Math.sin(a) * Math.sin(r) * Math.cos(f1), Math.cos(r) - Math.sin(f1) * Math.sin(f2))
    sonuc.push([(l2 * 180) / Math.PI, (f2 * 180) / Math.PI])
  }
  return sonuc
}

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
  sonIsi = g.katmanlar.isi ? (g.isi ?? null) : null
  if (g.katmanlar.isi && g.isi) {
    L.push(
      new BitmapLayer({
        id: 'isi',
        image: g.isi.goruntu,
        bounds: g.isi.sinirlar,
        opacity: g.isiOrtuculugu ?? 0.72,
        textureParameters: { minFilter: 'linear', magFilter: 'linear' },
        // Üzerine gelince hücrenin dökümü (J-175): hangi kaynak, ne kadar.
        pickable: true,
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
      // Durum (J-190): kapalı kırmızı ve düz; açıldı yeşil,
      // yanlış alarm gri, ikisi de kesik. Kırmızı yalnız hasar anlamında kalır
      // (ARAYUZ §6). Açıldı ve yanlış alarm yalnız kapanma yönetiminde gelir.
      const renk = {
        kapali: tokenRenk('--color-crit'),
        acildi: tokenRenk('--color-ok'),
        yanlis: tokenRenk('--color-ink-3'),
      }
      const yol = (d: Kapanma) => (d.cizgi ?? []).map(([enlem, boylam]) => [boylam, enlem] as [number, number])
      const secili = g.seciliKapanma ? cizgili.find((d) => d.id === g.seciliKapanma) : undefined
      if (secili) {
        L.push(
          new PathLayer<Kapanma>({
            id: 'yol-kapanmalari-secili',
            data: [secili],
            getPath: yol,
            getColor: [...tokenRenk('--color-accent'), 120],
            getWidth: 12,
            widthUnits: 'pixels',
            capRounded: true,
            jointRounded: true,
          }),
        )
      }
      L.push(
        new PathLayer<Kapanma, { getDashArray?: (d: Kapanma) => [number, number] }>({
          id: 'yol-kapanmalari-cizgi',
          data: cizgili,
          getPath: yol,
          getColor: (d) => [...renk[d.durum ?? 'kapali'], 235],
          getWidth: 4,
          widthUnits: 'pixels',
          widthMinPixels: 2.5,
          capRounded: true,
          jointRounded: true,
          pickable: true,
          getDashArray: (d) => ((d.durum ?? 'kapali') === 'kapali' ? [0, 0] : [3, 2]),
          extensions: [KESIK],
          updateTriggers: { getColor: [g.seciliKapanma], getDashArray: [g.seciliKapanma] },
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
  if (g.katmanlar.toplanma && g.toplanma?.length) {
    const k = kumele('toplanma', g.toplanma, g.zoom ?? 0, {
      konum: (d) => [d.lon, d.lat],
      enCokZoom: KUME_EN_COK_ZOOM.toplanma,
    })
    L.push(
      ...kumeKatmanlari('toplanma', k.kumeler, () => 'toplanma', () => tokenRenk('--color-ground')),
      new IconLayer<ToplanmaAlani>({
        ...SIMGE_ORTAK,
        id: 'toplanma',
        data: k.tekler,
        getPosition: (d) => [d.lon, d.lat],
        getIcon: () => ikon('toplanma'),
        getSize: 18,
      }),
    )
  }

  // Hastane ve sağlık merkezi (J-172): OSM kaydı; şehir ölçeğinde. Hastane
  // sağlık merkezinden büyük çizilir.
  if (g.katmanlar.saglik && g.saglik?.length) {
    const k = kumele('saglik', g.saglik, g.zoom ?? 0, {
      konum: (d) => [d.lon, d.lat],
      enCokZoom: KUME_EN_COK_ZOOM.saglik,
    })
    L.push(
      ...kumeKatmanlari('saglik', k.kumeler, () => 'hastane', () => tokenRenk('--color-ground')),
      new IconLayer<SaglikYeri>({
        ...SIMGE_ORTAK,
        id: 'saglik',
        data: k.tekler,
        getPosition: (d) => [d.lon, d.lat],
        getIcon: (d) => ikon(d.tur === 'hastane' ? 'hastane' : 'saglik'),
        getSize: (d) => (d.tur === 'hastane' ? 22 : 16),
      }),
    )
  }

  // Deprem riski (J-173; J-191). İl seçilmemişken: il merkezleri (skor içinde)
  // ve ülkenin M≥6 ana şokları. İl seçilince: o ilin hesabına giren depremler
  // ve hesap alanı ince kesik çizgi; öteki iller sönük. Eskiden ülke kataloğunun
  // binlerce dairesi ve iki dev dolu daire birlikte çiziliyordu.
  // Kırmızı-turuncu-sarı burada tehlike düzeyi anlamında (ARAYUZ §6).
  if (g.risk) {
    const r = g.risk
    const deprem = tokenRenk('--color-deprem')
    const zemin = tokenRenk('--color-ground')
    const vurgu = tokenRenk('--color-accent')
    const yazi = tokenRenk('--color-ink')
    const etiketOrtak = {
      fontFamily: 'IBM Plex Sans, sans-serif',
      fontWeight: 600,
      characterSet: 'auto' as const,
      fontSettings: { sdf: true },
      outlineWidth: 3,
      outlineColor: [...zemin, 255] as [number, number, number, number],
    }
    const renk = (s: number) =>
      tokenRenk(s >= 75 ? '--color-crit' : s >= 50 ? '--color-high' : s >= 25 ? '--color-mid' : '--color-ok')
    // Ülke ölçeğinde 81 il üst üste binmesin: yuvarlak yakınlıkla büyür, skor
    // yazısı yalnız sığınca ve çakışmayınca yazılır (yüksek skor önce).
    const z = g.zoom ?? 6
    const ilR = Math.max(6, Math.min(11, 4 + (z - 4) * 3))
    const olcek = Math.max(0.7, Math.min(1, (z - 4) / 3))
    const iller = r.secili ? r.iller.filter((d) => d.il !== r.secili) : r.iller
    const seciliIl = r.secili ? r.iller.filter((d) => d.il === r.secili) : []
    const ilKatmanlari = (id: string, veri: RiskIli[], soluk: boolean, buyuk: boolean): Layer[] => [
      new ScatterplotLayer<RiskIli>({
        id,
        data: veri,
        getPosition: (d) => [d.lon, d.lat],
        getRadius: buyuk ? Math.max(13, ilR + 4) : ilR,
        radiusUnits: 'pixels',
        getFillColor: (d) => [...renk(d.skor), soluk ? 110 : 240],
        stroked: true,
        lineWidthMinPixels: buyuk ? 2.5 : 1.5,
        getLineColor: buyuk ? [...yazi, 255] : [...zemin, soluk ? 140 : 255],
        pickable: true,
        updateTriggers: { getFillColor: soluk, getLineColor: soluk, getRadius: ilR },
      }),
      new TextLayer<RiskIli, CollisionFilterExtensionProps<RiskIli>>({
        id: `${id}-skor`,
        data: buyuk || ilR >= 8 ? veri : [],
        extensions: [CAKISMA],
        collisionGroup: 'risk-il',
        getCollisionPriority: (d) => d.skor,
        getPosition: (d) => [d.lon, d.lat],
        getText: (d) => String(Math.round(d.skor)),
        getSize: tokenPx(buyuk ? '--text-body' : '--text-small'),
        getColor: (d) => (d.skor >= 75 ? [...yazi, soluk ? 140 : 255] : [...zemin, soluk ? 140 : 255]),
        fontFamily: 'IBM Plex Sans, sans-serif',
        fontWeight: 700,
        characterSet: '0123456789',
        getTextAnchor: 'middle',
        getAlignmentBaseline: 'center',
        updateTriggers: { getColor: soluk },
      }),
    ]

    // Hesap alanı: ince kesik çizgi ve kuzey ucunda adı.
    if (r.alan) {
      const c = cember(r.alan.lon, r.alan.lat, r.alan.km)
      L.push(
        new PathLayer<{ p: [number, number][] }, { getDashArray: [number, number] }>({
          id: 'risk-alani',
          data: [{ p: c }],
          getPath: (d) => d.p,
          getColor: [...tokenRenk('--color-ink-3'), 200],
          getWidth: 1.5,
          widthUnits: 'pixels',
          getDashArray: [6, 5],
          extensions: [KESIK],
        }),
        new TextLayer<{ p: [number, number] }>({
          id: 'risk-alani-adi',
          data: [{ p: c[0] }],
          getPosition: (d) => d.p,
          getText: () => `${r.alan!.km} km · ilin hesap alanı`,
          getSize: tokenPx('--text-small'),
          getColor: [...tokenRenk('--color-ink-2'), 255],
          getPixelOffset: [0, -8],
          getTextAnchor: 'middle',
          getAlignmentBaseline: 'bottom',
          ...etiketOrtak,
        }),
      )
    }

    L.push(...ilKatmanlari('risk-illeri', iller, !!r.secili, false))

    // Son bir yıl: küçük dolu noktalar (çap büyüklükle).
    if (r.sonYil.length) {
      L.push(
        new ScatterplotLayer<RiskDepremi>({
          id: 'risk-son-yil',
          data: r.sonYil,
          getPosition: (d) => [d.lon, d.lat],
          getRadius: (d) => 2.5 + Math.max(0, d.m - 3) * 1.8,
          radiusUnits: 'pixels',
          getFillColor: (d) => (d.id === r.seciliDeprem ? [...vurgu, 255] : [...deprem, 170]),
          stroked: true,
          lineWidthMinPixels: 1,
          getLineColor: [...zemin, 200],
          pickable: true,
          updateTriggers: { getFillColor: r.seciliDeprem },
        }),
      )
    }

    // M≥6 ana şoklar: halka, çap büyüklük (M6 ~6 px, M7,8 ~19 px).
    if (r.anaSoklar.length) {
      const yaricap = (d: RiskDepremi) => (6 + Math.max(0, d.m - 6) * 7.2) * olcek
      L.push(
        new ScatterplotLayer<RiskDepremi>({
          id: 'risk-ana-sok',
          data: r.anaSoklar,
          getPosition: (d) => [d.lon, d.lat],
          getRadius: yaricap,
          radiusUnits: 'pixels',
          filled: true,
          getFillColor: (d) => (d.id === r.seciliDeprem ? [...vurgu, 60] : [...deprem, 55]),
          stroked: true,
          lineWidthUnits: 'pixels',
          getLineWidth: (d) => (d.id === r.seciliDeprem ? 3 : 2),
          getLineColor: (d) => (d.id === r.seciliDeprem ? [...vurgu, 255] : [...deprem, 235]),
          pickable: true,
          updateTriggers: {
            getFillColor: r.seciliDeprem,
            getLineColor: r.seciliDeprem,
            getLineWidth: r.seciliDeprem,
            getRadius: olcek,
          },
        }),
      )
      // Yıl ve büyüklük: il seçiliyse hepsi (en çok ~20), değilse yakında ya da M≥7.
      const yazilan = r.secili
        ? r.anaSoklar
        : r.anaSoklar.filter((d) => d.m >= (z >= 7 ? 0 : z >= 6 ? 7 : 7.4) || d.id === r.seciliDeprem)
      L.push(
        new TextLayer<RiskDepremi>({
          id: 'risk-ana-sok-adi',
          data: yazilan,
          getPosition: (d) => [d.lon, d.lat],
          getText: (d) => `${d.yil} · M${d.m.toFixed(1).replace('.', ',')}`,
          getSize: tokenPx('--text-small'),
          getColor: (d) => (d.id === r.seciliDeprem ? [...vurgu, 255] : [...tokenRenk('--color-ink-2'), 255]),
          getPixelOffset: (d) => [0, yaricap(d) + 4],
          getTextAnchor: 'middle',
          getAlignmentBaseline: 'top',
          updateTriggers: { getColor: r.seciliDeprem, getPixelOffset: olcek },
          ...etiketOrtak,
        }),
      )
    }

    // Seçili il en üstte; adı üstünde (altlık adlarıyla çakışmasın diye yalnız o).
    if (seciliIl.length) {
      L.push(
        ...ilKatmanlari('risk-secili-il', seciliIl, false, true),
        new TextLayer<RiskIli>({
          id: 'risk-secili-il-adi',
          data: seciliIl,
          getPosition: (d) => [d.lon, d.lat],
          getText: (d) => d.il,
          getSize: tokenPx('--text-body'),
          getColor: [...yazi, 255],
          getPixelOffset: [0, -20],
          getTextAnchor: 'middle',
          getAlignmentBaseline: 'bottom',
          ...etiketOrtak,
        }),
      )
    }
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
    const ek = kumele('ekipler', ekipler, g.zoom ?? 0, {
      konum: (d) => [d.lon, d.lat],
      enCokZoom: KUME_EN_COK_ZOOM.ekipler,
    })
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
      ...kumeKatmanlari('ekipler', ek.kumeler, () => 'ekip-musait', () => tokenRenk('--color-accent-ink')),
      new IconLayer<KonumluEkip>({
        ...SIMGE_ORTAK,
        id: 'ekipler',
        data: ek.tekler,
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
    // Seçili ihbar kümeye girmez: panelde seçilen nokta haritada hep görünür.
    const secili = veri.filter((i) => i.id === g.seciliIhbar)
    const k = kumele('ihbarlar', secili.length ? veri.filter((i) => i.id !== g.seciliIhbar) : veri, g.zoom ?? 0, {
      konum: (d) => [d.lon, d.lat],
      enCokZoom: KUME_EN_COK_ZOOM.ihbarlar,
      altTur: (d) => d.tur,
    })
    L.push(
      ...kumeKatmanlari(
        'ihbarlar',
        k.kumeler,
        (x) => `ihbar-${baskinTur(x) || 'metin'}` as SimgeTuru,
        () => tokenRenk('--color-ground'),
      ),
      new IconLayer<Ihbar>({
        ...SIMGE_ORTAK,
        id: 'ihbarlar',
        data: secili.length ? [...k.tekler, ...secili] : k.tekler,
        getPosition: (d) => [d.lon, d.lat],
        getIcon: (d) => ikon(`ihbar-${d.tur}` as SimgeTuru, g.seciliIhbar === d.id),
        getSize: (d) => (g.seciliIhbar === d.id ? 30 : 22),
        // Kapanan ihbar sönük.
        getColor: (d) => [255, 255, 255, d.durum === 'kapandi' ? 110 : 255],
        updateTriggers: { getIcon: g.seciliIhbar, getSize: g.seciliIhbar },
      }),
    )
  }

  // SOS kümesi içindeki en acil önceliğin rengini alır; seçili SOS kümeye girmez.
  const sosSecili = g.sos.filter((c) => c.id === g.seciliSos)
  const sosK = kumele('sos', sosSecili.length ? g.sos.filter((c) => c.id !== g.seciliSos) : g.sos, g.zoom ?? 0, {
    konum: (d) => [d.lon, d.lat],
    enCokZoom: KUME_EN_COK_ZOOM.sos,
    oncelik: (d) => SOS_ONCELIK[d.oncelik] ?? 1,
  })
  const sosKumeTuru = (k: Kume): SimgeTuru =>
    k.ozet.enYuksek >= 3 ? 'sos-kritik' : k.ozet.enYuksek === 2 ? 'sos-yuksek' : 'sos-orta'
  L.push(
    ...kumeKatmanlari('sos', sosK.kumeler, sosKumeTuru, (k) =>
      tokenRenk(sosKumeTuru(k) === 'sos-kritik' ? '--color-ink' : '--color-ground'),
    ),
    new IconLayer<SosCagrisi>({
      ...SIMGE_ORTAK,
      id: 'sos',
      data: sosSecili.length ? [...sosK.tekler, ...sosSecili] : sosK.tekler,
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
    // Uçlar etiketli (J-190): iki nokta A ve B, duraklar
    // 1, 2, 3…; hangi noktanın hangisi olduğu haritadan okunur.
    const uclar: { p: [number, number]; bas: boolean; etiket: string }[] = gz.duraklar?.length
      ? gz.duraklar.map((p, i) => ({ p, bas: i === 0, etiket: String(i + 1) }))
      : [
          ...(gz.bas ? [{ p: gz.bas, bas: true, etiket: 'A' }] : []),
          ...(gz.hedef ? [{ p: gz.hedef, bas: false, etiket: 'B' }] : []),
        ]
    if (uclar.length) {
      L.push(
        new ScatterplotLayer<(typeof uclar)[number]>({
          id: 'guzergah-uclari',
          data: uclar,
          getPosition: (d) => d.p,
          getRadius: 11,
          radiusUnits: 'pixels',
          getFillColor: (d) => (d.bas ? [...vurgu, 255] : [232, 236, 244, 255]),
          stroked: true,
          lineWidthMinPixels: 2,
          getLineColor: [...zemin, 255],
        }),
        new TextLayer<(typeof uclar)[number]>({
          id: 'guzergah-uclari-etiket',
          data: uclar,
          getPosition: (d) => d.p,
          getText: (d) => d.etiket,
          getSize: tokenPx('--text-small'),
          getColor: [...zemin, 255],
          fontFamily: 'IBM Plex Sans, sans-serif',
          fontWeight: 600,
          characterSet: 'ABCDEFGHIJ0123456789',
          getTextAnchor: 'middle',
          getAlignmentBaseline: 'center',
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
const KUME_ADI: Record<string, string> = {
  toplanma: 'toplanma alanı',
  saglik: 'hastane ve sağlık yeri',
  ekipler: 'ekip',
  ihbarlar: 'ihbar',
  sos: 'SOS çağrısı',
}

function kumeIpucu(k: Kume) {
  const turler = Object.entries(k.ozet.turler)
  return ipucuKarti({
    tur: 'Küme',
    baslik: `${k.sayi} ${KUME_ADI[k.tur] ?? 'kayıt'}`,
    satirlar: [
      k.tur === 'sos' && ['En acil', k.ozet.enYuksek >= 3 ? 'Kritik' : k.ozet.enYuksek === 2 ? 'Yüksek' : 'Orta'],
      k.tur === 'ihbarlar' && turler.length > 0
        ? turler.map(([t, n]) => `${IHBAR_TURU[t as IhbarTuru]?.ad ?? t}: ${n}`).join(' · ')
        : null,
    ],
    eylem: 'Tıkla: yakınlaş, küme açılsın',
  })
}

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

/** Son çizilen ısı dokusu: bilgi kartı hücre dökümünü buradan okur. */
let sonIsi: IsiDokusu | null = null

function isiIpucu(bilgi: PickingInfo) {
  const piksel = (bilgi as PickingInfo & { bitmap?: { pixel: [number, number] } }).bitmap?.pixel
  const h = piksel && sonIsi?.hucre(piksel[0], piksel[1])
  if (!h) return null
  // Sunucu ölçeği mutlak: 1,0 ≈ aynı 0,5 km içinde 3 birim ağırlıklı bildirim.
  const yaklasik = h.yogunluk * 3
  return ipucuKarti({
    tur: 'Birleşik ısı',
    baslik: paylarMetni(h.paylar) || 'Isı',
    satirlar: [
      ['Yoğunluk', `%${Math.round(h.yogunluk * 100)}`],
      [
        'Yaklaşık',
        // Ölçek 1,0'da doluyor: tavandaki hücre "en az 3" demektir, kaç olduğu bilinmez.
        h.yogunluk >= 0.99
          ? '3 ya da daha çok bildirim üst üste (ölçek doldu)'
          : yaklasik < 1.5
            ? '1 bildirim çevresi'
            : `${Math.round(yaklasik)} bildirim üst üste`,
      ],
      h.dusulen > 0.01 ? ['Çıkarılan', `%${Math.round(h.dusulen * 100)} (Çıkar ayarlı kaynaklar)`] : null,
    ],
    kaynak: 'Renk kaynağı, koyuluk yoğunluğu gösterir. Ağırlıklar sol panelde. Tahmindir; tek tek noktalara yakınlaşarak bak.',
  })
}

export function haritaIpucu(bilgi: PickingInfo) {
  const { object, layer } = bilgi
  if (layer?.id === 'isi') return isiIpucu(bilgi)
  if (!object || !layer) return null
  if (layer.id.startsWith('kume-')) return kumeIpucu(object as Kume)
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
        baslik:
          (k.durum ?? 'kapali') !== 'kapali'
            ? KAPANMA_DURUM_ADI[k.durum]
            : k.kaynak === 'uydu'
              ? 'Uydu analizinde kapalı'
              : `Kapalı (${k.kaynak})`,
        satirlar: [
          ['Bulundu', tarihSaatYilli(k.zaman)],
          ...(k.durumZaman ? [['Durum', `${KAPANMA_DURUM_ADI[k.durum]} · ${tarihSaatYilli(k.durumZaman)}`] as [string, string]] : []),
          (k.durum ?? 'kapali') === 'kapali'
            ? 'Araç rotası bu yoldan geçmez; başka yol yoksa geçer ve uyarır.'
            : 'Rota bu kaydı artık hesaba katmıyor.',
          'Durumunu değiştirmek için: Yol ve rota → Kapalı yollar.',
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
    case 'risk-ana-sok':
    case 'risk-son-yil': {
      const d = object as RiskDepremi
      const ana = layer.id === 'risk-ana-sok'
      return ipucuKarti({
        tur: ana ? 'Geçmiş büyük deprem (ana şok)' : 'Son bir yılın depremi',
        baslik: `M ${d.m.toFixed(1).replace('.', ',')} · ${d.yil}`,
        satirlar: [
          d.yer,
          ['Tarih', d.zaman.slice(0, 10)],
          ['İle uzaklık', d.km != null ? `${Math.round(d.km)} km` : null],
        ],
        kaynak: ana
          ? 'Katalog (Kandilli, USGS); artçılar ayıklandı. Uzun vadeli olasılık bunlardan hesaplanır'
          : 'Katalog (Kandilli, USGS); kısa vadeli tahminin girdisi',
        eylem: 'Tıkla: sağdaki listede vurgula',
      })
    }
    case 'risk-secili-il':
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
