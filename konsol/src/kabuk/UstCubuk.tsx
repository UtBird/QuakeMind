import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, useNavigate, useParams } from 'react-router-dom'
import { CaretDown } from '@phosphor-icons/react'
import { useOturum } from '@/kimlik/oturum'
import { ROL_ADI } from '@/kimlik/roller'
import { MODLAR, modGorunur } from '@/modlar/modlar'
import { useZaman } from '@/durum/zamanDurumu'
import { useCanliAkisDurumu } from '@/canli/canliAkis'
import { useKonsol } from '@/durum/konsolDurumu'
import { saat } from '@/lib/bicim'
import { sn } from '@/lib/sinif'
import { Marka } from './Marka'

export function UstCubuk() {
  const { oturum, cikisYap } = useOturum()
  const git = useNavigate()
  const canli = useZaman((d) => d.canli)
  const bitis = useZaman((d) => (d.canli ? d.simdi : d.bitis))
  const canliyaDon = useZaman((d) => d.canliyaDon)
  const akis = useCanliAkisDurumu((d) => d.durum)
  const komutPaleti = useKonsol((d) => d.komutPaleti)
  // Afetzede ekranını önizleyebilen roller (App.tsx'teki /afetzede kapısıyla aynı).
  const onizleyebilir = oturum?.rol === 'koordinator' || oturum?.rol === 'yonetici'

  const baglantiMetni =
    akis === 'bagli'
      ? 'Canlı akış bağlı'
      : akis === 'baglaniyor'
        ? 'Akışa bağlanılıyor'
        : 'Canlı akış bağlı değil'

  return (
    <header className="flex h-topbar shrink-0 items-center gap-gutter border-b border-line bg-panel px-3.5">
      <Marka />
      <span className="h-5 w-px bg-line-2" />

      {/* Ana modlar sekme, analiz modları tek menüde (J-56): on sekme sığmıyor,
          1366 px'te iki satıra kırılıyordu. */}
      <nav className="flex items-center gap-0.5" aria-label="Çalışma modu">
        {MODLAR.filter((m) => m.grup === 'ana' && modGorunur(m, oturum?.rol)).map((m) => (
          <NavLink
            key={m.id}
            to={`/konsol/${m.id}`}
            title={m.ozet}
            className={({ isActive }) =>
              sn(
                'rounded-control px-2.5 py-1.5 text-body whitespace-nowrap transition-colors duration-150 ease-out-qm',
                isActive ? 'bg-raised text-ink' : 'text-ink-2 hover:bg-hover hover:text-ink',
              )
            }
          >
            {m.ad}
          </NavLink>
        ))}
        <AnalizMenusu />
      </nav>

      <span className="flex-1" />

      <button
        type="button"
        onClick={() => komutPaleti(true)}
        className="flex items-center gap-2 rounded-control border border-line-2 px-2.5 py-1.5 text-small text-ink-2 hover:bg-hover hover:text-ink"
      >
        Ara veya komut ver
        <kbd className="rounded-badge border border-line-2 bg-sunken px-1 py-0.5 font-mono text-micro text-ink-3">
          Ctrl K
        </kbd>
      </button>

      {oturum?.rol === 'saha' && (
        <Link
          to="/ekip"
          title="Ekibinin görevi: yola çıktık, vardık, işimiz bitti"
          className="rounded-control border border-line-2 px-2.5 py-1.5 text-small text-ink-2 hover:bg-hover hover:text-ink"
        >
          Görev ekranı
        </Link>
      )}

      {onizleyebilir && (
        <Link
          to="/afetzede"
          title="Afetzedenin telefonunda gördüğü ekran: yardım çağrısı, çağrılar, toplanma alanı"
          className="rounded-control border border-line-2 px-2.5 py-1.5 text-small text-ink-2 hover:bg-hover hover:text-ink"
        >
          Afetzede ekranı
        </Link>
      )}

      {/* Canlı / Geçmiş rozeti — ARAYUZ §10 */}
      <span className="flex items-center gap-2 text-small text-ink-2" title={baglantiMetni}>
        <span
          aria-hidden
          className={sn(
            'h-1.5 w-1.5 rounded-full',
            canli && akis === 'bagli' ? 'bg-ok' : canli ? 'bg-mid' : 'bg-ink-3',
          )}
        />
        {canli ? 'Canlı' : 'Geçmiş'}
        <span className="font-mono text-small text-ink-3">{saat(bitis)}</span>
      </span>

      {!canli && (
        <button
          type="button"
          onClick={canliyaDon}
          className="rounded-control border border-line-2 px-2.5 py-1.5 text-small text-ink-2 hover:bg-hover hover:text-ink"
        >
          Canlıya dön
        </button>
      )}

      <button
        type="button"
        onClick={() => {
          void cikisYap().then(() => git('/giris', { replace: true }))
        }}
        title={oturum ? `${oturum.adSoyad} · ${ROL_ADI[oturum.rol]} — çıkış yap` : 'Çıkış yap'}
        className="grid h-6 w-6 place-items-center rounded-full bg-accent-deep text-micro text-ink"
      >
        {bashar(oturum?.adSoyad)}
      </button>
    </header>
  )
}

/** Analiz modları: tek düğme, açılınca her modun adı ve ne işe yaradığı. */
function AnalizMenusu() {
  const [acik, setAcik] = useState(false)
  const kutu = useRef<HTMLDivElement>(null)
  const { mod } = useParams()
  const modlar = MODLAR.filter((m) => m.grup === 'analiz')
  const secili = modlar.find((m) => m.id === mod)

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

  return (
    <div ref={kutu} className="relative">
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={acik}
        onClick={() => setAcik((v) => !v)}
        className={sn(
          'flex items-center gap-1.5 rounded-control px-2.5 py-1.5 text-body whitespace-nowrap transition-colors duration-150 ease-out-qm',
          secili ? 'bg-raised text-ink' : 'text-ink-2 hover:bg-hover hover:text-ink',
        )}
      >
        {secili ? `Analiz · ${secili.ad}` : 'Analiz'}
        <CaretDown size={12} className={sn(acik && 'rotate-180')} aria-hidden />
      </button>
      {acik && (
        <div
          role="menu"
          aria-label="Analiz modları"
          className="absolute top-full left-0 z-30 mt-1.5 w-80 rounded-panel border border-line-2 bg-panel p-1 shadow-float"
        >
          {modlar.map((m) => (
            <NavLink
              key={m.id}
              to={`/konsol/${m.id}`}
              role="menuitem"
              onClick={() => setAcik(false)}
              className={({ isActive }) =>
                sn('block rounded-control px-2.5 py-2', isActive ? 'bg-raised' : 'hover:bg-hover')
              }
            >
              <span className="block text-body text-ink">{m.ad}</span>
              <span className="block text-small text-ink-3">{m.ozet}</span>
            </NavLink>
          ))}
        </div>
      )}
    </div>
  )
}

function bashar(ad?: string): string {
  if (!ad) return '—'
  return ad
    .split(' ')
    .slice(0, 2)
    .map((p) => p.charAt(0).toLocaleUpperCase('tr'))
    .join('')
}
