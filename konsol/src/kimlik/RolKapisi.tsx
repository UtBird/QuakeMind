import { Navigate, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'
import { useOturum } from './oturum'
import { varsayilanYol, type Rol } from './roller'

/**
 * Rol tabanlı yönlendirme.
 *
 * UYARI: Buradaki koruma yalnız GÖRÜNÜMdür, güvenlik değildir (CLAUDE.md kural 5).
 * Yetkiyi her uç noktada sunucu kontrol eder; bu bileşen sadece kullanıcıyı
 * göremeyeceği ekrana göndermemek içindir.
 */
export function RolKapisi({ izinli, children }: { izinli: Rol[]; children: ReactNode }) {
  const { oturum, yukleniyor } = useOturum()
  const konum = useLocation()

  if (yukleniyor) return <Bekleme />
  if (!oturum) return <Navigate to="/giris" replace state={{ nereden: konum.pathname }} />
  // Geçici şifreyle giren önce kendi şifresini koyar (J-157); sunucu da öbür
  // uçları 403 ile kapatır.
  if (oturum.sifreDegismeli) return <Navigate to="/sifre-degistir" replace />
  if (!izinli.includes(oturum.rol)) return <Navigate to={varsayilanYol(oturum.rol)} replace />
  return <>{children}</>
}

export function Bekleme() {
  return (
    <div className="grid h-full place-items-center bg-ground text-small text-ink-3">
      Yükleniyor…
    </div>
  )
}
