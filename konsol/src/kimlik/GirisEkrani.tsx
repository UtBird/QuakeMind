import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useOturum } from './oturum'
import { GIRIS_KAPILARI, acilisYolu, type GirisKapisi } from './roller'
import { Marka } from '@/kabuk/Marka'
import { sn } from '@/lib/sinif'

/* ---------------------------------------------------------------------------
   Giriş ve hesap açma (J-156).

   Üç kapı: Afetzede · Saha ekibi · Koordinasyon. Kişi önce kim olarak girdiğini
   seçer. Kapı ROL VERMEZ (CLAUDE.md kural 5): sunucu hesabın gerçek rolünü
   seçilen kapıyla karşılaştırır, uymazsa oturum açmaz ve doğru kapıyı söyler.

   Hesap açma yalnız Afetzede kapısında. Ekip ve koordinasyon hesaplarını
   koordinasyon merkezi konsoldaki Kullanıcılar ekranından açar.
--------------------------------------------------------------------------- */

const SIFRE_EN_AZ = 8
const KAPI_ANAHTARI = 'qm.girisKapisi'

const KAPI: Record<
  GirisKapisi,
  { ad: string; ne: string; hesapYoksa: string | null }
> = {
  afetzede: {
    ad: 'Afetzede',
    ne: 'Yardım çağır, ihbar gönder, en yakın toplanma alanını gör.',
    hesapYoksa: null, // bu kapıda hesap açılır
  },
  ekip: {
    ad: 'Saha ekibi',
    ne: 'Ekibine atanan görevler, yol tarifi ve görev durumu.',
    hesapYoksa:
      'Ekip hesabını koordinasyon merkezi açar ve sana geçici bir şifre verir. Şifreni unuttuysan ekip sorumluna söyle; yenisini o üretir.',
  },
  koordinasyon: {
    ad: 'Koordinasyon',
    ne: 'Konsol: harita, SOS kuyruğu, ekipler, analiz.',
    hesapYoksa: 'Koordinatör hesabını yönetici açar. Şifreni unuttuysan yöneticiye başvur.',
  },
}

function kayitliKapi(): GirisKapisi {
  // Kişi başına kolaylık: son seçilen kapı hatırlanır. Okunamazsa afetzede.
  try {
    const k = localStorage.getItem(KAPI_ANAHTARI)
    if (k && (GIRIS_KAPILARI as readonly string[]).includes(k)) return k as GirisKapisi
  } catch {
    /* gizli pencere / engelli depolama */
  }
  return 'afetzede'
}

function kapiyiKaydet(k: GirisKapisi) {
  try {
    localStorage.setItem(KAPI_ANAHTARI, k)
  } catch {
    /* önemli değil */
  }
}

