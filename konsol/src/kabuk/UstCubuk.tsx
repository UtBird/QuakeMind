import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, useParams } from 'react-router-dom'
import { CaretDown, ClipboardText, DeviceMobile, MagnifyingGlass } from '@phosphor-icons/react'
import { useOturum } from '@/kimlik/oturum'
import { MODLAR, modGorunur } from '@/modlar/modlar'
import { useZaman } from '@/durum/zamanDurumu'
import { useCanliAkisDurumu } from '@/canli/canliAkis'
import { useKonsol } from '@/durum/konsolDurumu'
import { saat } from '@/lib/bicim'
import { sn } from '@/lib/sinif'
import { Marka } from './Marka'
import { ProfilMenusu } from '@/kimlik/ProfilMenusu'

export function UstCubuk() {
  const { oturum } = useOturum()
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
    <header className="flex h-topbar shrink-0 items-center gap-2.5 border-b border-line bg-panel px-3.5 xl:gap-gutter">
      {/* 1024 px'te üst çubuk 200 px taşıyor, çıkış ve Canlı rozeti ekran dışına
          düşüyordu (17 Kasım). 1280 altında yazılar simgeye iner, sekmeler sıkışır;
          yine sığmazsa yalnız sekmeler kayar, sağdaki denetimler hep görünür. */}
      {/* Logo ana ekrana (genel durum) götürür (J-191). */}
      <Link
        to="/konsol/genel"
        aria-label="Genel duruma dön"
        title="Genel durum"
        className="shrink-0 rounded-control text-ink focus-visible:outline-2 focus-visible:outline-accent"
      >
        <Marka daraltilir />
      </Link>
      <span className="h-5 w-px shrink-0 bg-line-2" />

      {/* Ana modlar sekme, analiz modları tek menüde (J-56): on sekme sığmıyor,
          1366 px'te iki satıra kırılıyordu. */}
      <nav className="flex min-w-0 items-center gap-0.5" aria-label="Çalışma modu">
        {/* Yalnız sekmeler kayar; Analiz menüsü dışarıda, açılır listesi kırpılmasın. */}
        <div className="flex min-w-0 items-center gap-0.5 overflow-x-auto">
        {MODLAR.filter((m) => m.grup === 'ana' && modGorunur(m, oturum?.rol)).map((m) => (
          <NavLink
            key={m.id}
            to={`/konsol/${m.id}`}
            title={m.ozet}
            className={({ isActive }) =>
              sn(
                'shrink-0 rounded-control px-2 py-1.5 text-body whitespace-nowrap transition-colors duration-150 ease-out-qm xl:px-2.5',
                isActive ? 'bg-raised text-ink' : 'text-ink-2 hover:bg-hover hover:text-ink',
              )
            }
          >
            {m.ad}
          </NavLink>
        ))}
        </div>
        <AnalizMenusu />
      </nav>

      <span className="flex-1" />

      <button
        type="button"
        onClick={() => komutPaleti(true)}
        aria-label="Ara veya komut ver (Ctrl K)"
        title="Ara veya komut ver (Ctrl K)"
        className="flex shrink-0 items-center gap-2 rounded-control border border-line-2 px-2.5 py-1.5 text-small whitespace-nowrap text-ink-2 hover:bg-hover hover:text-ink"
      >
        <MagnifyingGlass size={14} aria-hidden className="xl:hidden" />
        <span className="hidden xl:inline">Ara veya komut ver</span>
        <kbd className="hidden rounded-badge border border-line-2 bg-sunken px-1 py-0.5 font-mono text-micro text-ink-3 xl:inline">
          Ctrl K
        </kbd>
      </button>

      {oturum?.rol === 'saha' && (
        <Link
          to="/ekip"
          title="Ekibinin görevi: yola çıktık, vardık, işimiz bitti"
          aria-label="Görev ekranı"
          className="flex shrink-0 items-center gap-1.5 rounded-control border border-line-2 px-2.5 py-1.5 text-small text-ink-2 hover:bg-hover hover:text-ink whitespace-nowrap"
        >
          <ClipboardText size={14} aria-hidden className="xl:hidden" />
          <span className="hidden xl:inline">Görev ekranı</span>
        </Link>
      )}

      {onizleyebilir && (
        <Link
          to="/afetzede"
          title="Afetzedenin telefonunda gördüğü ekran: yardım çağrısı, çağrılar, toplanma alanı"
          aria-label="Afetzede ekranı"
          className="flex shrink-0 items-center gap-1.5 rounded-control border border-line-2 px-2.5 py-1.5 text-small text-ink-2 hover:bg-hover hover:text-ink whitespace-nowrap"
        >
          <DeviceMobile size={14} aria-hidden className="xl:hidden" />
          <span className="hidden xl:inline">Afetzede ekranı</span>
        </Link>
      )}

      {/* Canlı / Geçmiş rozeti — ARAYUZ §10 */}
      <span className="flex shrink-0 items-center gap-2 text-small whitespace-nowrap text-ink-2" title={baglantiMetni}>
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
          className="shrink-0 rounded-control border border-line-2 px-2.5 py-1.5 text-small text-ink-2 hover:bg-hover hover:text-ink whitespace-nowrap"
        >
          Canlıya dön
        </button>
      )}

      {/* Profil menüsü (J-183): hesap ayarları ve çıkış. */}
      <ProfilMenusu />
    </header>
  )
}

/** Analiz modları: tek düğme, açılınca her modun adı ve ne işe yaradığı. */
function AnalizMenusu() {
  const { oturum } = useOturum()
  const [acik, setAcik] = useState(false)
  const kutu = useRef<HTMLDivElement>(null)
  const { mod } = useParams()
  const modlar = MODLAR.filter((m) => m.grup === 'analiz' && modGorunur(m, oturum?.rol))
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
    <div ref={kutu} className="relative shrink-0">
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

