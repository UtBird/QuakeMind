import { useQueries, useQuery } from '@tanstack/react-query'
import { apiGet } from './istemci'
import type { Kutu } from '@/durum/secimDurumu'

/* ---------------------------------------------------------------------------
   Harita altlığı (J-40, ARAYUZ §11, MIMARI §8): kendi verimizden çizilir.
   Sunucu yerel OSM kopyasından bir kez üretilmiş bölge paketlerini verir
   (araclar_altlik_uret.py); tarayıcı bir bölgeyi bir kez indirir. Koordinatlar
   1e-5 derece tamsayı, bütün dizi boyunca ardışık fark olarak gelir ve burada
   deck.gl'in ikili biçimine (başlangıç indeksleri + düz dizi) açılır.
--------------------------------------------------------------------------- */

export type AltlikKaynagi = {
  ad: string
  atif: string
  lisans: string
  dosya: string
  /** Yerel OSM kopyasının dosya tarihi. */
  dosyaTarihi: string
}

export type AltlikBolgesi = {
  id: string
  ad: string
  /** `operasyon`: hizmet, yol ağı ve afetzede verisi olan beş bölge.
      `il`: risk ekranının 81 il seçicisi için il merkezi altlığı.
      `ulke`: il dairelerinin ve operasyon bölgelerinin dışında zemin boş
      kalmasın diye tüm Türkiye'yi kapsayan hafif yol iskeleti (J-40 sınırı);
      kutu ve viewport kesişiminden bağımsız her zaman çizilir.
      Eski katalogda alan yok; yoksa operasyon sayılır. */
  tur?: 'operasyon' | 'il' | 'ulke'
  kutu: Kutu
  sayilar: { yol: number; yapi: number; su: number; nehir: number }
  boyutBayt: number
  kaynak: AltlikKaynagi
  uretim: string
}

type KodluKatman = { adet: number; baslangic: number[]; koord: number[] }

type AltlikPaketi = {
  bolge: string
  olcek: number
  yollar: (KodluKatman & { sinif: number })[]
  nehirler: KodluKatman
  su: KodluKatman
  yapilar: KodluKatman
  /** Adlı paketlerde (J-41): OSM `place` noktaları ve sokak adı yerleşimleri. */
  yerler?: { ad: string; tur: string; lon: number; lat: number }[]
  sokaklar?: { ad: string[]; lon: number[]; lat: number[]; aci: number[]; sinif: number[] }
}

/** Haritada yazılan ad. `oncelik` çakışmada hangisinin kalacağını belirler. */
export type Etiket = { ad: string; lon: number; lat: number; aci: number; oncelik: number }

/* Yer türü → çakışma önceliği ve yazıldığı en düşük seviye
   (0 şehir/ilçe, 1 köy, 2 mahalle; bkz. KonsolKabugu etiket seviyesi). */
const YER_TURU: Record<string, { oncelik: number; seviye: 0 | 1 | 2 }> = {
  city: { oncelik: 100, seviye: 0 },
  town: { oncelik: 90, seviye: 0 },
  village: { oncelik: 60, seviye: 1 },
  suburb: { oncelik: 50, seviye: 2 },
  quarter: { oncelik: 48, seviye: 2 },
  neighbourhood: { oncelik: 45, seviye: 2 },
}

/* deck.gl ikili veri biçimi: `length` nesne, `startIndices` her nesnenin ilk
   köşesi, köşeler düz dizide. Nesne bir kez kurulur ve başvurusu değişmez;
   deck.gl veri başvurusu değişince 59 bin yapıyı yeniden üçgenlerdi. */
export type IkiliYol = {
  length: number
  startIndices: Uint32Array
  attributes: { getPath: { value: Float64Array; size: 2 } }
}
export type IkiliCokgen = {
  length: number
  startIndices: Uint32Array
  attributes: { getPolygon: { value: Float64Array; size: 2 } }
}

export type AltlikVerisi = {
  id: string
  /** Sınıf 0 otoyol … 4 patika; dizi patikadan otoyola sıralı (çizim sırası). */
  yollar: { sinif: number; veri: IkiliYol }[]
  nehirler: IkiliYol
  su: IkiliCokgen
  yapilar: IkiliCokgen
  /** Seviyeye göre birikimli yer adları: [0] şehir/ilçe, [1] +köy, [2] +mahalle.
      Diziler bir kez kurulur; seviye değişmedikçe başvuru aynı kalır. */
  yerAdlari: [Etiket[], Etiket[], Etiket[]]
  /** Sokak adları; büyük yol önce. */
  sokakAdlari: Etiket[]
}

