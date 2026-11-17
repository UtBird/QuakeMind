import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Crosshair, MapPin, MapTrifold, NavigationArrow, UsersThree, Warning } from '@phosphor-icons/react'
import { Marka } from '@/kabuk/Marka'
import { Rozet } from '@/kabuk/parcalar'
import { useOturum } from '@/kimlik/oturum'
import { useCanliAkisDurumu } from '@/canli/canliAkis'
import { useZaman } from '@/durum/zamanDurumu'
import { dogruluk, mesafe, once, saat, sureMetni, tarihSaat } from '@/lib/bicim'
import { sn } from '@/lib/sinif'
import { IHTIYAC_ADI, ONCELIK_ADI, ONCELIK_TON, type Ihtiyac } from '@/veri/sorgular'
import { IHBAR_TURU } from '@/veri/ihbar'
import {
  GOREV_DURUMU,
  SONRAKI_ADIM,
  kurumTur,
  useEkibim,
  useEkipKonumu,
  useGorevDurumu,
  type Ekibim,
  type GorevDurumu,
} from '@/veri/gorev'
import { kusUcusuM } from '@/afetzede/konum'
import { GorevCizelgesi, hedefEtiketi } from '@/modlar/sevk'

// J-162: harita motoru (MapLibre + deck.gl) yalnız "Haritada göster"e basılınca iner;
// görev ekranının telefondaki açılışı hafif kalır.
const GorevHaritasi = lazy(() => import('./GorevHaritasi'))

/* ---------------------------------------------------------------------------
   Saha ekibinin görev ekranı (J-54). Telefonda, tek sütun.

   Kullanıcı: "hangi ihbar, neredeki ihbar, hangi ekip gidecek ya da gidiyor,
   kaç kişi gidiyor; bunlar hep belirsiz." Ekip burada kendi görevini görür
   ve durumunu tek dokunuşla işaretler: "Yola çıktık", "Vardık", "İşimiz
   bitti". Her adım konsolda ve afetzedenin ekranında anında görünür.

   Konum: ekip isterse telefonunun konumunu paylaşır. Sayfa açıkken gider
   (tarayıcı arka planda konum vermez); en çok 30 saniyede bir ya da 25
   metreden fazla yer değişince. Bu yoklama değildir: cihaz konum verdikçe
   gönderilir.
--------------------------------------------------------------------------- */

const KONUM_TERCIHI = 'qm-ekip-konum-paylas'

function tercihOku(): boolean {
  try {
    return window.localStorage.getItem(KONUM_TERCIHI) === '1'
  } catch {
    return false
  }
}

function tercihYaz(acik: boolean) {
  try {
    window.localStorage.setItem(KONUM_TERCIHI, acik ? '1' : '0')
  } catch {
    /* gizli pencere: tercih hatırlanmaz */
  }
}

type KonumDurumu = { son?: number; dogrulukM?: number; hata?: string }

function useKonumPaylasimi(ekipId: string | null) {
  const [acik, setAcik] = useState(tercihOku)
  const [durum, setDurum] = useState<KonumDurumu>({})
  const { mutate } = useEkipKonumu()
  const son = useRef<{ lat: number; lon: number; t: number } | null>(null)

  useEffect(() => {
    if (!acik || !ekipId) return
    if (!('geolocation' in navigator)) {
      setDurum({ hata: 'Bu tarayıcı konum vermiyor.' })
      return
    }
    const izleme = navigator.geolocation.watchPosition(
      (p) => {
        const nokta = { lat: p.coords.latitude, lon: p.coords.longitude }
        const simdi = Date.now()
        const onceki = son.current
        if (onceki && simdi - onceki.t < 30_000 && kusUcusuM(onceki, nokta) < 25) return
        son.current = { ...nokta, t: simdi }
        mutate(
          { ekipId, ...nokta, dogrulukM: Number.isFinite(p.coords.accuracy) ? Math.round(p.coords.accuracy) : undefined },
          {
            onSuccess: () => setDurum({ son: simdi, dogrulukM: p.coords.accuracy }),
            onError: (e) => setDurum({ hata: e instanceof Error ? e.message : 'Konum gönderilemedi.' }),
          },
        )
      },
      (e) => setDurum({ hata: e.code === 1 ? 'Konum izni verilmedi.' : 'Konum alınamadı.' }),
      { enableHighAccuracy: true, maximumAge: 10_000, timeout: 30_000 },
    )
    return () => navigator.geolocation.clearWatch(izleme)
  }, [acik, ekipId, mutate])

  function degistir(yeni: boolean) {
    tercihYaz(yeni)
    setAcik(yeni)
    if (!yeni) {
      son.current = null
      setDurum({})
    }
  }
  return { acik, degistir, durum }
}

