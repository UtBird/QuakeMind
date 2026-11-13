import { useMutation, useQuery } from '@tanstack/react-query'
import { ApiHatasi, apiGet, apiGorsel, apiPost } from './istemci'
import { useSimulasyon } from '@/durum/simulasyonDurumu'

/* ---------------------------------------------------------------------------
   Simülasyon (tatbikat) modu — SIMULASYON_SOZLESMESI.md.

   Bu dosya SÖZLEŞMEYE bağlanır, modele değil (CLAUDE.md kural 2). Alan adları
   belgedeki §2 ve §4 ile birebirdir; bir alan değişirse önce o belge güncellenir.

   Uçlar backend'de yazılırken arayüz çalışabilsin diye sorgular gerçekten istek
   atar: uç yoksa hata döner ve paneller "veri yok" yazar. Uydurma veri üretilmez
   (kural 1).

   İki yer sözleşmeden sapıyor, ikisi de burada karşılanıyor (J-62):
   · Koordinat sırası. §4'te çizgiler `[[lat, lon], …]`; deck.gl `[lon, lat]`
     ister. Çevirme harita katmanında, tek yerde yapılır (`simKatmanlari.ts`).
   · Kısmi sonuç. §3 "arayüz her mesajda yalnız o katmanı ister" diyor ama tek
     sonuç ucu var; bu yüzden sonucun bölümleri isteğe bağlı tutulur ve ekran
     eldekini çizer.
--------------------------------------------------------------------------- */

/** Sözleşmede [lat, lon] sırasıyla gelen çizgi. Haritaya verilirken çevrilir. */
export type LatLonCizgi = [number, number][]

export type SimKatmanKunyesi = {
  id: string
  ad: string
  saglayici: string
  cekimTarihi: string
  /** Sözleşmede zorunlu; bugünkü uç göndermiyor (J-62). */
  gsdM?: number
  kapsamKm2?: number
  /** Ucun sözleşmeye eklediği alanlar. */
  kaynak?: string
  oamBasligi?: string
  /** OAM karo şablonu; tatbikatta zemine modelin baktığı görüntü serilir. */
  oamTmsUrl?: string
  waybackId?: string
  bbox?: [number, number, number, number] | null
  yaricapKm?: number
  gercek?: boolean
  not?: string
}

export type SimAlan = {
  id: string
  ad: string
  /** Sözleşmede alan düzeyinde; uçta katman düzeyinde geliyor (J-62). */
  bbox?: [number, number, number, number]
  alanKm2?: number
  merkez?: { lat: number; lon: number }
  katmanlar: SimKatmanKunyesi[]
}

export type SimModel = {
  id: string
  ad: string
  mimari: string
  sinamaIoU: number
  /** Sözleşmede `agirlikSha1`; uç `agirlikSha256` gönderiyor (J-62). */
  agirlikSha1?: string
  agirlikSha256?: string
  /** Ölçülene kadar null; null ise ekran süre YAZMAZ (kural 8). Uç bunu
      `ileriGecis512Sn` adıyla ve ölçüm notuyla gönderiyor. */
  tahminiSureSn?: number | null
  ileriGecis512Sn?: number | null
  olcumNotu?: string
  kunye?: string
  esik?: number
  hazir?: boolean
}

export type SimKosIstegi = {
  alanId: string
  katmanId: string
  modelId: string
  esik: number
  kapanmaYaricapiM: number
  yumusakMaliyet: boolean
  lambda: number | null
  ekipSayisi: number
  afetzedeSayisi: number
  tohum: number
}

/** POST /api/simulasyon/kos → HTTP 202 (istek yolunda çıkarım yok, kural 3). */
export type SimKosYaniti = { isId: string; parmakIzi: string; onbellekten: boolean }

export type SimKenar = { id: string; cizgi: LatLonCizgi; carpan?: number }

export type SimRotaVaryanti = { cizgi: LatLonCizgi; uzunlukM: number; sureDk: number }

export type SimVaryantId = 'depremOncesi' | 'kapanmali' | 'riskli'

export type SimUc = { lat: number; lon: number; ad: string }

