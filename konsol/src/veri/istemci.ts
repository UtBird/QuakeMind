import { QueryClient } from '@tanstack/react-query'

/**
 * Sunucu verisi TanStack Query'de tutulur (MIMARI §7).
 * Tazeleme YALNIZ SSE mesajıyla olur: zamanlayıcıyla yoklama kapalıdır (kural 4).
 */
export const sorguIstemcisi = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: Infinity,
      gcTime: 30 * 60_000,
      refetchOnWindowFocus: false,
      refetchOnReconnect: false,
      refetchInterval: false,
      retry: 1,
    },
  },
})

export class ApiHatasi extends Error {
  constructor(
    message: string,
    readonly durum: number,
  ) {
    super(message)
  }
}

/** Erişim jetonunu veren kanca; döngüsel import olmasın diye enjekte edilir. */
let jetonKaynagi: () => string | null = () => null
let jetonYenile: (() => Promise<unknown>) | null = null

export function kimlikBagla(kaynak: () => string | null, yenile: () => Promise<unknown>) {
  jetonKaynagi = kaynak
  jetonYenile = yenile
}

/** Geçerli erişim jetonu. Harita karolarını deck.gl kendi `fetch`'iyle
    indirdiği için başlığı oraya elle geçirmek gerekiyor (bkz. goruntuKatmani). */
export function erisimJetonu(): string | null {
  return jetonKaynagi()
}

function basliklar(ek?: Record<string, string>): Record<string, string> {
  const jeton = jetonKaynagi()
  return { ...(ek ?? {}), ...(jeton ? { authorization: `Bearer ${jeton}` } : {}) }
}

export function apiPost<T>(yol: string, govde: unknown): Promise<T> {
  return apiGonder<T>('POST', yol, govde)
}

export function apiPut<T>(yol: string, govde: unknown): Promise<T> {
  return apiGonder<T>('PUT', yol, govde)
}

export function apiPatch<T>(yol: string, govde: unknown): Promise<T> {
  return apiGonder<T>('PATCH', yol, govde)
}

/** Jeton yenilemesi DENENMEYEN kimlik uçları (J-49). Hesap yönetimi uçları da
    /api/oturum/ altında ama onlar sıradan korunan uçtur: 15 dakika açık kalan
    Kullanıcılar ekranı jeton dolunca yenilenip devam etmeli (J-157). */
const KIMLIK_UCLARI = ['/api/oturum/giris', '/api/oturum/kayit', '/api/oturum/yenile', '/api/oturum/cikis']

async function apiGonder<T>(yontem: 'POST' | 'PUT' | 'PATCH', yol: string, govde: unknown): Promise<T> {
  const gonder = () =>
    fetch(yol, {
      method: yontem,
      credentials: 'same-origin',
      headers: basliklar({ 'content-type': 'application/json' }),
      body: JSON.stringify(govde),
    })
  let y = await gonder()

  // GET'teki gibi: erişim jetonu 15 dakikalık. Sayfayı açık bırakıp sonra
  // yardım çağıran afetzedenin isteği 401 ile düşmesin. Yeniden göndermek
  // güvenli: 401'de sunucu isteği kimlik adımında reddetmiştir, kayıt açmamıştır.
  // Kimlik uçlarında (giriş, kayıt, yenileme, çıkış) DENENMEZ: yenileme isteği
  // 401 alınca kendi kendini beklerdi ve oturumsuz açılış "Yükleniyor…"da
  // takılı kalırdı; yanlış şifreyle giriş de hiç bitmezdi (J-49).
  if (y.status === 401 && jetonYenile && !KIMLIK_UCLARI.includes(yol)) {
    await jetonYenile()
    y = await gonder()
  }

  if (!y.ok) {
    let ayrinti = `${yol} → HTTP ${y.status}`
    try {
      const hata = (await y.json()) as { detail?: string }
      if (hata?.detail) ayrinti = hata.detail
    } catch {
      /* gövdesi JSON değilse durum kodu yeter */
    }
    throw new ApiHatasi(ayrinti, y.status)
  }
  return (await y.json()) as T
}

export async function apiGet<T>(
  yol: string,
  params?: Record<string, string | number | null | undefined>,
): Promise<T> {
  const url = new URL(yol, window.location.origin)
  // Boş değer adrese yazılmaz: "bitis=undefined" sunucuda 422 olur.
  for (const [k, v] of Object.entries(params ?? {})) if (v != null) url.searchParams.set(k, String(v))
  let y = await fetch(url, { credentials: 'same-origin', headers: basliklar() })

  // Erişim jetonu kısa ömürlü: 401 gelirse bir kez yenileyip tekrar dener.
  if (y.status === 401 && jetonYenile) {
    await jetonYenile()
    y = await fetch(url, { credentials: 'same-origin', headers: basliklar() })
  }

  if (!y.ok) {
    // Sunucunun açıklaması varsa o gösterilir (ör. "Hesabın askıya alınmış").
    let ayrinti = `${yol} → HTTP ${y.status}`
    try {
      const hata = (await y.json()) as { detail?: string }
      if (typeof hata?.detail === 'string') ayrinti = hata.detail
    } catch {
      /* gövdesi JSON değilse durum kodu yeter */
    }
    throw new ApiHatasi(ayrinti, y.status)
  }
  return (await y.json()) as T
}

/** Yetki isteyen bir görseli indirir (simülasyonun hasar maskesi gibi).
    `<img src>` kullanılamaz: tarayıcı o istekte Authorization başlığı
    göndermez. Gövde JSON değil, ikili veridir. */
export async function apiGorsel(yol: string): Promise<Blob> {
  const getir = () => fetch(yol, { credentials: 'same-origin', headers: basliklar() })
  let y = await getir()
  if (y.status === 401 && jetonYenile) {
    await jetonYenile()
    y = await getir()
  }
  if (!y.ok) throw new ApiHatasi(`${yol} → HTTP ${y.status}`, y.status)
  return await y.blob()
}