export function EkipEkrani() {
  const { oturum, cikisYap } = useOturum()
  const git = useNavigate()
  const ekibim = useEkibim()
  const akis = useCanliAkisDurumu((d) => d.durum)
  const ekip = ekibim.data?.ekip ?? null
  const konum = useKonumPaylasimi(ekip?.id ?? null)

  return (
    <div className="flex h-full flex-col bg-ground">
      <header className="flex h-topbar shrink-0 items-center gap-2 border-b border-line bg-panel px-3.5">
        <Marka />
        <span className="text-body text-ink-2">Saha ekibi</span>
        <span className="flex-1" />
        <span className="flex items-center gap-1.5 text-small text-ink-2" title="Görevin canlı gelir">
          <span
            aria-hidden
            className={sn('h-2 w-2 rounded-full', akis === 'bagli' ? 'bg-ok' : akis === 'kopuk' ? 'bg-ink-3' : 'bg-mid')}
          />
          {akis === 'bagli' ? 'Canlı' : akis === 'kopuk' ? 'Koptu' : 'Bağlanıyor'}
        </span>
        <Link
          to="/konsol/ekipler"
          className="hidden h-9 items-center rounded-control border border-line-2 px-3 text-body text-ink-2 hover:bg-hover hover:text-ink sm:flex"
        >
          Konsol
        </Link>
        <button
          type="button"
          onClick={() => void cikisYap().then(() => git('/giris', { replace: true }))}
          className="h-9 rounded-control border border-line-2 px-3 text-body text-ink-2 hover:bg-hover hover:text-ink"
        >
          Çıkış
        </button>
      </header>

      <main className="min-h-0 flex-1 overflow-auto">
        <div className="mx-auto w-full max-w-xl space-y-3 px-4 py-4">
          {ekibim.isPending && <p className="text-body text-ink-2">Görevin yükleniyor…</p>}
          {ekibim.isError && (
            <p role="alert" className="rounded-panel border border-line-2 bg-panel p-3 text-body text-ink">
              Görev bilgisi alınamadı. Bağlantını kontrol et; sayfa canlı akış gelince kendini yeniler.
            </p>
          )}
          {ekibim.data && !ekip && (
            <section className="rounded-panel border border-line-2 bg-panel p-4">
              <p className="text-subtitle text-ink">Bir ekibe bağlı değilsin.</p>
              <p className="mt-1 text-body text-ink-2">
                Koordinasyon seni bir ekibe bağlayınca ({oturum?.eposta}) ekibinin görevi burada görünür.
              </p>
            </section>
          )}
          {ekip && ekibim.data && (
            <>
              <EkipBasligi veri={ekibim.data} />
              <KonumPaylasimi {...konum} />
              {ekibim.data.gorev ? <GorevKarti veri={ekibim.data} /> : <GorevYok />}
              {ekibim.data.gecmis.length > 0 && <Gecmis veri={ekibim.data} />}
            </>
          )}
        </div>
      </main>
    </div>
  )
}