export type SimRota = {
  gorevId: string
  baslangic: SimUc
  hedef: SimUc
  varyantlar: Partial<Record<SimVaryantId, SimRotaVaryanti>>
  arama: {
    dijkstra: { uzunlukM: number; sureSn: number }
    astar: { uzunlukM: number; sureSn: number }
    ayniYol: boolean
  }
}

export type SimGorev = {
  id: string
  /** Ucun eklediği alanlar: araç yolunun bittiği yerden kalan yürüme (J-62). */
  sonAdimYurumeM?: number
  sonAdimYurumeDk?: number
  ekipId: string
  ekipAd: string
  /** Ekip üssü gerçek bir OSM tesisi mi (§6). */
  gercekTesis: boolean
  afetzedeId: string
  afetzedeAd: string
  /** Afetzede konumu üretilmiştir; ekranda "senaryo" etiketiyle görünür (§6). */
  senaryo: boolean
  hedefTur: string
  etaDk: number
  durum: string
}

export type SimKanal<T> = {
  kayitlar: T[]
  not?: string
  hata?: string
  fotoKaynagi?: string
}

type SimKanalOrtak = {
  id: string
  lat: number
  lon: number
  skor: number
  guven: number
  zaman: number
  kaynak: string
  etiket: string
  sentetikKonum: true
  konumNotu: string
  hasarBlobPiksel: number
}

export type SimKameraKaydi = SimKanalOrtak & {
  foto: {
    dosya: string
    baslik: string
    lisans: string
    yazar: string
    kaynakSayfa: string
    sha256: string
    gercek: true
  }
  tespitSayisi: number
  catlakSayisi: number
  binaSayisi: number
  kritik: boolean
  cikarimMs: number
  modeller: string[]
  tespitler: { label: string; sinif: string; confidence: number; model: string }[]
}

export type SimMetinKaydi = SimKanalOrtak & {
  sentetikMetin: true
  metin: string
  beklenen?: string
  ortusuyor: boolean
  elendi: boolean
  aciliyet: number
  yerAdaylari: string[]
  modelKonumu?: [number, number] | null
  modelKonumMetni?: string | null
  cikarimMs: number
}

export type SimSonuc = {
  isId: string
  /** Sözleşme §4: ilerleme YÜZDE (0–100), SSE ile aynı ölçek. */
  ilerleme?: number
  parmakIzi: string
  /** Kuyruktaki ya da hata veren koşuda YOK — `sonucuNormalle` de öyle okuyor. */
  alan?: { id: string; ad: string; bbox: [number, number, number, number] }
  /** Kuyruktaki ya da hata veren koşuda YOK. */
  kaynak?: {
    katmanId: string
    saglayici: string
    cekimTarihi: string
    gsdM: number
    /** Görüntü gerçek mi (§6 tablosu). */
    gercek: boolean
  }
  model: { id: string; mimari: string; agirlikSha1: string; esik: number }
  hasar?: {
    maskeUrl: string
    bbox: [number, number, number, number]
    hasarliPikselOrani: number
    noktaSayisi: number
    /** Aynı model, deprem öncesi görüntü: yanlış alarm tabanı (§2). */
    oncesiKontrol?: { kosuldu: boolean; hasarliPikselOrani: number }
  }
  kapanma?: {
    yaricapM: number
    kapaliKenarSayisi: number
    cezaliKenarSayisi: number
    kapaliKenarlar: SimKenar[]
    cezaliKenarlar: SimKenar[]
  }
  rotalar?: SimRota[]
  gorevler?: SimGorev[]
  /** Bütün ekip–afetzede çiftlerinden; ekranda yalnız özet (§4). */
  olcum?: {
    ciftSayisi: number
    /** Uzama yalnız araçla ulaşılan çiftlerden alınır (yürüme gerekenler dışarıda);
        öyle çift yoksa sunucu null döner — ekran "hesaplanamadı" yazar, sıfır değil. */
    uzamaHesabindakiCift?: number
    ortalamaUzamaM: number | null
    ortalamaUzamaYuzde: number | null
    ulasilamayanCift: number
    /* Ucun eklediği gerçek ölçümler (J-62). */
    enBuyukUzamaM?: number
    ortalamaYurumeM?: number
    yurumeGerekenCift?: number
    /** Süreye çevirirken kullanılan hız varsayımı. */
    hizKmh?: number
  }
  /** Kıyas kolları: anahtar = kolun adı ("Kapanmayı bilmeyen ekip", "QuakeMind"…).
      Kod adı (R0–R3) kullanılmaz; ad doğrudan ekrana yazılır. */
  referansAjanlar?: Record<
    string,
    /** ortalamaSureDk: kolun araçla ulaştığı görev yoksa null. */
    { ortalamaSureDk: number | null; uDonusuSayisi?: number; ulasanGorev?: number }
  >
  /** Dönüş maliyeti (sağdan trafik) uygulandı mı — panel varsayımı yazar. */
  donusMaliyetli?: boolean
  /** Kolların FİİLEN sürdüğü yollar (ilk tur). Planlanan varyantlar bunu
      göstermiyor; manşet sayı ise buradan geliyor, o yüzden haritada çizilir. */
  izlenenYollar?: Record<string, LatLonCizgi[]>
  /** Yer seviyesi kanallar (J-108). Fotoğraf ve model çıktısı GERÇEK;
      metinler ve her ikisinin KONUMU ÜRETİLMİŞTİR — her kayıt bunu
      `sentetikKonum` / `sentetikMetin` ile kendi içinde söyler. */
  kanallar?: {
    kamera?: SimKanal<SimKameraKaydi>
    metin?: SimKanal<SimMetinKaydi>
  } | null
  /* Sözleşmede olmayan, ucun verdiği gerçek ölçümler (J-62). */
  /** Aşama süreleri (ms): uydu, yol, çıkarım, lojistik, toplam. */
  sureler?: Record<string, number>
  /** Sunucunun koşu günlüğü; ekranda son satır gösterilir. */
  gunluk?: string[]
  durum?: string
  mesaj?: string
}

