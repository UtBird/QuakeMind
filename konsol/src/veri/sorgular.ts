import { useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiGet } from './istemci'
import { dogruluk } from '@/lib/bicim'
import type { SorguAraligi } from '@/durum/zamanDurumu'
import type { Gorev } from './gorev'

export type { Ekip } from './gorev'
export { useEkipler } from './gorev'

/* ---------------------------------------------------------------------------
   Ortak çıktı sözleşmesi (CLAUDE.md kural 2):
   (konum, hasar/aciliyet skoru, güven, zaman damgası, kaynak tipi)
   Arayüz modellere değil bu sözleşmeye bağlanır.

   Uçlar henüz bağlanmadı. Bu yüzden sorgular gerçekten istek atar; uç yoksa
   hata döner ve paneller "veri yok" yazar. Uydurma veri üretilmez (kural 1).
--------------------------------------------------------------------------- */

export type KaynakTipi = 'uydu' | 'kamera' | 'metin' | 'sos'

export type HasarNoktasi = {
  id: string
  lon: number
  lat: number
  skor: number
  guven: number
  zaman: number
  kaynak: KaynakTipi
}

export type SosDurumu = 'bekliyor' | 'atandi' | 'kapandi'

/** Aciliyet adı ve rozet tonu: liste, harita ipucu ve panel aynı adı kullanır. */
export const ONCELIK_ADI = { kritik: 'Kritik', yuksek: 'Yüksek', orta: 'Orta' } as const
export const ONCELIK_TON = { kritik: 'crit', yuksek: 'high', orta: 'mid' } as const

/** Sözleşmedeki kaynak tipinin görünen adı. */
export const KAYNAK_ADI = {
  uydu: 'Uydu hasar tespiti',
  sos: 'SOS çağrısı',
  kamera: 'Kamera tespiti',
  metin: 'Metin ihbarı',
} as const

/** Afetzedenin bildirebildiği ihtiyaçlar; sunucudaki `IHTIYACLAR` ile aynı sıra. */
export const IHTIYAC_ADI = {
  su: 'Su',
  gida: 'Gıda',
  barinma: 'Barınma',
  isinma: 'Isınma',
  ilac: 'İlaç, ilk yardım',
  tuvalet: 'Tuvalet, hijyen',
} as const
export type Ihtiyac = keyof typeof IHTIYAC_ADI

export type SosCagrisi = {
  id: string
  lon: number
  lat: number
  oncelik: 'kritik' | 'yuksek' | 'orta'
  durum: SosDurumu
  zaman: number
  mahalle?: string | null
  metin?: string | null
  ekipId?: string | null
  atamaZamani?: number | null
  /* Afetzede ekranından gelen yapılandırılmış bilgi (J-43); eski kayıtlarda yok. */
  kisiSayisi?: number | null
  ihtiyaclar?: Ihtiyac[] | null
  /** "gps": cihaz konumu · "mahalle": mahalle merkezi, yaklaşık konum. */
  konumKaynagi?: 'gps' | 'mahalle' | null
  konumDogrulukM?: number | null
  /** false: afetzede durum seçmeden SOS'a bastı; öncelik "kritik" varsayıldı (J-50). */
  durumSecildi?: boolean | null
  /** Çağrıya giden ekipler, yeniden eskiye (J-54). */
  gorevler?: Gorev[]
  /** Hesap başına tek açık çağrı (J-167 S-2): açıkken yeniden basınca aynı çağrı
      güncellenir. Kaç kez ve en son ne zaman; `zaman` ilk geldiği andır. */
  guncellemeSayisi?: number
  sonGuncelleme?: number | null
  /** Yalnız gönderme yanıtında: bu basış yeni çağrı açmadı, var olanı güncelledi. */
  guncellendi?: boolean
}

/**
 * Afetzede ekranından gelen bilgi, ekip ekranlarında tek biçimde (J-43).
 * `yaklasik` doluysa konum mahalle merkezidir: ekip bunu görmeden gitmemeli.
 */