function EkipBasligi({ veri }: { veri: Ekibim }) {
  const e = veri.ekip!
  return (
    <section className="flex items-center gap-3 rounded-panel border border-line bg-panel p-3">
      <span aria-hidden className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-accent-soft text-accent">
        <UsersThree size={22} weight="bold" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-subtitle font-semibold text-ink">{e.ad}</p>
        <p className="truncate text-small text-ink-2">
          {[kurumTur(e), e.kisiSayisi ? `${e.kisiSayisi} kişi` : null].filter(Boolean).join(' · ') ||
            'kurum ve tür yazılmamış'}
        </p>
      </div>
      <Rozet ton={e.gorev ? GOREV_DURUMU[e.gorev.durum].ton : e.durum === 'hizmet-disi' ? 'nötr' : 'accent'}>
        {e.gorev ? GOREV_DURUMU[e.gorev.durum].kisa : e.durum === 'hizmet-disi' ? 'Hizmet dışı' : 'Müsait'}
      </Rozet>
    </section>
  )
}

function KonumPaylasimi({
  acik,
  degistir,
  durum,
}: {
  acik: boolean
  degistir: (v: boolean) => void
  durum: KonumDurumu
}) {
  const simdi = useZaman((z) => z.simdi)
  return (
    <section className="flex items-center gap-3 rounded-panel border border-line bg-panel p-3">
      <Crosshair size={20} className={acik ? 'text-accent' : 'text-ink-3'} aria-hidden />
      <div className="min-w-0 flex-1 text-small">
        <p className="text-ink">{acik ? 'Konumun koordinasyonla paylaşılıyor' : 'Konumun paylaşılmıyor'}</p>
        <p className="text-ink-3">
          {durum.hata
            ? durum.hata
            : acik && durum.son
              ? `Son gönderim ${once(durum.son, simdi)}${durum.dogrulukM ? ` · ${dogruluk(durum.dogrulukM)}` : ''}. Sayfa açıkken gider.`
              : acik
                ? 'Konum bekleniyor…'
                : 'Paylaşırsan koordinasyon ve yardım bekleyen kişi ekibin nerede olduğunu görür.'}
        </p>
      </div>
      <button
        type="button"
        aria-pressed={acik}
        onClick={() => degistir(!acik)}
        className={sn(
          'h-10 shrink-0 rounded-control px-3 text-body font-semibold',
          acik ? 'border border-line-2 text-ink-2 hover:bg-hover hover:text-ink' : 'bg-accent text-accent-ink',
        )}
      >
        {acik ? 'Durdur' : 'Paylaş'}
      </button>
    </section>
  )
}

function GorevYok() {
  return (
    <section className="rounded-panel border border-line bg-panel p-4">
      <p className="text-subtitle text-ink">Şu an görevin yok.</p>
      <p className="mt-1 text-body text-ink-2">
        Koordinasyon ekibini bir olaya gönderince burada görünür; sayfa kendiliğinden yenilenir.
      </p>
    </section>
  )
}

/** Olayın ayrıntısı: sunucu ekibe olayın butun bilgisini verir (`/api/ekibim`). */
type Olay = {
  tur?: 'fotograf' | 'metin' | 'ihtiyac'
  oncelik?: 'kritik' | 'yuksek' | 'orta'
  metin?: string | null
  mahalle?: string | null
  etiket?: string | null
  kisiSayisi?: number | null
  ihtiyaclar?: Ihtiyac[] | null
  konumKaynagi?: 'gps' | 'mahalle' | 'metin' | null
  konumDogrulukM?: number | null
  zaman?: number
  lon?: number
  lat?: number
}

