import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useKonsol } from '@/durum/konsolDurumu'
import { useZaman } from '@/durum/zamanDurumu'
import { MODLAR, modGorunur } from '@/modlar/modlar'
import { useOturum } from '@/kimlik/oturum'
import { Micro } from './parcalar'
import { sn } from '@/lib/sinif'

/** Ctrl K — arama ve komut. Şimdilik mod ve zaman komutları; veri uçları
    bağlanınca çağrı/mahalle araması aynı listeye eklenecek. */
export function KomutPaleti() {
  const acik = useKonsol((d) => d.komutPaletiAcik)
  const komutPaleti = useKonsol((d) => d.komutPaleti)
  const git = useNavigate()
  const rol = useOturum().oturum?.rol
  const [arama, setArama] = useState('')
  const [secili, setSecili] = useState(0)

  const komutlar = useMemo(() => {
    const hepsi = [
      ...MODLAR.filter((m) => modGorunur(m, rol)).map((m) => ({
        grup: 'Mod',
        etiket: m.ad,
        ipucu: m.ozet,
        calistir: () => git(`/konsol/${m.id}`),
      })),
      {
        grup: 'Zaman',
        etiket: 'Canlıya dön',
        ipucu: 'Pencereyi şimdiye kilitle',
        calistir: () => useZaman.getState().canliyaDon(),
      },
      {
        grup: 'Zaman',
        etiket: 'Son 24 saat',
        ipucu: 'Geçmiş moduna geç',
        calistir: () => useZaman.getState().pencereSec('24s'),
      },
    ]
    const q = arama.trim().toLocaleLowerCase('tr')
    return q ? hepsi.filter((k) => k.etiket.toLocaleLowerCase('tr').includes(q)) : hepsi
  }, [arama, git, rol])

  useEffect(() => {
    function tus(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        komutPaleti(!useKonsol.getState().komutPaletiAcik)
      }
      if (e.key === 'Escape') komutPaleti(false)
    }
    window.addEventListener('keydown', tus)
    return () => window.removeEventListener('keydown', tus)
  }, [komutPaleti])

  useEffect(() => {
    if (acik) {
      setArama('')
      setSecili(0)
    }
  }, [acik])

  if (!acik) return null

  return (
    <div
      className="fixed inset-0 z-20 grid justify-center bg-ground/70 pt-palette-top"
      onClick={(e) => e.target === e.currentTarget && komutPaleti(false)}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Komut paleti"
        className="h-max w-palette max-w-full overflow-hidden rounded-panel border border-line-2 bg-panel shadow-float"
      >
        <input
          autoFocus
          value={arama}
          onChange={(e) => setArama(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'ArrowDown') setSecili((i) => Math.min(komutlar.length - 1, i + 1))
            if (e.key === 'ArrowUp') setSecili((i) => Math.max(0, i - 1))
            if (e.key === 'Enter' && komutlar[secili]) {
              komutlar[secili].calistir()
              komutPaleti(false)
            }
          }}
          placeholder="Mod, zaman aralığı veya komut…"
          className="w-full border-b border-line bg-transparent px-4 py-3.5 text-subtitle text-ink outline-none"
        />
        <div className="max-h-80 overflow-auto p-1.5">
          {komutlar.length === 0 && <p className="px-2.5 py-2 text-small text-ink-3">Sonuç yok.</p>}
          {komutlar.map((k, i) => (
            <button
              key={k.grup + k.etiket}
              type="button"
              onClick={() => {
                k.calistir()
                komutPaleti(false)
              }}
              onMouseEnter={() => setSecili(i)}
              className={sn(
                'flex w-full items-center gap-2.5 rounded-control px-2.5 py-2 text-left text-body',
                i === secili ? 'bg-raised text-ink' : 'text-ink-2',
              )}
            >
              <span className="text-ink">{k.etiket}</span>
              <span className="text-small text-ink-3">{k.ipucu}</span>
              <span className="ml-auto">
                <Micro>{k.grup}</Micro>
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
