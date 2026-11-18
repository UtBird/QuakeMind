import { create } from 'zustand'

/* ---------------------------------------------------------------------------
   Konsolun arayüz durumu (sunucu verisi değil — o TanStack Query'de).
   Modlar sayfa değildir: mod değişince harita yerinde kalır, paneller ve
   açık katmanlar değişir (MIMARI §7, ARAYUZ §8).
--------------------------------------------------------------------------- */

/** Hasar analizi modunda soldan seçilen görüntünün karo adresi; harita
    katmanı buradan okur (mod paneli ile kabuk arasındaki tek bağ). */
export type AnalizKarosu = { url: string; kunye: string; ortuculuk?: number } | null

export const KATMANLAR = [
  'analizGoruntusu',
  'analizSonucu',
  'yapilar',
  'yollar',
  'hasarliYollar',
  'isi',
  'depremler',
  'toplanma',
  'saglik',
  'ekipler',
  'faylar',
  'ihbarlar',
  // Tatbikat katmanları (SIMULASYON_SOZLESMESI.md §5): yalnız simülasyon
  // modunda önerilir, koşu yoksa hiçbir şey çizmez.
  'simHasar',
  'simKapanma',
  'simRota',
  'simGorev',
  'simKamera',
  'simMetin',
] as const
export type KatmanId = (typeof KATMANLAR)[number]

export const KATMAN_ADI: Record<KatmanId, string> = {
  analizGoruntusu: 'Analiz görüntüsü (modelin gördüğü)',
  analizSonucu: 'Analiz sonucu (kapalı yollar)',
  yapilar: 'Yapılar',
  yollar: 'Yol ağı',
  hasarliYollar: 'Yol kapanmaları',
  isi: 'Birleşik ısı',
  depremler: 'Depremler',
  toplanma: 'Toplanma alanları',
  saglik: 'Hastane ve sağlık',
  ekipler: 'Saha ekipleri',
  faylar: 'Fay hatları',
  ihbarlar: 'Afetzede ihbarları',
  simHasar: 'Tatbikat: hasar maskesi',
  simKapanma: 'Tatbikat: kapanan yollar',
  simRota: 'Tatbikat: rotalar',
  simGorev: 'Tatbikat: ekip ve afetzede',
  simKamera: 'Tatbikat: kamera tespiti (YOLO)',
  simMetin: 'Tatbikat: metin ihbarı (BERTurk)',
}

/** Katmanın grubu, kaynağı ve haritaya bağlı olup olmadığı (J-56). Kaynak her
    katmanın yanında yazılır (kural 1). `bagli: false` katman haritada henüz
    çizilmiyor: anahtarı yok, "bağlanmadı" yazar. Eskiden anahtarı vardı ama
    hiçbir şey çizmiyordu (hasarlı yollar boş veriyle, ötekiler hiç). */
export const KATMAN_BILGI: Record<
  KatmanId,
  { grup: 'olay' | 'hasar' | 'yer' | 'altlik' | 'tatbikat'; kaynak: string; bagli: boolean }