function GorevKarti({ veri }: { veri: Ekibim }) {
  const g = veri.gorev!
  const olay = (g.olay ?? {}) as Olay
  const simdi = useZaman((z) => z.simdi)
  const durum = useGorevDurumu()
  const [form, setForm] = useState<null | 'tamamlandi' | 'iptal'>(null)
  const [not, setNot] = useState('')
  const [suruyor, setSuruyor] = useState(false)
  const [haritaAcik, setHaritaAcik] = useState(false)
  const sonraki = SONRAKI_ADIM[g.durum]
  const sos = g.hedefTur === 'sos'
  const tur = sos ? IHBAR_TURU.sos : IHBAR_TURU[olay.tur ?? 'metin']
  const lat = g.hedef?.lat ?? olay.lat
  const lon = g.hedef?.lon ?? olay.lon

  function gonder(yeni: GorevDurumu, ek?: { not?: string; olaySuruyor?: boolean }) {
    durum.mutate(
      { gorevId: g.id, durum: yeni, ...ek },
      {
        onSuccess: () => {
          setForm(null)
          setNot('')
          setSuruyor(false)
        },
      },
    )
  }

  return (
    <section className={sn('rounded-panel border-2 bg-panel p-4', tur.kenar)}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className={sn('text-small font-semibold', tur.metin)}>{tur.ad}</p>
          <p className="text-title font-semibold text-ink">{olay.mahalle ?? hedefEtiketi(g.hedef)}</p>
        </div>
        {sos && olay.oncelik && <Rozet ton={ONCELIK_TON[olay.oncelik]}>{ONCELIK_ADI[olay.oncelik]}</Rozet>}
      </div>

      <dl className="kilav-kv mt-3 gap-x-3 gap-y-1.5 text-body">
        {olay.kisiSayisi != null && (
          <>
            <dt className="text-ink-3">Kişi</dt>
            <dd className="font-semibold text-ink">{olay.kisiSayisi} kişi</dd>
          </>
        )}
        {!!olay.ihtiyaclar?.length && (
          <>
            <dt className="text-ink-3">İhtiyaç</dt>
            <dd className="text-ink">{olay.ihtiyaclar.map((i) => IHTIYAC_ADI[i] ?? i).join(', ')}</dd>
          </>
        )}
        {olay.metin && (
          <>
            <dt className="text-ink-3">Notu</dt>
            <dd className="whitespace-pre-line text-ink">{olay.metin}</dd>
          </>
        )}
        {olay.etiket && !sos && (
          <>
            <dt className="text-ink-3">Model</dt>
            <dd className="text-ink">{olay.etiket}</dd>
          </>
        )}
        <dt className="text-ink-3">Geldi</dt>
        <dd className="text-ink">
          {olay.zaman ? tarihSaat(olay.zaman) : '—'}
          {olay.zaman ? <span className="text-ink-3"> · {once(olay.zaman, simdi)}</span> : null}
        </dd>
        <dt className="text-ink-3">Giden</dt>
        <dd className="text-ink">
          {g.kisiSayisi} kişi{g.ekDestek ? ' · ek destek' : ''}
          {g.atayanAd ? <span className="text-ink-3"> · gönderen {g.atayanAd}</span> : null}
        </dd>
      </dl>

      {olay.konumKaynagi === 'mahalle' && (
        <p className="mt-3 flex gap-2 rounded-control border border-high bg-high/15 px-2.5 py-2 text-small text-ink">
          <Warning size={16} weight="fill" className="mt-0.5 shrink-0 text-high" aria-hidden />
          Konum yaklaşık: kişi konum veremedi, mahalle merkezi işaretli. Notunu ve çevreyi kontrol et.
        </p>
      )}

      {lat != null && lon != null && (
        <div className="mt-3 rounded-control border border-line-2 bg-sunken p-2.5 text-small">
          <p className="flex items-center gap-1.5 text-ink">
            <MapPin size={16} weight="bold" className="text-accent" aria-hidden />
            {g.durum === 'olay-yerinde'
              ? 'Olayın konumu'
              : g.yol
                ? `Olaya yoldan ${mesafe(g.yol.mesafeM)} · tahmini ~${sureMetni(g.yol.sureDk)}`
                : g.kalanM != null
                  ? `Olaya kuş uçuşu ${mesafe(g.kalanM)} (yol ağı dışında)`
                  : 'Olayın konumu'}
          </p>
          {g.yol && g.durum !== 'olay-yerinde' && (
            <p className="mt-0.5 text-ink-3">
              Son konumuna göre, araç yolundan; tek yönlere uyar, bilinen kapanmalardan kaçınır. Hız yol
              türüne göre ortalama, trafik verisi yok.
              {g.yol.kapanmadanGecer > 0 ? ' Başka yol olmadığı için rota bilinen bir kapanmadan geçiyor.' : ''}
            </p>
          )}
          <p className="mt-0.5 font-mono text-ink-2">
            {lat.toFixed(5)}, {lon.toFixed(5)}
            {olay.konumKaynagi === 'gps' && olay.konumDogrulukM != null ? ` · ${dogruluk(olay.konumDogrulukM)}` : ''}
          </p>
          <button
            type="button"
            aria-expanded={haritaAcik}
            onClick={() => setHaritaAcik((a) => !a)}
            className="mt-2 flex h-10 w-full items-center justify-center gap-1.5 rounded-control border border-line-2 text-body text-ink hover:bg-hover"
          >
            <MapTrifold size={16} weight="bold" className="text-accent" aria-hidden />
            {haritaAcik ? 'Haritayı gizle' : 'Rotayı haritada göster'}
          </button>
          {haritaAcik && (
            <Suspense fallback={<p className="mt-2 text-small text-ink-3">Harita yükleniyor…</p>}>
              <GorevHaritasi
                rota={g.rota}
                ekip={g.ekipKonumu ? [g.ekipKonumu.lon, g.ekipKonumu.lat] : null}
                olay={[lon, lat]}
              />
            </Suspense>
          )}
          {/* geo: bağlantısı telefonun kendi harita uygulamasını açar; konum
              bir web hizmetine adres içinde gönderilmez. O uygulama bizim
              kapanmalarımızı BİLMEZ (J-162); bu yüzden ikincil düğme. */}
          <a
            href={`geo:${lat},${lon}?q=${lat},${lon}`}
            className="mt-2 flex h-10 items-center justify-center gap-1.5 rounded-control border border-line-2 text-body text-ink hover:bg-hover"
          >
            <NavigationArrow size={16} weight="bold" aria-hidden />
            Telefonun haritasında aç
          </a>
          <p className="mt-1 text-small text-ink-3">
            Telefonun haritası bilinen kapalı yolları bilmez; yolu yukarıdaki haritaya göre seç.
          </p>
        </div>
      )}

      {g.not && (
        <p className="mt-3 rounded-control border border-line-2 px-2.5 py-2 text-small text-ink">
          <span className="text-ink-3">Koordinasyonun notu: </span>
          {g.not}
        </p>
      )}

      <div className="mt-3">
        <GorevCizelgesi gorev={g} />
      </div>

      {/* Adım düğmeleri kartın altında YAPIŞKAN (J-167 U-1): telefonda kart uzun,
          "Yola çıktık" 375×812'de 800. pikseldeydi ve görmek için kaydırmak
          gerekiyordu. Çubuk kart boyunca ekranın altında durur. */}
      <div className="sticky bottom-0 z-10 -mx-4 -mb-4 mt-4 rounded-b-panel border-t border-line bg-panel px-4 pt-3 alt-guvenli">
      {form === null ? (
        <div className="grid gap-2">
          {sonraki && sonraki.durum !== 'tamamlandi' ? (
            <>
              <button
                type="button"
                disabled={durum.isPending}
                onClick={() => gonder(sonraki.durum)}
                className="h-12 rounded-control bg-accent text-subtitle font-semibold text-accent-ink hover:bg-accent-deep hover:text-ink disabled:opacity-40"
              >
                {sonraki.ekipEylemi}
              </button>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  disabled={durum.isPending}
                  onClick={() => setForm('tamamlandi')}
                  className="h-11 rounded-control border border-line-2 text-body text-ink hover:bg-hover disabled:opacity-40"
                >
                  İşimiz bitti…
                </button>
                <button
                  type="button"
                  disabled={durum.isPending}
                  onClick={() => setForm('iptal')}
                  className="h-11 rounded-control border border-line-2 text-body text-ink-2 hover:bg-hover hover:text-ink disabled:opacity-40"
                >
                  Gidemiyoruz…
                </button>
              </div>
            </>
          ) : (
            <>
              <button
                type="button"
                disabled={durum.isPending}
                onClick={() => setForm('tamamlandi')}
                className="h-12 rounded-control bg-accent text-subtitle font-semibold text-accent-ink hover:bg-accent-deep hover:text-ink disabled:opacity-40"
              >
                İşimiz bitti…
              </button>
              <button
                type="button"
                disabled={durum.isPending}
                onClick={() => setForm('iptal')}
                className="h-11 rounded-control border border-line-2 text-body text-ink-2 hover:bg-hover hover:text-ink disabled:opacity-40"
              >
                Gidemiyoruz…
              </button>
            </>
          )}
        </div>
      ) : (
        <div className="rounded-control border border-line-2 p-3">
          <label htmlFor="gorev-not" className="block text-body text-ink">
            {form === 'iptal' ? 'Neden gidemiyorsunuz? (zorunlu)' : 'Sonuç (isteğe bağlı)'}
          </label>
          <input
            id="gorev-not"
            value={not}
            maxLength={300}
            onChange={(e) => setNot(e.target.value)}
            placeholder={form === 'iptal' ? 'ör. yol kapalı, araç arızalı' : 'ör. 2 kişi kurtarıldı'}
            className="mt-1.5 w-full rounded-control border border-line-2 bg-sunken px-2.5 py-2.5 text-body text-ink"
          />
          {form === 'tamamlandi' && (
            <label className="mt-2.5 flex items-start gap-2 text-body text-ink">
              <input
                type="checkbox"
                checked={suruyor}
                onChange={(e) => setSuruyor(e.target.checked)}
                className="mt-1 accent-accent"
              />
              Olay sürüyor; başka ekip ya da ekipman gerekiyor
            </label>
          )}
          <p className="mt-2 text-small text-ink-3">
            {form === 'iptal'
              ? 'Olay yeniden sıraya girer; koordinasyon başka ekip gönderir.'
              : suruyor
                ? 'Olay kapanmaz, yeniden sıraya girer.'
                : 'Olayda başka ekip yoksa olay kapanır.'}
          </p>
          <div className="mt-3 grid grid-cols-2 gap-2">
            <button
              type="button"
              disabled={durum.isPending || (form === 'iptal' && !not.trim())}
              onClick={() =>
                gonder(form, { not: not.trim() || undefined, olaySuruyor: form === 'tamamlandi' ? suruyor : undefined })
              }
              className="h-11 rounded-control bg-accent text-body font-semibold text-accent-ink hover:bg-accent-deep hover:text-ink disabled:opacity-40"
            >
              {form === 'iptal' ? 'Gidemiyoruz' : 'Bitti olarak kaydet'}
            </button>
            <button
              type="button"
              onClick={() => setForm(null)}
              className="h-11 rounded-control border border-line-2 text-body text-ink-2 hover:bg-hover hover:text-ink"
            >
              Vazgeç
            </button>
          </div>
        </div>
      )}
      {durum.isError && (
        <p role="alert" className="mt-2 text-small text-crit">
          {durum.error instanceof Error ? durum.error.message : 'Durum kaydedilemedi.'}
        </p>
      )}
      </div>
    </section>
  )
}

function Gecmis({ veri }: { veri: Ekibim }) {
  return (
    <section className="rounded-panel border border-line bg-panel p-3">
      <p className="text-small text-ink-2">Son görevler</p>
      <ul className="mt-1.5">
        {veri.gecmis.map((g) => (
          <li key={g.id} className="border-t border-line py-2 text-small">
            <p className="text-ink">
              {hedefEtiketi(g.hedef)} · {g.kisiSayisi} kişi
              <span className="text-ink-2">
                {' '}
                · {GOREV_DURUMU[g.durum].kisa}
                {g.bitti ? ` ${saat(g.bitti)}` : ''}
              </span>
            </p>
            {g.sonuc && <p className="text-ink-3">{g.sonuc}</p>}
          </li>
        ))}
      </ul>
    </section>
  )
}