function yerAdlariKur(yerler: AltlikPaketi['yerler']): AltlikVerisi['yerAdlari'] {
  const seviyeli = (yerler ?? []).flatMap((y) => {
    const t = YER_TURU[y.tur]
    return t ? [{ seviye: t.seviye, e: { ad: y.ad, lon: y.lon, lat: y.lat, aci: 0, oncelik: t.oncelik } }] : []
  })
  const kadar = (n: number) => seviyeli.filter((x) => x.seviye <= n).map((x) => x.e)
  return [kadar(0), kadar(1), kadar(2)]
}

function sokakAdlariKur(s: AltlikPaketi['sokaklar']): Etiket[] {
  if (!s) return []
  return s.ad.map((ad, i) => ({
    ad,
    lon: s.lon[i],
    lat: s.lat[i],
    aci: s.aci[i],
    oncelik: 30 - 5 * s.sinif[i],
  }))
}

function ac(k: KodluKatman, olcek: number) {
  const koord = new Float64Array(k.koord.length)
  let x = 0
  let y = 0
  for (let i = 0; i < k.koord.length; i += 2) {
    x += k.koord[i]
    y += k.koord[i + 1]
    koord[i] = x / olcek
    koord[i + 1] = y / olcek
  }
  return { length: k.adet, startIndices: Uint32Array.from(k.baslangic), koord }
}

const yolOlarak = (k: KodluKatman, olcek: number): IkiliYol => {
  const { koord, ...g } = ac(k, olcek)
  return { ...g, attributes: { getPath: { value: koord, size: 2 } } }
}

const cokgenOlarak = (k: KodluKatman, olcek: number): IkiliCokgen => {
  const { koord, ...g } = ac(k, olcek)
  return { ...g, attributes: { getPolygon: { value: koord, size: 2 } } }
}

/** Yalnız inmiş paketler; sorgu sonuçları değişmedikçe aynı dizi döner. */
const yuklenenler = (sonuclar: { data?: AltlikVerisi }[]) =>
  sonuclar.flatMap((s) => (s.data ? [s.data] : []))

export function useAltlikKatalogu() {
  return useQuery({
    queryKey: ['altlik-katalog'],
    queryFn: async () => (await apiGet<{ bolgeler: AltlikBolgesi[] }>('/api/altlik')).bolgeler,
  })
}

/** Görünen bölgelerin paketleri; bir kez iner, önbellekte kalır. Adreste
    üretim zamanı sürüm olarak durur: sunucu paketleri günlük önbelleğe
    izin veriyor, yeniden üretilen paket eski adresten gelmesin. */
export function useAltlikPaketleri(bolgeler: AltlikBolgesi[]) {
  return useQueries({
    combine: yuklenenler,
    queries: bolgeler.map(({ id, uretim }) => ({
      queryKey: ['altlik', id, uretim],
      structuralSharing: false,
      queryFn: async (): Promise<AltlikVerisi> => {
        const p = await apiGet<AltlikPaketi>(`/api/altlik/${id}`, { v: uretim })
        return {
          id,
          yollar: [...p.yollar]
            .sort((a, b) => b.sinif - a.sinif)
            .map((y) => ({ sinif: y.sinif, veri: yolOlarak(y, p.olcek) })),
          nehirler: yolOlarak(p.nehirler, p.olcek),
          su: cokgenOlarak(p.su, p.olcek),
          yapilar: cokgenOlarak(p.yapilar, p.olcek),
          yerAdlari: yerAdlariKur(p.yerler),
          sokakAdlari: sokakAdlariKur(p.sokaklar),
        }
      },
    })),
  })
}

/** Hizmet, yol ağı ve afetzede verisi olan bölgeler; il altlıkları hariç. */
export const operasyonBolgeleri = (bolgeler: AltlikBolgesi[]) =>
  bolgeler.filter((b) => (b.tur ?? 'operasyon') === 'operasyon')

export function kutularKesisir(a: Kutu, b: Kutu): boolean {
  return a[0] < b[2] && b[0] < a[2] && a[1] < b[3] && b[1] < a[3]
}
