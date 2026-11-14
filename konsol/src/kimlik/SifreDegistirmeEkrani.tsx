import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useOturum } from './oturum'
import { Bekleme } from './RolKapisi'
import { ROL_ADI, varsayilanYol } from './roller'
import { Marka } from '@/kabuk/Marka'

/* ---------------------------------------------------------------------------
   Şifre değiştirme (J-157).

   Koordinasyonun açtığı ya da şifresini yenilediği hesap geçici şifreyle girer;
   kendi şifresini koymadan başka hiçbir ekrana geçemez (RolKapisi yönlendirir,
   sunucu da korunan her uçta 403 verir). Geçici şifresi olmayan biri de bu
   ekrandan kendi şifresini değiştirebilir.
--------------------------------------------------------------------------- */

const SIFRE_EN_AZ = 8

export function SifreDegistirmeEkrani() {
  const { oturum, yukleniyor, sifreDegistir, cikisYap } = useOturum()
  const git = useNavigate()
  const [eski, setEski] = useState('')
  const [yeni, setYeni] = useState('')
  const [tekrar, setTekrar] = useState('')
  const [hata, setHata] = useState<string | null>(null)
  const [gonderiliyor, setGonderiliyor] = useState(false)
  // Kaydedildikten sonra sonraki ekran yüklenirken form bir an "isteğe bağlı"
  // hâliyle görünmesin.
  const [bitti, setBitti] = useState(false)

  if (yukleniyor) return <Bekleme />
  if (!oturum) return <Navigate to="/giris" replace />
  if (bitti)
    return (
      <div className="grid h-full place-items-center bg-ground text-small text-ink-2">
        Şifren kaydedildi. Açılıyor…
      </div>
    )

  const zorunlu = !!oturum.sifreDegismeli
  const eksik = [
    !eski && (zorunlu ? 'sana verilen geçici şifre' : 'şu anki şifren'),
    yeni.length < SIFRE_EN_AZ && `en az ${SIFRE_EN_AZ} karakterlik yeni şifre`,
    yeni && eski && yeni === eski && 'eskisinden farklı bir şifre',
    tekrar !== yeni && 'iki yeni şifre aynı olmalı',
  ].filter(Boolean)

  async function gonder(e: FormEvent) {
    e.preventDefault()
    if (eksik.length) return
    setHata(null)
    setGonderiliyor(true)
    try {
      const guncel = await sifreDegistir(eski, yeni)
      setBitti(true)
      git(varsayilanYol(guncel.rol), { replace: true })
    } catch (err) {
      setHata(err instanceof Error ? err.message : 'Şifre değiştirilemedi.')
    } finally {
      setGonderiliyor(false)
    }
  }

  const alan =
    'mt-1.5 w-full rounded-control border border-line-2 bg-sunken px-2.5 py-2 text-body text-ink outline-none focus:border-accent'
  const etiket = 'mt-3 block text-micro ls-micro text-ink-3 uppercase'

  return (
    <div className="grid h-full place-items-center overflow-auto bg-ground p-6">
      <div className="w-full max-w-form">
        <div className="mb-5 flex items-center gap-2.5">
          <Marka />
        </div>

        <form
          onSubmit={gonder}
          className="rounded-panel border border-line bg-panel p-3.5"
          aria-labelledby="sifre-baslik"
        >
          <h1 id="sifre-baslik" className="text-subtitle text-ink">
            {zorunlu ? 'Kendi şifreni belirle' : 'Şifreni değiştir'}
          </h1>
          <p className="mt-1.5 text-small text-ink-2">
            {zorunlu
              ? `Hoş geldin ${oturum.adSoyad}. Hesabını koordinasyon merkezi açtı ve sana geçici bir şifre verdi. Devam etmeden önce yalnız senin bildiğin bir şifre koy.`
              : 'Yeni şifre bütün cihazlardaki açık oturumlarını kapatır; bu cihazda oturumun sürer.'}
          </p>
          <p className="mt-1.5 text-small text-ink-3">
            {oturum.eposta} · {ROL_ADI[oturum.rol]}
          </p>

          <label className={etiket} htmlFor="eski-sifre">
            {zorunlu ? 'Geçici şifre' : 'Şu anki şifre'}
          </label>
          <input
            id="eski-sifre"
            type="password"
            autoComplete="current-password"
            value={eski}
            onChange={(e) => setEski(e.target.value)}
            className={alan}
          />

          <label className={etiket} htmlFor="yeni-sifre">
            Yeni şifre · en az {SIFRE_EN_AZ} karakter
          </label>
          <input
            id="yeni-sifre"
            type="password"
            autoComplete="new-password"
            value={yeni}
            onChange={(e) => setYeni(e.target.value)}
            className={alan}
          />

          <label className={etiket} htmlFor="yeni-sifre-tekrar">
            Yeni şifre (tekrar)
          </label>
          <input
            id="yeni-sifre-tekrar"
            type="password"
            autoComplete="new-password"
            value={tekrar}
            onChange={(e) => setTekrar(e.target.value)}
            className={alan}
          />

          {hata && (
            <p role="alert" className="mt-3 text-small text-crit">
              {hata}
            </p>
          )}

          <button
            type="submit"
            disabled={gonderiliyor || eksik.length > 0}
            className="mt-4 w-full rounded-control bg-accent px-3 py-2.5 text-body font-semibold text-accent-ink disabled:opacity-50"
          >
            {gonderiliyor ? 'Kaydediliyor…' : 'Şifreyi kaydet ve devam et'}
          </button>
          {eksik.length > 0 && (eski || yeni || tekrar) && (
            <p className="mt-2 text-small text-ink-3">Gerekli: {eksik.join(' · ')}.</p>
          )}
        </form>

        <div className="mt-3 flex items-center justify-between gap-2 rounded-panel border border-line bg-panel p-3.5">
          <p className="text-small text-ink-2">
            {zorunlu ? 'Geçici şifren çalışmıyorsa ekip sorumluna söyle.' : 'Vazgeçtin mi?'}
          </p>
          {zorunlu ? (
            <button
              type="button"
              onClick={() => void cikisYap().then(() => git('/giris', { replace: true }))}
              className="rounded-control border border-line-2 px-3 py-1.5 text-body text-ink-2 hover:bg-hover"
            >
              Çıkış
            </button>
          ) : (
            <button
              type="button"
              onClick={() => git(varsayilanYol(oturum.rol))}
              className="rounded-control border border-line-2 px-3 py-1.5 text-body text-ink-2 hover:bg-hover"
            >
              Geri dön
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
