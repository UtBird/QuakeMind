import { Crosshair } from '@phosphor-icons/react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { HaritaKabugu, useHarita } from '@/harita/HaritaKabugu'
import { useAltlikGirdisi } from '@/harita/altlikGorunumu'
import type { SosCagrisi } from '@/veri/sorgular'
import { afetzedeIpucu, afetzedeKatmanlari, type HaritaKonumu } from './haritaKatmanlari'
import { CEVRE_YARICAP_KM, useCevre, type YakinYer } from './veri'

/* ---------------------------------------------------------------------------
   Afetzede haritası (J-50): "Nereye gidebilirim?" kartının yanında, küçük.
   Tembel yüklenir; SOS ve liste harita motoru inmeden çalışır (MIMARI §7).
   Konsolun harita kabuğunu ve kendi altlığımızı kullanır; dış karo servisi
   yok (ARAYUZ §11).
--------------------------------------------------------------------------- */

export type AfetzedeHaritasiProps = {
  konum: HaritaKonumu | null
  /** Seçili türün yerleri (sunucudan, uzaklığa göre). */
  yerler: YakinYer[]
  secili: YakinYer | null
  sec: (y: YakinYer) => void
  cagrilar: SosCagrisi[]
  rota: [number, number][] | null
}

export default function AfetzedeHaritasi(p: AfetzedeHaritasiProps) {
  const baslangic = p.konum ? { lon: p.konum.lon, lat: p.konum.lat, zoom: 15 } : undefined
  // Çevredeki tehlike (J-180) varsayılan açık; kişi haritayı sadeleştirmek
  // isterse lejanttan kapatır.
  const [tehlike, setTehlike] = useState(true)
  const q = { ...p, tehlike, setTehlike }
  return (
    <div className="relative h-full w-full">
      {/* isolate: harita kendi katman bağlamında kalır. Yoksa deck.gl tuvali
          (z-index'li) "Konumuma dön" düğmesinin üstüne boyanıyor, sokak adları
          düğmeyi örtüyordu (J-51, kullanıcı). */}
      <HaritaKabugu className="absolute inset-0 isolate" ipucu={afetzedeIpucu} baslangic={baslangic}>
        <Kopru {...q} />
        <Ustyazi {...q} />
      </HaritaKabugu>
    </div>
  )
}

type IcProps = AfetzedeHaritasiProps & { tehlike: boolean; setTehlike: (t: boolean) => void }

/** Veri → katmanlar; seçim ve konum değişince harita oraya uçar. */
function Kopru(p: IcProps) {
  const { hazir, katmanlariYaz, tiklamaYaz, ucus, haritaAl } = useHarita()
  const { altlik, altlikYapiGorunur, bolgeAdlari, adSeviyesi } = useAltlikGirdisi()
  const cevre = useCevre(p.konum)

  const katmanlar = useMemo(
    () =>
      afetzedeKatmanlari({
        altlik,
        altlikYapiGorunur,
        bolgeAdlari,
        adSeviyesi,
        yerler: p.yerler,
        secili: p.secili,
        konum: p.konum,
        cagrilar: p.cagrilar,
        rota: p.rota,
        cevre: p.tehlike ? (cevre.data ?? null) : null,
      }),
    [altlik, altlikYapiGorunur, bolgeAdlari, adSeviyesi, p.yerler, p.secili, p.konum, p.cagrilar, p.rota, p.tehlike, cevre.data],
  )

  useEffect(() => {
    if (hazir) katmanlariYaz(katmanlar)
  }, [hazir, katmanlar, katmanlariYaz])

  // Haritada bir yere tıklanınca seçilir (liste de o yere geçer).
  const sec = useRef(p.sec)
  sec.current = p.sec
  useEffect(() => {
    if (!hazir) return
    tiklamaYaz((bilgi) => {
      if (bilgi.layer?.id === 'yerler' && bilgi.object) sec.current(bilgi.object as YakinYer)
    })
  }, [hazir, tiklamaYaz])

  // Konum ilk kez gelince ya da değişince (mahalle seçimi) oraya git; her
  // doğruluk güncellemesinde uçmasın.
  const konumAnahtari = p.konum ? `${p.konum.lon.toFixed(4)},${p.konum.lat.toFixed(4)}` : null
  useEffect(() => {
    if (hazir && p.konum) ucus(p.konum.lon, p.konum.lat, 15)
  }, [hazir, konumAnahtari])

  // Listeden seçilen yere git; rota gelince bütün rotayı sığdır (J-44).
  // Rota önbellekteyse doğrudan sığdırılır, önce yere uçup sonra geri
  // dönmez.
  const rota = p.rota
  useEffect(() => {
    if (hazir && p.secili && !rota) ucus(p.secili.lon, p.secili.lat, 16)
  }, [hazir, p.secili?.id])
  const rotaAnahtari = rota && rota.length > 1 ? `${rota.length}:${rota[0]}:${rota[rota.length - 1]}` : null
  useEffect(() => {
    const harita = haritaAl()
    if (!hazir || !harita || !rota || rota.length < 2) return
    let [w, s, e, n] = [rota[0][0], rota[0][1], rota[0][0], rota[0][1]]
    for (const [x, y] of rota) {
      w = Math.min(w, x)
      e = Math.max(e, x)
      s = Math.min(s, y)
      n = Math.max(n, y)
    }
    const azalt = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    harita.fitBounds(
      [
        [w, s],
        [e, n],
      ],
      { padding: 40, maxZoom: 17, duration: azalt ? 0 : 900 },
    )
  }, [hazir, rotaAnahtari])

  return null
}