/* ---- sorgular ----------------------------------------------------------- */

/** Uç ya düz dizi ya da tek anahtarlı sarmal döndürüyor (J-62): ikisi de
    kabul edilir, yoksa boş liste. Panel çökmez. */
function liste<T>(yanit: unknown, anahtar: string): T[] {
  if (Array.isArray(yanit)) return yanit as T[]
  const kutu = (yanit as Record<string, unknown> | null)?.[anahtar]
  return Array.isArray(kutu) ? (kutu as T[]) : []
}

export function useSimAlanlar() {
  return useQuery({
    queryKey: ['simulasyon', 'alanlar'],
    queryFn: async () => liste<SimAlan>(await apiGet<unknown>('/api/simulasyon/alanlar'), 'alanlar'),
  })
}

export function useSimModeller() {
  return useQuery({
    queryKey: ['simulasyon', 'modeller'],
    queryFn: async () => liste<SimModel>(await apiGet<unknown>('/api/simulasyon/modeller'), 'modeller'),
  })
}

/** Koşuyu başlatır. 202 döner; sonuç canlı akıştan haber gelince istenir. */
export function useSimKos() {
  return useMutation({
    mutationFn: (istek: SimKosIstegi) => apiPost<SimKosYaniti>('/api/simulasyon/kos', istek),
  })
}

export type SimBitirYaniti = { isId: string; durum: string; silinenHasarNoktasi: number }

/** Tatbikatı bitirir: koşunun yazdığı hasar noktaları silinir, konsol normal
    akışa döner. Sunucu canlı akışa `durum: 'iptal'` yayınlar, böylece AÇIK olan
    bütün istemciler aynı anda çıkar — tek ekranı temizlemek yetmez. */
export function useSimBitir() {
  return useMutation({
    mutationFn: (isId: string) => apiPost<SimBitirYaniti>('/api/simulasyon/bitir', { isId }),
  })
}

/* ---- ucun biçimini sözleşmeye çevirme (J-62) ---------------------------
   Uç bugün sözleşmeden üç yerde ayrılıyor; ikisi de kabul edilir ki tatbikat
   bugün çalışsın. Sözleşme güncellenince bu çeviriler sadeleşir.
     · bbox: sözleşmede [batı, güney, doğu, kuzey]; uçta {west, south, east, north}.
     · kapalı kenar: sözleşmede {id, cizgi}; uçta doğrudan [lat, lon] dizisi.
     · maskeUrl: sözleşmede /api/simulasyon/kosu/{id}/maske.png; uçta eski
       görsel ucu. Adres neyse o kullanılır.
------------------------------------------------------------------------- */

