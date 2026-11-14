/** Roller MIMARI.md §9'daki dört rol. Rol yalnızca sunucudan (veritabanından) gelir. */
export const ROLLER = ['afetzede', 'saha', 'koordinator', 'yonetici'] as const
export type Rol = (typeof ROLLER)[number]

export const ROL_ADI: Record<Rol, string> = {
  afetzede: 'Afetzede',
  saha: 'Saha ekibi',
  koordinator: 'Koordinatör',
  yonetici: 'Yönetici',
}

/** Giriş ekranının kapıları (J-156). Kapı rol VERMEZ; sunucu hesabın rolünü
    kapıyla karşılaştırır (kimlik.GIRIS_KAPILARI ile aynı eşleme). */
export const GIRIS_KAPILARI = ['afetzede', 'ekip', 'koordinasyon'] as const
export type GirisKapisi = (typeof GIRIS_KAPILARI)[number]

export function rolunKapisi(rol: Rol): GirisKapisi {
  return rol === 'afetzede' ? 'afetzede' : rol === 'saha' ? 'ekip' : 'koordinasyon'
}

/** Konsolu (harita, analiz) görebilen roller. Afetzede ayrı ve hafif ekrana gider. */
export const KONSOL_ROLLERI: Rol[] = ['saha', 'koordinator', 'yonetici']

/** Rolün açılışta gideceği yer. */
export function varsayilanYol(rol: Rol): string {
  // Saha ekibi sahada telefonla çalışır: açılışta kendi görev ekranı (J-54).
  return rol === 'afetzede' ? '/afetzede' : rol === 'saha' ? '/ekip' : '/konsol/genel'
}

/** Girişten sonra gidilecek yer: geçici şifre varsa önce şifre ekranı (J-157). */
export function acilisYolu(o: Pick<Oturum, 'rol' | 'sifreDegismeli'>): string {
  return o.sifreDegismeli ? '/sifre-degistir' : varsayilanYol(o.rol)
}

export type Oturum = {
  kullaniciId: string
  adSoyad: string
  eposta: string
  rol: Rol
  /** Saha kullanıcısının bağlı olduğu ekip (J-54). Yalnız görünüm içindir;
      yetkiyi her uçta sunucu kontrol eder. */
  ekipId?: string | null
  /** Geçici şifreyle girdi (J-157): kendi şifresini koymadan başka ekrana geçemez.
      Sunucu da korunan her uçta 403 verir; buradaki yönlendirme yalnız görünüm. */
  sifreDegismeli?: boolean
  /** Oturumun kaynağı; bugün tek seçenek imzalı erişim jetonu. */
  kaynak: 'jwt'
}