export function sosEkBilgi(c: SosCagrisi): { kisiIhtiyac: string | null; konum: string | null; yaklasik: boolean } {
  const kisiIhtiyac =
    [
      c.durumSecildi === false ? 'Durum seçilmedi (tek dokunuş SOS)' : null,
      c.kisiSayisi ? `${c.kisiSayisi} kişi` : null,
      c.ihtiyaclar?.length ? c.ihtiyaclar.map((i) => IHTIYAC_ADI[i] ?? i).join(', ') : null,
    ]
      .filter(Boolean)
      .join(' · ') || null
  const yaklasik = c.konumKaynagi === 'mahalle'
  const konum = yaklasik
    ? 'Yaklaşık konum: mahalle merkezi (afetzede konum veremedi)'
    : c.konumKaynagi === 'gps' && c.konumDogrulukM != null
      ? `Cihaz konumu, ${dogruluk(c.konumDogrulukM)}`
      : null
  return { kisiIhtiyac, konum, yaklasik }
}


/** Canlıda sunucu en çok 15 dakika geniş pencere döner (bkz. useSorguAraligi);
    liste burada tam pencereye süzülür. Süzme yalnız dakika değişince yeniden
    koşar, istek atmaz. */
function useTamPencere<T extends { zaman: number }>(kesinBaslangic: number | null) {
  return useCallback(
    (l: T[]) => (kesinBaslangic == null ? l : l.filter((x) => x.zaman >= kesinBaslangic)),
    [kesinBaslangic],
  )
}

export function useHasarNoktalari({ baslangic, bitis, kesinBaslangic }: SorguAraligi) {
  const suz = useTamPencere<HasarNoktasi>(kesinBaslangic)
  return useQuery({
    queryKey: ['hasar', baslangic, bitis ?? 'canli'],
    queryFn: () => apiGet<HasarNoktasi[]>('/api/hasar-noktalari', { baslangic, bitis }),
    select: suz,
  })
}

export function useSosCagrilari({ baslangic, bitis, kesinBaslangic }: SorguAraligi) {
  const suz = useTamPencere<SosCagrisi>(kesinBaslangic)
  return useQuery({
    queryKey: ['sos', baslangic, bitis ?? 'canli'],
    queryFn: () => apiGet<SosCagrisi[]>('/api/sos', { baslangic, bitis }),
    select: suz,
  })
}

/* ---- Isı haritası -------------------------------------------------------
   Izgara sunucuda üretilir; ölçek MUTLAKtır (istek başına maksimuma göre
   normalize edilmez), bu yüzden aynı yer harita kaydırılınca renk
   değiştirmez. İstemci ikinci kez bulanıklaştırma YAPMAZ (MIMARI §5). */

export type IsiIzgarasi = {
  /** [lat, lon, yoğunluk 0-1] */
  points: [number, number, number][]
  bounds: { west: number; south: number; east: number; north: number }
  olcek: { tip: string; referans: number }
  generatedFrom: { totalReports: number; bySource: Record<string, number>; source: string }
}

export function useIsiIzgarasi(
  merkez: { lon: number; lat: number },
  yaricapKm: number,
  { baslangic, bitis }: SorguAraligi,
  kaynak: KaynakTipi,
  acik: boolean,
) {
  // Anahtar kaynakla başlar: canlı akış yalnız değişen kanalı tazeler (J-51).
  return useQuery({
    queryKey: ['isi', kaynak, merkez.lon, merkez.lat, yaricapKm, baslangic, bitis ?? 'canli'],
    enabled: acik,
    queryFn: () =>
      apiGet<IsiIzgarasi>('/api/road_damage/heatmap', {
        latitude: merkez.lat,
        longitude: merkez.lon,
        radiusKm: yaricapKm,
        baslangic,
        bitis,
        kaynak,
      }),
  })
}

/** Bölge özeti: KPI sayıları sunucuda hesaplanır, istemci hazır olanı gösterir. */
export type Ozet = {
  yikikYapi: number
  hasarliYapi: number
  hasarliYol: number
  bekleyenSos: number
  atananSos: number
  kapananSos: number
  /* Ekipler şu anki durumuyla, zaman aralığından bağımsız (J-54). */
  ekipSayisi?: number
  musaitEkip?: number
  gorevdekiEkip?: number
  /** Açık görevlerde sahaya giden toplam kişi. */
  sahadakiKisi?: number
  /** Kanal başına nokta sayısı: ısı panelindeki sayılar buradan gelir. */
  kaynakSayilari: Partial<Record<KaynakTipi, number>>
}

export function useOzet({ baslangic, bitis }: SorguAraligi) {
  return useQuery({
    queryKey: ['ozet', baslangic, bitis ?? 'canli'],
    queryFn: () => apiGet<Ozet>('/api/ozet', { baslangic, bitis }),
  })
}
