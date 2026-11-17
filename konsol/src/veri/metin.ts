import type { Ihtiyac } from './sorgular'
import type { Ihbar } from './ihbar'

/* ---------------------------------------------------------------------------
   Metin analizinin ortak parçaları (J-170). Sunucu: QuakeMindBackend/metin_analizi.

   Konsoldaki deneme analizi (/api/nlp/analyze) ve afetzedenin yazılı ihbarı
   (/api/afetzede/metin-analiz) aynı çözümleyiciden geçer; ekranlar bu dosyadaki
   tiplerle ikisini aynı biçimde gösterir. Aralıklar metnin karakter
   konumudur (`metin.slice(bas, son)`), metni vurgulamak için.

   J-170'ten önce yazılmış ihbarlarda bu alanların hiçbiri yoktur: hepsi
   isteğe bağlı okunur.
--------------------------------------------------------------------------- */

export type Aralik = { bas: number; son: number; metin: string }

/** Adres hangi incelikte bulundu. Belirsizlik sunucuda düzeyden gelir. */
export type KonumDuzeyi = 'sokak' | 'mahalle' | 'koy' | 'kasaba' | 'sehir' | 'ilce' | 'il'

export type AdresEslesmesi = Aralik & { tur: string; bulanik?: boolean }
export type KisiBilgisi = Aralik & { sayi: number; ne: string }
export type IhtiyacBilgisi = Aralik & { ihtiyac: Ihtiyac }
export type SinyalBilgisi = Aralik & { sinyal: string; ad: string }
export type KategoriUyarisi = { onerilen: string; metin: string }
export type AdresAdayi = { konumMetin: string; konum: [number, number]; duzey: string }

/** Düzeyin ekipçe okunan adı. */
export const DUZEY_ADI: Record<KonumDuzeyi, string> = {
  sokak: 'Sokak',
  mahalle: 'Mahalle',
  koy: 'Köy',
  kasaba: 'Kasaba',
  sehir: 'Şehir',
  ilce: 'İlçe',
  il: 'İl',
}

/** Ekip bu konuma doğrudan gidebilir mi? Sokak ve mahalle evet; ilçe ve il
    yalnız bölgeyi söyler (ilçe merkezi olayın yeri değildir). */
export function konumYeterli(d: KonumDuzeyi | null | undefined): boolean {
  return d === 'sokak' || d === 'mahalle' || d === 'koy'
}

/** "±800 m", "±5 km". */
export function belirsizlikMetni(m: number | null | undefined): string | null {
  if (m == null) return null
  return m >= 1000 ? `±${(m / 1000).toLocaleString('tr-TR', { maximumFractionDigits: 1 })} km` : `±${Math.round(m)} m`
}

export const KATEGORI_KAYNAGI: Record<string, string> = {
  model: 'model',
  anahtar_sozcuk: 'anahtar sözcük kuralı',
  belirsiz: 'model kararsız',
  kisa_metin: 'metin çok kısa',
}

const DUZEY_ACIKLAMASI: Record<KonumDuzeyi, string> = {
  sokak: 'Nokta sokağın orta yeridir; bina numarası çözülmez.',
  mahalle: 'Nokta mahallenin merkezidir; olay mahallenin herhangi bir yerinde olabilir.',
  koy: 'Nokta köyün merkezidir.',
  kasaba: 'Nokta kasabanın merkezidir.',
  sehir: 'Nokta şehrin merkezidir; olayın yeri değildir.',
  ilce: 'Yalnız ilçe bulundu: nokta ilçe merkezidir, olayın yeri değildir.',
  il: 'Yalnız il bulundu: nokta il merkezidir, olayın yeri değildir.',
}

export function duzeyAciklamasi(d: KonumDuzeyi | null | undefined): string | null {
  return d ? DUZEY_ACIKLAMASI[d] : null
}

/** Haritadaki belirsizlik çemberi için (bkz. harita/katmanlar.ts). */
export type BelirsizlikCemberi = {
  lon: number
  lat: number
  yaricapM: number
  baslik: string
  aciklama: string
  nokta?: boolean
}

/** Seçili ihbarın konumu ne kadar sapabilir? Bilinmiyorsa null (çember
    uydurulmaz: afetzedenin seçtiği mahalle merkezinin payı bilinmez). */
export function ihbarBelirsizligi(i: Ihbar): BelirsizlikCemberi | null {
  if (i.konumKaynagi === 'metin' && i.analiz?.belirsizlikM) {
    const a = i.analiz
    return {
      lon: i.lon,
      lat: i.lat,
      yaricapM: a.belirsizlikM!,
      baslik: `Metindeki adres · ${belirsizlikMetni(a.belirsizlikM)}`,
      aciklama: [a.konumMetin, duzeyAciklamasi(a.konumDuzeyi)].filter(Boolean).join(' · '),
    }
  }
  if (i.konumKaynagi === 'gps' && i.konumDogrulukM) {
    return {
      lon: i.lon,
      lat: i.lat,
      yaricapM: i.konumDogrulukM,
      baslik: `Cihaz konumu · ${belirsizlikMetni(i.konumDogrulukM)}`,
      aciklama: 'Telefonun bildirdiği konum doğruluğu.',
    }
  }
  return null
}