export function GirisEkrani() {
  const { oturum, girisYap, kayitOl } = useOturum()
  const git = useNavigate()
  const [kapi, setKapi] = useState<GirisKapisi>(kayitliKapi)
  const [kip, setKip] = useState<'giris' | 'kayit'>('giris')
  const [adSoyad, setAdSoyad] = useState('')
  const [eposta, setEposta] = useState('')
  const [sifre, setSifre] = useState('')
  const [hata, setHata] = useState<string | null>(null)
  const [gonderiliyor, setGonderiliyor] = useState(false)

  if (oturum) return <Navigate to={acilisYolu(oturum)} replace />

  const kayit = kip === 'kayit' && kapi === 'afetzede'
  const eksik = kayit
    ? [
        adSoyad.trim().length < 2 && 'ad soyad',
        !eposta.includes('@') && 'e-posta',
        sifre.length < SIFRE_EN_AZ && `en az ${SIFRE_EN_AZ} karakterlik şifre`,
      ].filter(Boolean)
    : [!eposta.trim() && 'e-posta', !sifre && 'şifre'].filter(Boolean)

  async function gonder(e: FormEvent) {
    e.preventDefault()
    if (eksik.length) return
    setHata(null)
    setGonderiliyor(true)
    try {
      const yeni = kayit
        ? await kayitOl(eposta.trim(), adSoyad.trim(), sifre)
        : await girisYap(eposta.trim(), sifre, kapi)
      kapiyiKaydet(kapi)
      git(acilisYolu(yeni), { replace: true })
    } catch (err) {
      setHata(err instanceof Error ? err.message : kayit ? 'Hesap açılamadı.' : 'Giriş yapılamadı.')
    } finally {
      setGonderiliyor(false)
    }
  }

  function kapiSec(k: GirisKapisi) {
    setKapi(k)
    setKip('giris')
    setHata(null)
    setSifre('')
  }

  function kipDegistir(yeni: 'giris' | 'kayit') {
    setKip(yeni)
    setHata(null)
    setSifre('')
  }

  const alan =
    'mt-1.5 w-full rounded-control border border-line-2 bg-sunken px-2.5 py-2 text-body text-ink outline-none focus:border-accent'
  const etiket = 'mt-3 block text-micro ls-micro text-ink-3 uppercase'
  const tanim = KAPI[kapi]

  return (
    <div className="grid h-full place-items-center overflow-auto bg-ground p-6">
      <div className="w-full max-w-form">
        <div className="mb-5 flex items-center gap-2.5">
          <Marka />
        </div>

        <p id="kapi-baslik" className="text-micro ls-micro text-ink-3 uppercase">
          Kim olarak giriyorsun?
        </p>
        <div
          role="radiogroup"
          aria-labelledby="kapi-baslik"
          className="mt-1.5 grid grid-cols-3 gap-1 rounded-control border border-line bg-panel p-1"
        >
          {GIRIS_KAPILARI.map((k) => (
            <button
              key={k}
              type="button"
              role="radio"
              aria-checked={kapi === k}
              onClick={() => kapiSec(k)}
              className={sn(
                'rounded-control px-2 py-2 text-body transition-colors duration-150 ease-out-qm',
                kapi === k ? 'bg-accent-soft font-semibold text-ink' : 'text-ink-2 hover:bg-hover hover:text-ink',
              )}
            >
              {KAPI[k].ad}
            </button>
          ))}
        </div>
        <p className="mt-1.5 text-small text-ink-2">{tanim.ne}</p>

        <form
          onSubmit={gonder}
          className="mt-3 rounded-panel border border-line bg-panel p-3.5"
          aria-labelledby="giris-baslik"
        >
          <h1 id="giris-baslik" className="text-subtitle text-ink">
            {kayit ? 'Afetzede hesabı aç' : `${tanim.ad} girişi`}
          </h1>
          {kayit && (
            <p className="mt-1.5 text-small text-ink-2">
              Yardım çağırır, çağrının durumunu ve en yakın toplanma alanını görürsün.
            </p>
          )}

          {kayit && (
            <>
              <label className={etiket} htmlFor="ad-soyad">
                Ad soyad
              </label>
              <input
                id="ad-soyad"
                autoComplete="name"
                value={adSoyad}
                onChange={(e) => setAdSoyad(e.target.value)}
                className={alan}
              />
            </>
          )}

          <label className={etiket} htmlFor="eposta">
            E-posta
          </label>
          <input
            id="eposta"
            type="email"
            autoComplete={kayit ? 'email' : 'username'}
            value={eposta}
            onChange={(e) => setEposta(e.target.value)}
            className={alan}
          />

          <label className={etiket} htmlFor="sifre">
            Şifre{kayit ? ` · en az ${SIFRE_EN_AZ} karakter` : ''}
          </label>
          <input
            id="sifre"
            type="password"
            autoComplete={kayit ? 'new-password' : 'current-password'}
            value={sifre}
            onChange={(e) => setSifre(e.target.value)}
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
            {gonderiliyor
              ? kayit
                ? 'Hesap açılıyor…'
                : 'Giriş yapılıyor…'
              : kayit
                ? 'Hesap aç ve gir'
                : 'Giriş yap'}
          </button>
          {kayit && eksik.length > 0 && (adSoyad || eposta || sifre) && (
            <p className="mt-2 text-small text-ink-3">Eksik: {eksik.join(' · ')}.</p>
          )}
        </form>

        <div className="mt-3 rounded-panel border border-line bg-panel p-3.5">
          {kapi !== 'afetzede' ? (
            <>
              <p className="text-micro ls-micro text-ink-3 uppercase">Hesabın yoksa</p>
              <p className="mt-2 text-small text-ink-2">{tanim.hesapYoksa}</p>
            </>
          ) : kayit ? (
            <>
              <p className="text-small text-ink-2">Hesabın var mı?</p>
              <button
                type="button"
                onClick={() => kipDegistir('giris')}
                className="mt-2 w-full rounded-control border border-line-2 px-3 py-2 text-body text-ink hover:bg-hover"
              >
                Giriş yap
              </button>
            </>
          ) : (
            <>
              <p className="text-micro ls-micro text-ink-3 uppercase">Hesabın yoksa</p>
              <p className="mt-2 text-small text-ink-2">
                Yardım çağırmak için hesap aç; bir dakika sürer.
              </p>
              <button
                type="button"
                onClick={() => kipDegistir('kayit')}
                className="mt-2.5 w-full rounded-control border border-line-2 px-3 py-2 text-body text-ink hover:bg-hover"
              >
                Afetzede hesabı aç
              </button>
            </>
          )}
          <p className="mt-2.5 text-small text-ink-3">Acil durumda 112'yi ara.</p>
        </div>
      </div>
    </div>
  )
}