> = {
  ihbarlar: { grup: 'olay', kaynak: 'Afetzede ekranı: fotoğraf (YOLO), yazılı (BERTurk), ihtiyaç', bagli: true },
  ekipler: { grup: 'olay', kaynak: 'Ekip kaydı; konum ekibin telefonundan ya da koordinasyondan', bagli: true },
  isi: { grup: 'hasar', kaynak: 'Uydu, SOS, kamera ve metin noktaları; ızgara sunucuda', bagli: true },
  analizGoruntusu: {
    grup: 'hasar',
    kaynak: 'Soldan seçilen görüntü kaynağı: Google, Esri Wayback ya da OpenAerialMap',
    bagli: true,
  },
  analizSonucu: { grup: 'hasar', kaynak: 'Bu oturumda biten uydu analizi (Hasar analizi modu)', bagli: true },
  hasarliYollar: {
    grup: 'hasar',
    kaynak: 'Uydu analizinin yazdığı kapanmalar; kapalı yol parçasının orta noktası',
    bagli: true,
  },
  depremler: {
    grup: 'hasar',
    kaynak: 'Deprem kataloğu (Kandilli, USGS); M ≥ 4, geçmiş kayıt',
    bagli: true,
  },
  faylar: {
    grup: 'hasar',
    kaynak: 'GEM etkin fay hatları; veri setinde ad alanı boş',
    bagli: true,
  },
  yapilar: { grup: 'altlik', kaynak: 'OpenStreetMap, yerel kopya; yakınlaşınca çizilir', bagli: true },
  yollar: { grup: 'altlik', kaynak: 'OpenStreetMap, yerel kopya', bagli: true },
  toplanma: {
    grup: 'yer',
    kaynak: 'AFAD toplanma alanları listesi; şehir ölçeğine yakınlaşınca çizilir',
    bagli: true,
  },
  saglik: {
    grup: 'yer',
    kaynak: 'OpenStreetMap (hastane, sağlık merkezi); şehir ölçeğine yakınlaşınca çizilir',
    bagli: true,
  },
  // Tatbikat katmanları: gerçek olan ne, üretilen ne — her satır kendi yazıyor
  // (SIMULASYON_SOZLESMESI.md §6).
  simHasar: {
    grup: 'tatbikat',
    kaynak: 'Kendi modelimizin çıktısı; gerçek, tarihli uydu/drone görüntüsü üzerinde',
    bagli: true,
  },
  simKapanma: {
    grup: 'tatbikat',
    kaynak: 'Hasar maskesinden türetildi; yol ağı OpenStreetMap',
    bagli: true,
  },
  simRota: {
    grup: 'tatbikat',
    kaynak: 'Dijkstra ve A* ile OSM yol ağında hesaplandı; üç varyant',
    bagli: true,
  },
  simGorev: {
    grup: 'tatbikat',
    kaynak: 'Ekip üssü gerçek OSM tesisi; afetzede konumu ÜRETİLEN senaryo',
    bagli: true,
  },
  simKamera: {
    grup: 'tatbikat',
    kaynak:
      'Fotoğraf GERÇEK (6 Şubat 2023, Wikimedia Commons, PD/CC BY-SA) ve YOLO çıktısı gerçek; haritadaki konum ÜRETİLDİ',
    bagli: true,
  },
  simMetin: {
    grup: 'tatbikat',
    kaynak:
      'Metin ÜRETİLDİ (elle yazıldı), BERTurk sınıflandırması gerçek; haritadaki konum ÜRETİLDİ',
    bagli: true,
  },
}

export const KATMAN_GRUBU = {
  olay: 'Olaylar ve ekipler',
  hasar: 'Hasar',
  yer: 'Yerler',
  altlik: 'Altlık',
  tatbikat: 'Tatbikat (simülasyon)',
} as const

/** Isı haritasının dört kanalı (MIMARI §5). */
export const KANALLAR = ['sat', 'sos', 'cam', 'nlp'] as const
export type KanalId = (typeof KANALLAR)[number]

export const KANAL_BILGI: Record<KanalId, { ad: string; kaynak: string; renk: string }> = {
  sat: { ad: 'Uydu hasar tespiti', kaynak: 'SegFormer bölütleme çıktısı', renk: 'var(--color-ch-sat)' },
  sos: { ad: 'SOS çağrıları', kaynak: 'vatandaş acil çağrıları', renk: 'var(--color-ch-sos)' },
  cam: { ad: 'Kamera tespiti', kaynak: 'saha fotoğrafları · YOLO', renk: 'var(--color-ch-cam)' },
  nlp: { ad: 'Metin ihbarı', kaynak: 'metin analizi · BERTurk', renk: 'var(--color-ch-nlp)' },
}

type Agirliklar = Record<KanalId, number>

export const KARISIM_HAZIRLARI = [
  {
    id: 'genel',
    etiket: 'Genel durum',
    w: { sat: 1, sos: 1, cam: 1, nlp: 1 } as Agirliklar,
    not: 'Bütün kaynaklar birlikte: nerede hasar yoğun?',
  },
  {
    id: 'cagri',
    etiket: 'Yalnız çağrılar',
    w: { sat: 0, sos: 1, cam: 0, nlp: 1 } as Agirliklar,
    not: 'Yalnızca vatandaştan gelen çağrılar: ekip talebi olan yerler.',
  },
  {
    id: 'sessiz',
    etiket: 'Sessiz bölgeler',
    w: { sat: 1, sos: -1, cam: -0.6, nlp: -0.6 } as Agirliklar,
    not: 'Uydu yıkık gösteriyor ama oradan çağrı gelmemiş. Kimsenin haber veremediği yerler.',
  },
] as const

