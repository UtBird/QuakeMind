import { apiPost } from '@/veri/istemci'
import type { GirisKapisi, Oturum, Rol } from './roller'

/* ---------------------------------------------------------------------------
   Gerçek kimlik akışı (backend: /api/oturum/*).

   · Erişim jetonu kısa ömürlü ve yalnız BELLEKTE durur; localStorage'a yazılmaz.
   · Yenileme jetonu httpOnly çerezde; JavaScript göremez, biz de tutmayız.
   · Sayfa yenilendiğinde oturum /yenile ile geri alınır.
   · Rol istemciden gönderilmez, sunucudan gelir (CLAUDE.md kural 5).
--------------------------------------------------------------------------- */

type SunucuKullanici = {
  id: string
  eposta: string
  adSoyad: string
  rol: Rol
  birim?: string | null
  sehir?: string | null
  ekipId?: string | null
  sifreDegismeli?: boolean
}

type OturumYaniti = { erisimJetonu: string; kullanici: SunucuKullanici }

let erisimJetonu: string | null = null

export function jetonAl(): string | null {
  return erisimJetonu
}

function jetonYaz(jeton: string | null) {
  erisimJetonu = jeton
}

function oturumaCevir(y: OturumYaniti): Oturum {
  return {
    kullaniciId: y.kullanici.id,
    adSoyad: y.kullanici.adSoyad,
    eposta: y.kullanici.eposta,
    rol: y.kullanici.rol,
    ekipId: y.kullanici.ekipId ?? null,
    sifreDegismeli: !!y.kullanici.sifreDegismeli,
    kaynak: 'jwt',
  }
}

/** `kapi` ROL DEĞİLDİR: giriş ekranında seçilen kapı. Sunucu hesabın
    gerçek rolüyle karşılaştırır, uymazsa doğru kapıyı söyleyip reddeder (J-156). */
export async function girisYap(eposta: string, sifre: string, kapi?: GirisKapisi): Promise<Oturum> {
  const yanit = await apiPost<OturumYaniti>('/api/oturum/giris', { eposta, sifre, kapi })
  jetonYaz(yanit.erisimJetonu)
  return oturumaCevir(yanit)
}

export async function kayitOl(eposta: string, adSoyad: string, sifre: string): Promise<Oturum> {
  // Rol alanı gönderilmiyor: yeni hesap her zaman afetzede olarak açılır.
  const yanit = await apiPost<OturumYaniti>('/api/oturum/kayit', { eposta, adSoyad, sifre })
  jetonYaz(yanit.erisimJetonu)
  return oturumaCevir(yanit)
}

/** Kişinin kendi şifresini değiştirmesi (J-157). Sunucu bütün eski oturumları
    düşürür ve bu cihaza yeni oturum verir; yeni erişim jetonu buradan gelir. */
export async function sifreDegistir(eskiSifre: string, yeniSifre: string): Promise<Oturum> {
  const yanit = await apiPost<OturumYaniti>('/api/oturum/sifre', { eskiSifre, yeniSifre })
  jetonYaz(yanit.erisimJetonu)
  return oturumaCevir(yanit)
}

/** Açılışta ve jeton süresi dolunca: httpOnly çerezden yeni erişim jetonu.

    Sunucu her yenilemede jetonu döndürüyor (eskisini iptal ediyor); bu yüzden
    aynı anda iki yenileme isteği gitmemeli — ikincisi iptal edilmiş jetonu
    kullanır ve oturumu düşürür. Uçuştaki istek varsa aynı söz paylaşılır. */
let ucustakiYenileme: Promise<Oturum | null> | null = null

export function oturumYenile(): Promise<Oturum | null> {
  if (ucustakiYenileme) return ucustakiYenileme

  ucustakiYenileme = (async () => {
    try {
      const yanit = await apiPost<OturumYaniti>('/api/oturum/yenile', {})
      jetonYaz(yanit.erisimJetonu)
      return oturumaCevir(yanit)
    } catch {
      jetonYaz(null)
      return null
    } finally {
      // Sonraki yenileme yeni bir istek açsın.
      setTimeout(() => {
        ucustakiYenileme = null
      }, 0)
    }
  })()

  return ucustakiYenileme
}

export async function cikisYap(): Promise<void> {
  try {
    await apiPost('/api/oturum/cikis', {})
  } finally {
    jetonYaz(null)
  }
}