/** Harita üstü: konuma dön, tehlike lejantı ve kaynak künyesi (ARAYUZ §11). */
function Ustyazi(p: IcProps) {
  const { ucus } = useHarita()
  const cevre = useCevre(p.konum)
  const c = cevre.data
  const { gorunen, katalog } = useAltlikGirdisi()
  const kaynak = gorunen[0]?.kaynak ?? katalog.data?.[0]?.kaynak
  const k = p.konum
  const kapsamda =
    !k ||
    !katalog.data ||
    katalog.data.some((b) => k.lon >= b.kutu[0] && k.lon <= b.kutu[2] && k.lat >= b.kutu[1] && k.lat <= b.kutu[3])

  return (
    <>
      {k && (
        <button
          type="button"
          onClick={() => ucus(k.lon, k.lat, 15)}
          className="absolute top-2 right-2 z-10 flex h-9 items-center gap-1.5 rounded-control border border-line-2 bg-panel px-2.5 text-body text-ink shadow-float hover:bg-hover"
        >
          <Crosshair size={16} className="text-accent" aria-hidden />
          {k.kaynak === 'gps' ? 'Konumuma dön' : 'Mahalleme dön'}
        </button>
      )}
      {k && (
        // Tek satırlık lejant: küçük haritayı kapatmasın. Ayrıntı üzerine gelince.
        <label
          title={c ? `${c.kaynak.kapaliYollar}
${c.kaynak.hasarBolgeleri}
${c.kaynak.uyari}` : undefined}
          className="absolute top-2 left-2 z-10 flex h-9 cursor-pointer items-center gap-2 rounded-control border border-line-2 bg-panel px-2.5 text-small text-ink-2 shadow-float"
        >
          <input type="checkbox" checked={p.tehlike} onChange={(e) => p.setTehlike(e.target.checked)} aria-label="Çevremdeki tehlikeyi göster" />
          {!p.tehlike ? (
            <span className="text-ink">Tehlike</span>
          ) : cevre.isError ? (
            'Tehlike bilgisi alınamadı'
          ) : c && c.kapaliYollar.length + c.hasarBolgeleri.length === 0 ? (
            `${CEVRE_YARICAP_KM} km içinde bilinen tehlike yok`
          ) : (
            <>
              <span className="flex items-center gap-1 whitespace-nowrap">
                <span aria-hidden className="h-1 w-3.5 rounded-badge bg-crit" />
                Kapalı yol{c ? ` ${c.kapaliYollar.length}` : ''}
              </span>
              <span className="flex items-center gap-1 whitespace-nowrap">
                <span aria-hidden className="h-3 w-3 rounded-badge border border-high bg-high/40" />
                Hasar{c ? ` ${c.hasarBolgeleri.length}` : ''}
              </span>
            </>
          )}
        </label>
      )}
      <p className="pointer-events-none absolute bottom-0 left-0 z-10 m-2 max-w-full rounded-control border border-line-2 bg-panel px-2.5 py-1 text-small text-ink-2 shadow-float">
        {kaynak ? `${kaynak.atif} (${kaynak.lisans})` : 'Altlık yükleniyor'}
        {!kapsamda && ' · bu çevrenin altlığı üretilmedi'}
      </p>
    </>
  )
}
