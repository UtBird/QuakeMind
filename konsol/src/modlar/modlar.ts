import type { KatmanId } from '@/durum/konsolDurumu'
import type { Rol } from '@/kimlik/roller'

/* ---------------------------------------------------------------------------
   Sayfa yok, MOD var (MIMARI §7 · ARAYUZ §8).
   Mod değişince harita yerinde kalır; yalnız paneller ve açık katmanlar değişir.
   Yeni mod eklemek = bu listeye bir satır eklemek.

   `grup`: üst çubukta "ana" modlar sekme, "analiz" modları tek açılır menüde
   (J-56; kullanıcı: "üst menüde bir sürü alan var").
--------------------------------------------------------------------------- */

export const MODLAR = [
  {
    id: 'genel',
    grup: 'ana',
    ad: 'Genel durum',
    ozet: 'Bütün kaynaklardan gelen hasar bilgisi ve afetzede ihbarları tek haritada.',
    katmanlar: ['yapilar', 'yollar', 'hasarliYollar', 'isi', 'depremler', 'ekipler', 'ihbarlar'],
  },
  {
    id: 'sos',
    grup: 'ana',
    ad: 'SOS kuyruğu',
    ozet: 'Ekip bekleyen çağrılar, kime kim gidiyor, ekip gönderme.',
    katmanlar: ['yollar', 'hasarliYollar', 'ekipler', 'toplanma'],
  },
  {
    id: 'ekipler',
    grup: 'ana',
    ad: 'Ekipler',
    ozet: 'Hangi ekip nerede, neye gidiyor, kaç kişiyle; ekip tanımı ve bağlı hesaplar.',
    katmanlar: ['yollar', 'ekipler', 'ihbarlar', 'toplanma'],
  },
  {
    id: 'ihtiyac',
    grup: 'ana',
    ad: 'İhtiyaç talepleri',
    ozet: 'Afetzedelerin su, gıda, barınma gibi ihtiyaç talepleri; nerede ne eksik.',
    katmanlar: ['yollar', 'toplanma', 'ekipler', 'ihbarlar'],
  },
  {
    id: 'bildirim',
    grup: 'ana',
    ad: 'Acil bildirim',
    ozet: 'Afetzede ekranlarına acil durum bildirimi yayınla, yanlış olanı geri çek.',
    katmanlar: ['yollar', 'isi', 'ekipler'],
  },
  {
    id: 'kullanicilar',
    grup: 'ana',
    ad: 'Kullanıcılar',
    ozet: 'Bütün hesaplar: ekip hesabı aç, rol ve ekip ata, askıya al, işlem geçmişi.',
    katmanlar: ['ekipler'],
    // Listeyi sunucu yalnız bu rollere verir; sekme de yalnız onlara görünür.
    roller: ['koordinator', 'yonetici'],
    // Tablo ve düzenleme çekmecesi haritaya sığmaz: harita kurulu kalır,
    // üstünü tam sayfa kaplar (J-157).
    sayfa: true,
  },
  {
    id: 'hasar',
    grup: 'analiz',
    ad: 'Hasar analizi',
    ozet: 'Uydu görüntüsünden yol kapanmalarını çıkaran analizi başlat ve izle.',
    katmanlar: ['analizGoruntusu', 'analizSonucu', 'yollar', 'hasarliYollar'],
  },
  {
    id: 'kamera',
    grup: 'analiz',
    ad: 'Kamera tespiti',
    ozet: 'Afetzedelerin hasar fotoğrafları ve saha fotoğrafında çatlak, yapı hasarı tespiti.',
    katmanlar: ['yollar', 'yapilar', 'isi', 'ihbarlar'],
  },
  {
    id: 'metin',
    grup: 'analiz',
    ad: 'Metin analizi',
    ozet: 'Afetzedelerin yazılı ihbarları; Türkçe metinden kategori, konum ve aciliyet.',
    katmanlar: ['yollar', 'isi', 'ekipler', 'ihbarlar'],
  },
  {
    id: 'risk',
    grup: 'analiz',
    ad: 'Deprem riski',
    ozet: 'Bölge bazlı risk skoru: sismik geçmiş, fay uzaklığı, son hareketlilik.',
    katmanlar: ['yollar', 'depremler', 'faylar'],
  },
  {
    id: 'simulasyon',
    grup: 'analiz',
    ad: 'Simülasyon (tatbikat)',
    ozet: 'Gerçek görüntüde model koşturup rotaları tatbikat olarak dener; gerçek olay değildir.',
    katmanlar: ['yollar', 'simHasar', 'simKapanma', 'simRota', 'simGorev', 'simKamera', 'simMetin'],
  },
  {
    id: 'yol',
    grup: 'analiz',
    ad: 'Yol ve rota',
    ozet: 'Kapalı yollar ve ekiplerin geçebileceği güzergâh.',
    katmanlar: ['yollar', 'hasarliYollar', 'toplanma', 'ekipler'],
  },
] as const satisfies ReadonlyArray<{
  id: string
  grup: 'ana' | 'analiz'
  ad: string
  ozet: string
  katmanlar: readonly KatmanId[]
  /** Yalnız bu rollere görünür (yoksa bütün konsol rollerine). Görünüm
      kilididir; yetkiyi sunucu denetler (CLAUDE.md kural 5). */
  roller?: readonly Rol[]
  /** Sol/sağ panel yerine haritanın üstünü kaplayan tam sayfa. Harita yeniden
      kurulmaz (CLAUDE.md §6), yalnız örtülür. */
  sayfa?: true
}>

export type ModId = (typeof MODLAR)[number]['id']
/** Tam sayfa modlar; sol/sağ panelleri yoktur. */
export type SayfaModu = Extract<(typeof MODLAR)[number], { sayfa: true }>['id']
/** Haritanın iki yanında panel gösteren modlar. */
export type PanelModu = Exclude<ModId, SayfaModu>

export function sayfaModuMu(id: ModId): id is SayfaModu {
  const m = MODLAR.find((x) => x.id === id)
  return !!m && 'sayfa' in m && m.sayfa === true
}

/** Mod bu role sekmede ve komut paletinde gösterilir mi? */
export function modGorunur(m: (typeof MODLAR)[number], rol: Rol | undefined): boolean {
  return !('roller' in m) || (rol !== undefined && (m.roller as readonly Rol[]).includes(rol))
}

export const VARSAYILAN_MOD: ModId = 'genel'

export function modBul(id: string | undefined) {
  return MODLAR.find((m) => m.id === id)
}
