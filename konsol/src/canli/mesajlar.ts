/* Tek SSE akışının mesaj tipleri (MIMARI.md §6).
   Sunucu yalnızca DEĞİŞİKLİK olduğunda mesaj gönderir; istemci yoklama yapmaz. */

export type CanliMesaj =
  | {
      tip: 'yeni-sos'
      id: string
      zaman: number
      /* Konsol rollerine tam kayıt gider. Afetzedeye yalnız KENDİ çağrısının
         kimliği ve durumu gider; konum ve öncelik hiç gitmez (J-42). */
      lon?: number
      lat?: number
      oncelik?: string
      mahalle?: string | null
      durum?: 'bekliyor' | 'atandi' | 'kapandi'
    }
  | {
      tip: 'is-durumu'
      isId: string
      /** 'hasar-analizi' | 'simulasyon' (SIMULASYON_SOZLESMESI.md §3) | … */
      isTipi: string
      /** 'iptal' yalnız simülasyonda: tatbikat bitirildi, istemciler normal akışa döner. */
      durum: 'kuyrukta' | 'calisiyor' | 'bitti' | 'hata' | 'iptal'
      /** Hasar analizi YÜZDE gönderiyor (0-100); simülasyon sözleşmesi 0..1
          diyor. Çeviri tek yerde: `CanliSaglayici`. */
      ilerleme?: number
      mesaj?: string
      hata?: string
    }
  /** Simülasyonun bir katmanı çizilmeye hazır (SIMULASYON_SOZLESMESI.md §3).
      Sıra: hasar → kapanma → rota → görev. Arayüz sonucun tamamını beklemez;
      her mesajda koşunun o ana kadarki hâlini ister. */
  | {
      tip: 'simulasyon-katman'
      isId: string
      katman: 'hasar' | 'kapanma' | 'rota' | 'gorev'
      /** Kaç poligon / kenar / rota (bilinmiyorsa gelmez). */
      sayi?: number
    }
  | { tip: 'yeni-analiz'; kaynak: string; isId?: string; bolge?: string; sayi?: number }
  | { tip: 'isi-surumu'; surum: string; bolge?: string }
  /** Konsola ekibin kimliği ve konumu gider. Afetzedeye yalnız KENDİ olayına
      giden ekip için, koordinatsız (J-54): istemci kendi çağrısını yeniden ister. */
  | {
      tip: 'ekip-konumu'
      ekipId?: string
      lon?: number | null
      lat?: number | null
      hedefTur?: 'sos' | 'ihbar'
      hedefId?: string
    }
  /** Sevk görevi açıldı ya da durumu değişti (J-54). */
  | {
      tip: 'gorev'
      id?: string
      zaman: number
      hedefTur: 'sos' | 'ihbar'
      hedefId: string
      ekipId?: string
      durum: 'atandi' | 'yolda' | 'olay-yerinde' | 'tamamlandi' | 'iptal'
      /** Görev bitince olayın yeni durumu: 'kapandi' ya da 'bekliyor'. */
      hedefDurumu?: string | null
    }
  /** Bir hesap açıldı ya da değişti (J-157); yalnız konsol rollerine gider. */
  | { tip: 'hesap'; kullaniciId: string }
  /** Koordinasyonun yayınladığı acil durum bildirimi (herkese gider). */
  | { tip: 'bildirim'; id: string; baslik: string; onem: string; zaman: number; durum?: 'yayinda' | 'kaldirildi' }
  /** Afetzede ihbarı (J-51): yeni ihbar ya da durum değişikliği. Afetzedeye
      yalnız KENDİ ihbarının kimliği, türü ve durumu gider. */
  | {
      tip: 'ihbar'
      id: string
      zaman: number
      tur: 'fotograf' | 'metin' | 'ihtiyac'
      durum: 'yeni' | 'goruldu' | 'kapandi'
      lon?: number
      lat?: number
      etiket?: string | null
      /** İhbar ısı haritasına nokta yazdıysa hangi kanal: 'kamera' | 'metin'. */
      hasarKaynagi?: string | null
    }

export const MESAJ_TIPLERI: CanliMesaj['tip'][] = [
  'yeni-sos',
  'is-durumu',
  'yeni-analiz',
  'isi-surumu',
  'ekip-konumu',
  'bildirim',
  'ihbar',
  'gorev',
  'simulasyon-katman',
  'hesap',
]

/** Mesaj → tazelenecek sorgu anahtarları. Yalnız değişen şey tazelenir: yeni
    SOS'ta dört ısı kanalı değil yalnız SOS kanalı, durum değişikliğinde hiçbiri. */
export function tazelenecekler(m: CanliMesaj): string[][] {
  switch (m.tip) {
    case 'yeni-sos':
      // Konumlu mesaj yeni çağrıdır; konumsuz olan durum değişikliği.
      return m.lon != null ? [['sos'], ['ozet'], ['hasar'], ['isi', 'sos']] : [['sos'], ['ozet']]
    case 'ihbar':
      return m.hasarKaynagi
        ? [['ihbar'], ['hasar'], ['ozet'], ['isi', m.hasarKaynagi]]
        : [['ihbar']]
    case 'is-durumu':
      return [['isler']]
    case 'yeni-analiz':
      // Biten uydu analizi kapanmaları da depoya yazar (J-56 katmanı).
      return [['hasar'], ['ozet'], ['isi', 'uydu'], ['katman', 'kapanmalar']]
    case 'isi-surumu':
      return [['isi']]
    case 'ekip-konumu':
      // Afetzedeye gelen mesajda ekip kimliği yok: kendi çağrısı ya da ihbarı tazelenir.
      return m.ekipId
        ? [['ekipler'], ['aday-ekipler'], ['ekibim']]
        : [[m.hedefTur === 'ihbar' ? 'ihbar' : 'sos']]
    case 'gorev':
      return [
        [m.hedefTur === 'ihbar' ? 'ihbar' : 'sos'],
        ['ekipler'],
        ['aday-ekipler'],
        ['gorevler'],
        ['ekibim'],
        ['ozet'],
      ]
    case 'bildirim':
      return [['bildirimler']]
    case 'hesap':
      return [['kullanicilar'], ['hesap-kayitlari'], ['uye-adaylari']]
    case 'simulasyon-katman':
      // Yalnız o koşunun sonucu; başka hiçbir sorgu etkilenmez. Sunucu
      // katmanları sırayla bitirdiği için sonuç her mesajda bir parça daha
      // dolu gelir (SIMULASYON_SOZLESMESI.md §3).
      return [['simulasyon', 'kosu', m.isId]]
  }
}

/** Akış yeniden bağlanınca bir kez tazelenen bütün anahtarlar: kopukken
    yayınlanan mesajlar sunucuda birikmez. */
export const AKIS_ANAHTARLARI: string[][] = [
  ['sos'],
  ['ozet'],
  ['hasar'],
  ['isi'],
  ['isler'],
  ['ekipler'],
  ['bildirimler'],
  ['ihbar'],
  ['gorevler'],
  ['aday-ekipler'],
  ['ekibim'],
  ['kullanicilar'],
  ['hesap-kayitlari'],
  // Fay, deprem ve toplanma katmanları değişmez; yalnız kapanmalar tazelenir.
  ['katman', 'kapanmalar'],
]
