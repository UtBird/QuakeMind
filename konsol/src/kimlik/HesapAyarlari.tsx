import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, SignOut } from '@phosphor-icons/react'
import { useOturum } from './oturum'
import { ROL_ADI, varsayilanYol, type Rol } from './roller'
import { SifreFormu } from './SifreDegistirmeEkrani'
import { bashar } from './ProfilMenusu'
import { Marka } from '@/kabuk/Marka'

/* ---------------------------------------------------------------------------
   Hesap ayarları (J-183). Profil menüsünden açılır; her rol aynı sayfayı görür.
   Kim olduğun, ne yapabildiğin, şifre değiştirme ve çıkış.

   Ad, e-posta ve rol kişinin kendisi tarafından değiştirilmez: rol yalnız
   sunucudan gelir (CLAUDE.md kural 5); ad ve rolü koordinasyon düzeltir.
--------------------------------------------------------------------------- */

const ROL_ACIKLAMASI: Record<Rol, string> = {
  afetzede: 'Yardım çağırır, hasar ve ihtiyaç bildirir, en yakın toplanma alanını ve hastaneyi görür.',
  saha: 'Ekibine verilen görevleri görür, durumunu ve konumunu bildirir.',
  koordinator: 'Konsolu kullanır: SOS kuyruğu, ekip sevki, duyuru. Saha ekibi hesabı açar.',
  yonetici: 'Koordinatörün yaptığı her şey; ayrıca koordinatör ve yönetici hesabı açar.',
}

export function HesapAyarlari() {
  const { oturum, cikisYap } = useOturum()
  const git = useNavigate()
  const [kaydedildi, setKaydedildi] = useState(false)
  if (!oturum) return null // RolKapisi girişe gönderir

  const kart = 'rounded-panel border border-line bg-panel p-3.5'
  const baslik = 'text-micro ls-micro text-ink-3 uppercase'

  return (
    <div className="h-full overflow-auto bg-ground">
      <header className="flex h-topbar items-center gap-3 border-b border-line bg-panel px-4">
        <Marka />
        <span className="h-5 w-px bg-line-2" />
        <h1 className="text-body text-ink">Hesap ayarları</h1>
        <Link
          to={varsayilanYol(oturum.rol)}
          className="ml-auto flex h-9 items-center gap-1.5 rounded-control border border-line-2 px-3 text-body text-ink-2 hover:bg-hover hover:text-ink"
        >
          <ArrowLeft size={16} aria-hidden />
          Geri dön
        </Link>
      </header>

      <main className="mx-auto w-full max-w-form space-y-3 px-4 py-5">
        <section className={kart} aria-labelledby="hesap-kim">
          <h2 id="hesap-kim" className={baslik}>
            Hesabın
          </h2>
          <div className="mt-2.5 flex items-center gap-3">
            <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-accent-deep text-subtitle font-semibold text-ink">
              {bashar(oturum.adSoyad)}
            </span>
            <div className="min-w-0">
              <p className="truncate text-subtitle text-ink">{oturum.adSoyad}</p>
              <p className="truncate text-small text-ink-2">{oturum.eposta}</p>
            </div>
          </div>
          <dl className="mt-3 space-y-1.5 text-small">
            <div className="flex gap-3">
              <dt className="w-24 shrink-0 text-ink-3">Rol</dt>
              <dd className="text-ink">{ROL_ADI[oturum.rol]}</dd>
            </div>
            <div className="flex gap-3">
              <dt className="w-24 shrink-0 text-ink-3">Yapabildiğin</dt>
              <dd className="text-ink-2">{ROL_ACIKLAMASI[oturum.rol]}</dd>
            </div>
            {oturum.rol === 'saha' && (
              <div className="flex gap-3">
                <dt className="w-24 shrink-0 text-ink-3">Ekip</dt>
                <dd className="text-ink-2">
                  {oturum.ekipId
                    ? 'Bir ekibe bağlısın; görevlerin ekip ekranında.'
                    : 'Henüz bir ekibe bağlı değilsin; koordinasyona söyle.'}
                </dd>
              </div>
            )}
          </dl>
          <p className="mt-3 text-small text-ink-3">
            Adın ya da rolün yanlışsa {oturum.rol === 'yonetici' ? 'başka bir yönetici' : 'koordinasyon merkezi'}{' '}
            düzeltir; rolünü kendin değiştiremezsin.
          </p>
        </section>

        <section className={kart} aria-labelledby="hesap-sifre">
          <h2 id="hesap-sifre" className={baslik}>
            Şifre
          </h2>
          {oturum.ortakHesap ? (
            <p className="mt-2 text-small text-ink-2">
              Bu, ekip ve değerlendiricilerin birlikte kullandığı <span className="text-ink">ortak örnek hesap</span>.
              Şifresi buradan değiştirilemez; değişseydi herkes dışarıda kalırdı. Kendine ait bir hesap için
              yöneticiye başvur.
            </p>
          ) : (
            <>
              <p className="mt-2 text-small text-ink-2">
                Yeni şifre bütün cihazlardaki açık oturumlarını kapatır; bu cihazda oturumun sürer.
              </p>
              {kaydedildi && (
                <p role="status" className="mt-2 text-small text-ok">
                  Şifren değişti. Öbür cihazlarda yeniden giriş yapman gerekecek.
                </p>
              )}
              <SifreFormu zorunlu={false} dugme="Şifreyi değiştir" kaydedildi={() => setKaydedildi(true)} />
            </>
          )}
        </section>

        <section className={kart} aria-labelledby="hesap-oturum">
          <h2 id="hesap-oturum" className={baslik}>
            Oturum
          </h2>
          <div className="mt-2 flex items-center justify-between gap-3">
            <p className="text-small text-ink-2">Bu cihazdaki oturumu kapatır.</p>
            <button
              type="button"
              onClick={() => void cikisYap().then(() => git('/giris', { replace: true }))}
              className="flex h-9 shrink-0 items-center gap-1.5 rounded-control border border-line-2 px-3 text-body text-ink-2 hover:bg-hover hover:text-ink"
            >
              <SignOut size={16} aria-hidden />
              Çıkış yap
            </button>
          </div>
        </section>
      </main>
    </div>
  )
}
