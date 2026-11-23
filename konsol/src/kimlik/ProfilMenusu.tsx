import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { SignOut, UserGear } from '@phosphor-icons/react'
import { useOturum } from './oturum'
import { ROL_ADI } from './roller'
import { sn } from '@/lib/sinif'

/* ---------------------------------------------------------------------------
   Profil menüsü (J-183): konsol, saha ekibi ve afetzede ekranlarının sağ üst
   köşesinde aynı simge. Tıklayınca kim olduğun, "Hesap ayarları" ve en altta
   "Çıkış yap". Eskiden simgeye tıklamak doğrudan çıkış yapıyordu.
--------------------------------------------------------------------------- */

export function ProfilMenusu({ boyut = 'kucuk' }: { boyut?: 'kucuk' | 'buyuk' }) {
  const { oturum, cikisYap } = useOturum()
  const git = useNavigate()
  const [acik, setAcik] = useState(false)
  const kutu = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!acik) return
    const disari = (e: MouseEvent) => {
      if (!kutu.current?.contains(e.target as Node)) setAcik(false)
    }
    const tus = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setAcik(false)
    }
    document.addEventListener('mousedown', disari)
    document.addEventListener('keydown', tus)
    return () => {
      document.removeEventListener('mousedown', disari)
      document.removeEventListener('keydown', tus)
    }
  }, [acik])

  if (!oturum) return null
  const satir = 'flex w-full items-center gap-2.5 rounded-control px-2.5 py-2 text-left text-body'

  return (
    <div ref={kutu} className="relative shrink-0">
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={acik}
        aria-label={`Hesap menüsü: ${oturum.adSoyad}, ${ROL_ADI[oturum.rol]}`}
        title={`${oturum.adSoyad} · ${ROL_ADI[oturum.rol]}`}
        onClick={() => setAcik((v) => !v)}
        className={sn(
          'grid shrink-0 place-items-center rounded-full bg-accent-deep font-semibold text-ink ring-accent hover:ring-1',
          acik && 'ring-1',
          boyut === 'buyuk' ? 'h-9 w-9 text-small' : 'h-7 w-7 text-micro',
        )}
      >
        {bashar(oturum.adSoyad)}
      </button>
      {acik && (
        <div
          role="menu"
          aria-label="Hesap"
          className="absolute top-full right-0 z-40 mt-1.5 w-64 rounded-panel border border-line-2 bg-panel p-1 shadow-float"
        >
          <div className="border-b border-line px-2.5 pt-1.5 pb-2.5">
            <p className="truncate text-body font-semibold text-ink">{oturum.adSoyad}</p>
            <p className="truncate text-small text-ink-2">{oturum.eposta}</p>
            <p className="mt-1 text-small text-ink-3">
              {ROL_ADI[oturum.rol]}
              {oturum.ortakHesap && ' · ortak örnek hesap'}
            </p>
          </div>
          <Link
            to="/hesap"
            role="menuitem"
            onClick={() => setAcik(false)}
            className={sn(satir, 'mt-1 text-ink hover:bg-hover')}
          >
            <UserGear size={18} className="text-ink-2" aria-hidden />
            Hesap ayarları
          </Link>
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              setAcik(false)
              void cikisYap().then(() => git('/giris', { replace: true }))
            }}
            className={sn(satir, 'text-ink-2 hover:bg-hover hover:text-ink')}
          >
            <SignOut size={18} aria-hidden />
            Çıkış yap
          </button>
        </div>
      )}
    </div>
  )
}

export function bashar(ad?: string): string {
  if (!ad) return '—'
  return ad
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p.charAt(0).toLocaleUpperCase('tr'))
    .join('')
}