type Kutu = [number, number, number, number]

function kutuya(x: unknown): Kutu | undefined {
  if (Array.isArray(x) && x.length === 4 && x.every((n) => typeof n === 'number')) return x as Kutu
  const k = x as { west?: number; south?: number; east?: number; north?: number } | null
  if (k && typeof k.west === 'number' && typeof k.south === 'number' && typeof k.east === 'number' && typeof k.north === 'number') {
    return [k.west, k.south, k.east, k.north]
  }
  return undefined
}

function kenarlara(x: unknown): SimKenar[] {
  if (!Array.isArray(x)) return []
  return x
    .map((k, i): SimKenar | null => {
      if (Array.isArray(k)) {
        const cizgi = k.filter((n): n is [number, number] => Array.isArray(n) && n.length >= 2)
        return cizgi.length > 1 ? { id: `kenar-${i}`, cizgi } : null
      }
      const o = k as SimKenar
      return o?.cizgi?.length > 1 ? o : null
    })
    .filter((k): k is SimKenar => k !== null)
}

function sonucuNormalle(ham: Record<string, unknown>): SimSonuc {
  const hasar = ham.hasar as Record<string, unknown> | undefined
  const kapanma = ham.kapanma as Record<string, unknown> | undefined
  const alan = ham.alan as Record<string, unknown> | undefined
  // Uçta ayrı bir `rotalar` dizisi yok: rota alanları görevin içinde geliyor.
  // Sözleşmedeki iki liste burada yeniden kuruluyor (J-62).
  const gorevler = (ham.gorevler ?? []) as Array<SimGorev & Partial<SimRota>>
  const rotalar =
    (ham.rotalar as SimRota[] | undefined) ??
    gorevler
      .filter((g) => g.varyantlar && g.baslangic && g.hedef && g.arama)
      .map((g) => ({
        gorevId: g.id,
        baslangic: g.baslangic!,
        hedef: g.hedef!,
        varyantlar: g.varyantlar!,
        arama: g.arama!,
      }))
  return {
    ...(ham as unknown as SimSonuc),
    rotalar,
    alan: alan
      ? ({ ...alan, bbox: kutuya(alan.bbox) as Kutu } as NonNullable<SimSonuc['alan']>)
      : undefined,
    hasar: hasar
      ? {
          ...(hasar as unknown as NonNullable<SimSonuc['hasar']>),
          bbox: kutuya(hasar.bbox) as Kutu,
        }
      : undefined,
    kapanma: kapanma
      ? {
          ...(kapanma as unknown as NonNullable<SimSonuc['kapanma']>),
          kapaliKenarlar: kenarlara(kapanma.kapaliKenarlar),
          cezaliKenarlar: kenarlara(kapanma.cezaliKenarlar),
        }
      : undefined,
  }
}

/** Koşunun o ana kadarki sonucu. Tazeleme YALNIZ canlı akış mesajıyla olur
    (`tazelenecekler`); burada zamanlayıcı yok (kural 4). */
export function useSimSonuc(isId: string | null) {
  const temizle = useSimulasyon((d) => d.temizle)
  return useQuery({
    queryKey: ['simulasyon', 'kosu', isId],
    enabled: !!isId,
    // Bilinmeyen iş kimliği TEKRAR DENENMEZ ve tatbikat modu kapatılır.
    // Koşu kimliği sekmenin sessionStorage'ında duruyor (J-74); backend
    // yeniden başladığında iş kaydı kayboluyor ama konsol "%0 · sonuç
    // bekleniyor" diye sonsuza kadar asılı kalıyordu (ölçüldü, 26 Eylül).
    retry: (deneme, hata) =>
      !(hata instanceof ApiHatasi && hata.durum === 404) && deneme < 2,
    queryFn: async () => {
      try {
        return sonucuNormalle(
          await apiGet<Record<string, unknown>>(`/api/simulasyon/kosu/${isId}`),
        )
      } catch (hata) {
        if (hata instanceof ApiHatasi && hata.durum === 404) temizle()
        throw hata
      }
    },
  })
}

/** Hasar maskesi PNG'i. Uç yetki istediği için `<img src>` ile çekilemez:
    jetonla indirilip ImageBitmap'e çevrilir. Çözme tarayıcının kendi iş
    parçacığında olur, ana iş parçacığı bloklanmaz (§5 madde 9). */
