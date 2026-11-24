import Supercluster from 'supercluster'

/* ---------------------------------------------------------------------------
   Nokta kümeleme (J-191). Uzakta aynı türden yakın noktalar tek bir sayılı
   kümeye iner; yakınlaştıkça kümeler açılır, en sonunda tek tek simgeler kalır.
   Eskiden toplanma alanı ve sağlık yerleri belli bir yakınlığın altında hiç
   çizilmiyordu ("yakınlaşınca görünür"), SOS ve ihbarlar üst üste biniyordu.

   Supercluster (Mapbox, ISC) dizini her yakınlık düzeyi için kümeleri bir kez
   kurar; sorgu O(log n). Dizin veri dizisine bağlıdır (WeakMap): veri
   değişmedikçe yeniden kurulmaz. Yakınlık tam sayıya yuvarlanır, sonuç o
   düzey için saklanır: kaydırma ve ara yakınlıkta deck.gl'e aynı dizi gider,
   GPU'ya yeniden yüklenmez.
--------------------------------------------------------------------------- */

export type KumeOzeti = {
  /** Kümedeki en yüksek öncelik (SOS: 3 kritik, 2 yüksek, 1 orta). */
  enYuksek: number
  /** Türlere göre sayım (ihbar: fotoğraf / metin / ihtiyaç). */
  turler: Record<string, number>
}

export type Kume = {
  tur: string
  lon: number
  lat: number
  sayi: number
  /** Kümenin açıldığı yakınlık; tıklayınca oraya uçulur. */
  genisleme: number
  ozet: KumeOzeti
}

type Ayar<T> = {
  konum: (d: T) => [number, number]
  /** Bu yakınlığın ÜSTÜNDE kümelenmez, hepsi tek tek çizilir. */
  enCokZoom: number
  /** Küme yarıçapı, piksel (512 px karo). */
  yaricap?: number
  oncelik?: (d: T) => number
  altTur?: (d: T) => string
}

type Ozellik = { i: number; enYuksek: number; turler: Record<string, number> }

type Dizin = {
  sc: Supercluster<Ozellik, Ozellik>
  sonuclar: Map<number, { tekler: unknown[]; kumeler: Kume[] }>
}

const dizinler = new WeakMap<object, Map<string, Dizin>>()

function dizinKur<T>(veri: readonly T[], a: Ayar<T>): Dizin {
  const sc = new Supercluster<Ozellik, Ozellik>({
    radius: a.yaricap ?? 56,
    maxZoom: a.enCokZoom,
    minPoints: 2,
    map: (p) => ({ i: -1, enYuksek: p.enYuksek, turler: { ...p.turler } }),
    reduce: (acc, p) => {
      acc.enYuksek = Math.max(acc.enYuksek, p.enYuksek)
      for (const [k, v] of Object.entries(p.turler)) acc.turler[k] = (acc.turler[k] ?? 0) + v
    },
  })
  sc.load(
    veri.map((d, i) => {
      const alt = a.altTur?.(d)
      return {
        type: 'Feature' as const,
        geometry: { type: 'Point' as const, coordinates: a.konum(d) },
        properties: { i, enYuksek: a.oncelik?.(d) ?? 0, turler: alt ? { [alt]: 1 } : {} },
      }
    }),
  )
  return { sc, sonuclar: new Map() }
}

/** Veriyi verilen yakınlıkta kümeler: tek kalanlar ve kümeler.
    `tur` aynı veri dizisi için ayrı dizin anahtarıdır. */
export function kumele<T>(
  tur: string,
  veri: readonly T[],
  zoom: number,
  a: Ayar<T>,
): { tekler: T[]; kumeler: Kume[] } {
  const z = Math.max(0, Math.floor(zoom))
  if (z > a.enCokZoom || veri.length < 2) return { tekler: veri as T[], kumeler: [] }
  let turlere = dizinler.get(veri)
  if (!turlere) {
    turlere = new Map()
    dizinler.set(veri, turlere)
  }
  let dz = turlere.get(tur)
  if (!dz) {
    dz = dizinKur(veri, a)
    turlere.set(tur, dz)
  }
  const onceki = dz.sonuclar.get(z)
  if (onceki) return onceki as { tekler: T[]; kumeler: Kume[] }

  const tekler: T[] = []
  const kumeler: Kume[] = []
  for (const f of dz.sc.getClusters([-180, -85, 180, 85], z)) {
    const p = f.properties as Ozellik & Partial<Supercluster.ClusterProperties>
    if (p.cluster) {
      const [lon, lat] = f.geometry.coordinates
      kumeler.push({
        tur,
        lon,
        lat,
        sayi: p.point_count ?? 0,
        genisleme: Math.min(dz.sc.getClusterExpansionZoom(p.cluster_id!), a.enCokZoom + 1),
        ozet: { enYuksek: p.enYuksek, turler: p.turler },
      })
    } else {
      tekler.push(veri[p.i])
    }
  }
  const sonuc = { tekler, kumeler }
  dz.sonuclar.set(z, sonuc)
  return sonuc
}

/** Küme etiketindeki sayı: 1 240 -> "1,2 B". */
export function kumeSayisi(n: number): string {
  return n >= 1000 ? `${(n / 1000).toFixed(1).replace('.', ',')} B` : String(n)
}