export type KarisimId = (typeof KARISIM_HAZIRLARI)[number]['id']

/** SOS kuyruğu ve ekip listesi süzgeçleri: sol paneldeki seçim sağdaki listeyi
    süzer. Eskiden durum sol panelde kalıyordu ve liste süzülmüyordu (J-54). */
export type SosSuzgeci = 'bekleyen' | 'kritik' | 'atanan' | 'tum'
export type EkipSuzgeci = 'tum' | 'musait' | 'gorevde' | 'hizmet-disi'

type KonsolDurumu = {
  katmanlar: Record<KatmanId, boolean>
  sosSuzgeci: SosSuzgeci
  ekipSuzgeci: EkipSuzgeci
  agirliklar: Agirliklar
  karisim: KarisimId | null
  seciliKayit: { tip: 'sos' | 'yol' | 'yapi' | 'ihbar'; id: string } | null
  komutPaletiAcik: boolean

  katmanDegistir: (id: KatmanId, acik?: boolean) => void
  katmanlariAyarla: (acik: KatmanId[]) => void
  agirlikAyarla: (id: KanalId, deger: number) => void
  karisimSec: (id: KarisimId) => void
  kayitSec: (kayit: KonsolDurumu['seciliKayit']) => void
  komutPaleti: (acik: boolean) => void
  sosSuzgeciSec: (s: SosSuzgeci) => void
  ekipSuzgeciSec: (s: EkipSuzgeci) => void
  analizKarosu: AnalizKarosu
  analizKarosuYaz: (k: AnalizKarosu) => void
}

const BASLANGIC: Record<KatmanId, boolean> = {
  analizGoruntusu: true,
  analizSonucu: true,
  yapilar: true,
  yollar: true,
  hasarliYollar: true,
  isi: true,
  depremler: true,
  toplanma: false,
  saglik: false,
  ekipler: true,
  faylar: false,
  ihbarlar: true,
  // Tatbikat katmanları yalnız simülasyon modunda önerilir; koşu yoksa zaten
  // hiçbir şey çizmezler.
  simHasar: false,
  simKapanma: false,
  simRota: false,
  simGorev: false,
  simKamera: false,
  simMetin: false,
}

export const useKonsol = create<KonsolDurumu>((set) => ({
  katmanlar: BASLANGIC,
  sosSuzgeci: 'bekleyen',
  ekipSuzgeci: 'tum',
  agirliklar: { sat: 1, sos: 1, cam: 1, nlp: 1 },
  karisim: 'genel',
  seciliKayit: null,
  komutPaletiAcik: false,

  katmanDegistir: (id, acik) =>
    set((d) => ({ katmanlar: { ...d.katmanlar, [id]: acik ?? !d.katmanlar[id] } })),

  katmanlariAyarla: (acik) =>
    set(() => {
      const yeni = { ...BASLANGIC }
      for (const k of KATMANLAR) yeni[k] = acik.includes(k)
      return { katmanlar: yeni }
    }),

  agirlikAyarla: (id, deger) =>
    set((d) => ({ agirliklar: { ...d.agirliklar, [id]: deger }, karisim: null })),

  karisimSec: (id) => {
    const h = KARISIM_HAZIRLARI.find((x) => x.id === id)
    if (h) set({ karisim: id, agirliklar: { ...h.w } })
  },

  kayitSec: (kayit) => set({ seciliKayit: kayit }),
  komutPaleti: (acik) => set({ komutPaletiAcik: acik }),
  sosSuzgeciSec: (sosSuzgeci) => set({ sosSuzgeci }),
  ekipSuzgeciSec: (ekipSuzgeci) => set({ ekipSuzgeci }),
  analizKarosu: null,
  // Aynı adres ikinci kez yazılmaz: karo nesnesi her çizimde yeniden kurulduğu
  // için kıyas adres üzerinden yapılır, yoksa sonsuz güncelleme olur.
  analizKarosuYaz: (k) =>
    set((d) => (d.analizKarosu?.url === k?.url ? d : { analizKarosu: k })),
}))