export function useSimMaske(url: string | undefined) {
  return useQuery({
    queryKey: ['simulasyon', 'maske', url],
    enabled: !!url,
    queryFn: async () => {
      const blob = await apiGorsel(url!)
      return maskeyiBoya(await createImageBitmap(blob))
    },
  })
}

/** Gri maskeyi SAYDAM ALFALI kırmızıya çevirir.

    Uçtan gelen maske siyah zemin + beyaz hasar. Haritaya olduğu gibi konunca
    (opaklık 0,72) koca bir koyu dikdörtgen oluyor ve altındaki drone
    görüntüsünü örtüyordu — ölçüldü, 26 Eylül: tatbikatta enkaz görünmüyordu.
    Hasar pikselinin parlaklığı ALFA'ya, rengi hasar tokenına gider; zemin
    tamamen saydam kalır, enkaz altta okunur.

    Renk kuralı (ARAYUZ §6): kırmızı yalnız hasar içindir — burada tam yerinde. */
async function maskeyiBoya(kaynak: ImageBitmap): Promise<ImageBitmap> {
  const { width: w, height: h } = kaynak
  const tuval =
    typeof OffscreenCanvas !== 'undefined'
      ? new OffscreenCanvas(w, h)
      : Object.assign(document.createElement('canvas'), { width: w, height: h })
  const ctx = (tuval as OffscreenCanvas).getContext('2d') as
    | OffscreenCanvasRenderingContext2D
    | CanvasRenderingContext2D
    | null
  if (!ctx) return kaynak
  ctx.drawImage(kaynak, 0, 0)
  const veri = ctx.getImageData(0, 0, w, h)
  const p = veri.data
  const kok = getComputedStyle(document.documentElement)
  const token = kok.getPropertyValue('--color-high').trim()
  const [kr, kg, kb] = token.startsWith('#')
    ? [1, 3, 5].map((i) => parseInt(token.slice(i, i + 2), 16))
    : [239, 68, 68]
  for (let i = 0; i < p.length; i += 4) {
    const v = p[i]
    p[i] = kr
    p[i + 1] = kg
    p[i + 2] = kb
    p[i + 3] = v // parlaklık = örtme gücü; siyah zemin tamamen saydam
  }
  ctx.putImageData(veri, 0, 0)
  return createImageBitmap(veri)
}

/* ---- yardımcılar -------------------------------------------------------- */

/** "Segformer (mit_b2) · sınama IoU 0,409" — modeli tek satırda tanıtır. */
export function modelOzeti(m: SimModel): string {
  return `${m.mimari} · sınama IoU ${m.sinamaIoU.toFixed(3).replace('.', ',')}`
}

/** Ölçülmüş süre (saniye) ya da null. Sözleşmedeki ad `tahminiSureSn`, uçtaki
    `ileriGecis512Sn` (512×512 tek ileri geçiş). Yoksa ekran süre yazmaz. */
export function modelSuresiSn(m: SimModel): number | null {
  return m.tahminiSureSn ?? m.ileriGecis512Sn ?? null
}

/** Sözleşmedeki varyant adlarının ekrandaki karşılığı (§4). */
export const VARYANT_ADI: Record<SimVaryantId, string> = {
  depremOncesi: 'Kapanma olmasaydı',
  kapanmali: 'QuakeMind güzergâhı',
  riskli: 'Enkazdan uzak',
}

/** Adın altına yazılan tek cümle: hangi kural olduğu anlaşılsın.
    Eski adlar ("Deprem öncesi", "Kapanmalara göre") neyin neye göre
    hesaplandığını söylemiyordu; kullanıcı hangisinin "bilmeseydik" hangisinin
    "bizim bulduğumuz" olduğunu ayıramıyordu (27 Eylül). */
export const VARYANT_ACIKLAMA: Record<SimVaryantId, string> = {
  depremOncesi: 'kapanmalar yok sayılır — kıyas çizgisi',
  kapanmali: 'kapalı yollar çıkarılarak bulunan yol',
  riskli: 'kapalılar çıkarılır, hasara yakın kenarlar pahalanır',
}

export const VARYANT_SIRASI: SimVaryantId[] = ['depremOncesi', 'kapanmali', 'riskli']
