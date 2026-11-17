import {
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
import { IHBAR_DURUMU, IHBAR_TURU, ihbarBasligi, ihbarKonumu, type Ihbar, type IhbarTuru } from '@/veri/ihbar'
import type { BelirsizlikCemberi } from '@/veri/metin'
import { DEPREM_EN_AZ, type Deprem, type Fay, type Kapanma, type ToplanmaAlani } from '@/veri/katman'
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

/* Veri katmanları altlıktan belirgin şekilde ayrılır: altlık soğuk ve sönük,
   veri sıcak ve doygun (ARAYUZ §11). Hasar renkleri haritada ve panelde aynıdır. */

const ONCELIK_RENK: Record<SosCagrisi['oncelik'], [number, number, number, number]> = {
  kritik: [255, 92, 92, 240],
  yuksek: [255, 145, 82, 235],
  orta: [242, 193, 78, 225],
}

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
      new ScatterplotLayer<Kapanma>({
        id: 'yol-kapanmalari',
        data: noktali,
        getPosition: (d) => [d.lon, d.lat],
        getRadius: 14,
        radiusUnits: 'meters',
        radiusMinPixels: 3,
        radiusMaxPixels: 9,
        getFillColor: [...tokenRenk('--color-high'), 235],
        stroked: true,
        getLineColor: [...tokenRenk('--color-ground'), 220],
        lineWidthUnits: 'pixels',
        getLineWidth: 1,
        pickable: true,
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
      new ScatterplotLayer<ToplanmaAlani>({
        id: 'toplanma',
        data: g.toplanma,
        getPosition: (d) => [d.lon, d.lat],
        getRadius: 16,
        radiusUnits: 'meters',
        radiusMinPixels: 2.5,
        radiusMaxPixels: 8,
        getFillColor: [...tokenRenk('--color-yer-toplanma'), 225],
        stroked: true,
        getLineColor: [...tokenRenk('--color-ground'), 200],
        lineWidthUnits: 'pixels',
        getLineWidth: 1,
        pickable: true,
      }),
    )
  }

  // Hasar noktaları birleşik ısının kaynağıdır; ısıyla birlikte açılır.
  // ("Yapılar" bayrağı artık altlıktaki yapıları çizer.)
  if (g.katmanlar.isi) {
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
      new ScatterplotLayer<KonumluEkip>({
        id: 'ekipler',
        data: ekipler,
        getPosition: (d) => [d.lon, d.lat],
        getRadius: 30,
        radiusMinPixels: 5,
        radiusMaxPixels: 11,
        getFillColor: (d) =>
          d.gorev
            ? [...tokenRenk('--color-ink'), 245]
            : d.durum === 'hizmet-disi'
              ? [...tokenRenk('--color-ink-3'), 220]
              : [...vurgu, 240],
        stroked: true,
        lineWidthMinPixels: 1.8,
        getLineColor: (d) => (d.gorev ? [...vurgu, 255] : [...tokenRenk('--color-ground'), 255]),
        pickable: true,
      }),
      new TextLayer<KonumluEkip>({
        id: 'ekip-adlari',
        data: ekipler,
        getPosition: (d) => [d.lon, d.lat],
        getText: (d) => d.ad,
        getSize: tokenPx('--text-small'),
        getColor: [...tokenRenk('--color-ink'), 255],
        getPixelOffset: [0, -16],
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
      new ScatterplotLayer<Ihbar>({
        id: 'ihbarlar',
        data: veri,
        getPosition: (d) => [d.lon, d.lat],
        getRadius: (d) => (g.seciliIhbar === d.id ? 46 : 30),
        radiusUnits: 'meters',
        radiusMinPixels: 4,
        radiusMaxPixels: 12,
        getFillColor: (d) => [...tokenRenk(IHBAR_TURU[d.tur].renk), d.durum === 'kapandi' ? 90 : 235],
        stroked: true,
        lineWidthMinPixels: 1.5,
        getLineColor: (d) => (g.seciliIhbar === d.id ? [232, 236, 244, 255] : [10, 14, 20, 220]),
        updateTriggers: { getRadius: g.seciliIhbar, getLineColor: g.seciliIhbar },
        pickable: true,
      }),
    )
  }

  L.push(
    new ScatterplotLayer<SosCagrisi>({
      id: 'sos',
      data: g.sos,
      getPosition: (d) => [d.lon, d.lat],
      getRadius: (d) => (g.seciliSos === d.id ? 52 : 34),
      radiusUnits: 'meters',
      radiusMinPixels: 4.5,
      radiusMaxPixels: 14,
      getFillColor: (d) => ONCELIK_RENK[d.oncelik],
      stroked: true,
      lineWidthMinPixels: 1.6,
      getLineColor: (d) => (g.seciliSos === d.id ? [232, 236, 244, 255] : [10, 14, 20, 220]),
      updateTriggers: { getRadius: g.seciliSos, getLineColor: g.seciliSos },
      pickable: true,
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

export function ipucuKutusu(baslik: string, satirlar: Array<string | null | undefined | false>) {
  const govde = satirlar
    .filter((x): x is string => !!x)
    .map((x) => `<div>${kacis(x)}</div>`)
    .join('')
  return {
    html: `<div class="qm-ipucu"><div class="qm-ipucu-baslik">${kacis(baslik)}</div>${govde}</div>`,
    style: { background: 'transparent', boxShadow: 'none', padding: '0', margin: '0' },
  }
}

export function haritaIpucu({ object, layer }: PickingInfo) {
  if (!object || !layer) return null
  switch (layer.id) {
    case 'sos': {
      const c = object as SosCagrisi
      const ek = sosEkBilgi(c)
      return ipucuKutusu(`SOS · ${ONCELIK_ADI[c.oncelik].toLocaleLowerCase('tr')} aciliyet`, [
        sevkSatiri(c.durum, c.gorevler),
        c.mahalle,
        ek.kisiIhtiyac,
        c.metin,
        ek.yaklasik && ek.konum,
        tarihSaat(c.zaman),
        'Tıkla: seç ve yakınlaş',
      ])
    }
    case 'ihbarlar': {
      const i = object as Ihbar
      return ipucuKutusu(ihbarBasligi(i), [
        IHBAR_DURUMU[i.durum].ad,
        gorevOzeti(i.gorevler),
        i.tur === 'ihtiyac' && i.kisiSayisi ? `${i.kisiSayisi} kişi` : null,
        i.metin && i.metin.length > 140 ? `${i.metin.slice(0, 140)}…` : i.metin,
        ihbarKonumu(i),
        tarihSaat(i.zaman),
        'Tıkla: seç ve yakınlaş',
      ])
    }
    case 'konum-belirsizligi':
    case 'konum-belirsizligi-merkez': {
      const b = object as KonumBelirsizligi
      return ipucuKutusu(b.baslik, [b.aciklama])
    }
    case 'hasar-noktalari': {
      const h = object as HasarNoktasi
      return ipucuKutusu(KAYNAK_ADI[h.kaynak], [
        `Hasar skoru %${Math.round(h.skor * 100)} · güven %${Math.round(h.guven * 100)}`,
        tarihSaat(h.zaman),
      ])
    }
    case 'ekipler': {
      const e = object as Ekip
      return ipucuKutusu(e.ad, [
        [kurumTur(e), e.kisiSayisi ? `${e.kisiSayisi} kişi` : null].filter(Boolean).join(' · '),
        ekipSatiri(e),
        e.konumZamani ? `Konum: ${e.yerAdi ? `${e.yerAdi} yakını, ` : ''}${tarihSaat(e.konumZamani)}` : null,
      ])
    }
    case 'analiz-kapali':
      return ipucuKutusu('Kapalı yol', ['Uydu analizinden: modelin tahmini, sahada doğrulanmadı.'])
    case 'yol-kapanmalari': {
      const k = object as Kapanma
      return ipucuKutusu('Yol kapanması', [
        k.kaynak === 'uydu' ? 'Uydu analizinden: modelin tahmini, sahada doğrulanmadı.' : `Kaynak: ${k.kaynak}`,
        'Kapalı bulunan yol parçasının orta noktası.',
        tarihSaatYilli(k.zaman),
      ])
    }
    case 'depremler': {
      const d = object as Deprem
      return ipucuKutusu(`M ${d.buyukluk.toFixed(1)} deprem`, [
        d.yer,
        d.derinlikKm != null ? `Derinlik ${d.derinlikKm.toFixed(0)} km` : null,
        tarihSaatYilli(d.zaman),
        'Katalog kaydı (Kandilli, USGS); bugünün hasarı değil.',
      ])
    }
    case 'faylar':
      return ipucuKutusu('Etkin fay hattı', [
        'GEM Global Active Faults; veri setinde ad alanı boş.',
        'Jeolojik başvuru: bugünkü hasarla ilgisi yok.',
      ])
    case 'toplanma': {
      const t = object as ToplanmaAlani
      return ipucuKutusu(t.ad ?? 'Toplanma alanı', [
        t.adres,
        'AFAD listesi; alanın şu an açık olduğunu göstermez.',
      ])
    }
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
