import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Warning } from '@phosphor-icons/react'
import { Micro } from './parcalar'
import { useSimulasyon } from '@/durum/simulasyonDurumu'
import { sonIsSec, useIsler } from '@/durum/islerDurumu'
import { useSimBitir, useSimSonuc } from '@/veri/simulasyon'
import { useOturum } from '@/kimlik/oturum'
import { modBul, modGorunur } from '@/modlar/modlar'

/* ---------------------------------------------------------------------------
   TATBİKAT şeridi (SIMULASYON_SOZLESMESI.md §5 madde 1).

   Koşu varken KALICIDIR: uyarıyı susturan bir "kapat" yoktur ve mod değişince
   kaybolmaz, çünkü asıl işi "ekrandaki bu şey gerçek olay değil" demektir.
   Şerit kabukta durur, mod panelinde değil; SOS moduna geçilse de görünür.

   "Tatbikatı bitir" ise şeritte durur (J-186): uyarıyı susturmaz, tatbikatı
   SONA ERDİRİR (koşunun hasar noktaları silinir, katmanlar düşer). Eskiden
   yalnız tatbikat panelinin dibindeydi; başka moddaki kullanıcı tatbikatı
   kapatmanın yolunu bulamıyordu.

   Yanıp sönmez, renk geçişi yapmaz (ARAYUZ §6: sürekli yanıp sönen öğe yok).
--------------------------------------------------------------------------- */

export function TatbikatSeridi() {
  const isId = useSimulasyon((d) => d.isId)
  const hazir = useSimulasyon((d) => d.hazir)
  const is = useIsler(sonIsSec)
  const sonuc = useSimSonuc(isId)
  const { oturum } = useOturum()
  // Şerit herkese görünür (gerçek olay değil uyarısı); panel bağlantısı yalnız
  // tatbikatı yönetebilene (J-163).
  const sim = modBul('simulasyon')
  const panelGorunur = !!sim && modGorunur(sim, oturum?.rol)
  const bitir = useSimBitir()
  const temizle = useSimulasyon((d) => d.temizle)
  const [soruyor, setSoruyor] = useState(false)

  if (!isId) return null

  function tatbikatiBitir() {
    if (!isId) return
    bitir.mutate(isId, {
      onSuccess: () => {
        setSoruyor(false)
        temizle()
      },
    })
  }

  const simIs = is?.isTipi === 'simulasyon' ? is : null
  // `alan` OPSIYONEL: bayat bir is kimliginle yenilendiginde sunucu 404 doner
  // ya da is henuz kuyruktayken yanitta alan kunyesi bulunmaz. Burada `?.`
  // olmayinca butun konsol beyaz ekrana dusuyordu (J-104, 27 Eylul 2026).
  const alanAdi = sonuc.data?.alan?.ad
  // Sayfa yenilendiğinde iş kaydı (sekme belleği) sıfırlanır ama koşu sunucuda
  // durur; o yüzden durum SONUCUN kendisinden de okunur, yoksa biten koşu
  // yenileme sonrası "%0 · katman bekleniyor" görünüyordu.
  const sonucDurumu = sonuc.data?.durum
  const durum =
    simIs?.durum === 'bitti' || sonucDurumu === 'bitti'
      ? 'bitti'
      : simIs?.durum === 'hata' || sonucDurumu === 'hata'
        ? 'hata'
        : 'koşuyor'
  const hazirSayisi = sonucDurumu === 'bitti' ? 4 : hazir.length

  return (
    <div
      role="status"
      className="flex shrink-0 items-center gap-3 rounded-panel border border-mid bg-panel px-3 py-2"
    >
      <span className="flex items-center gap-2 text-mid">
        <Warning size={16} weight="fill" aria-hidden />
        <span className="text-micro ls-micro uppercase">Tatbikat</span>
      </span>
      <span className="text-small text-ink">
        Bu ekranda gördüklerin bir tatbikat koşusudur — gerçek olay değildir.
      </span>
      {alanAdi && <Micro>{alanAdi}</Micro>}
      <Micro>
        {durum === 'bitti'
          ? `${hazirSayisi}/4 katman`
          : durum === 'hata'
            ? 'koşu hatası'
            : `%${Math.round(simIs?.ilerleme ?? sonuc.data?.ilerleme ?? 0)}`}
      </Micro>
      {panelGorunur && (
        <span className="ml-auto flex shrink-0 items-center gap-1.5">
          {soruyor ? (
            <>
              <span className="text-small text-ink-2">Bitirilsin mi? Koşunun hasar noktaları silinir.</span>
              <button
                type="button"
                onClick={tatbikatiBitir}
                disabled={bitir.isPending}
                className="rounded-control bg-accent px-2.5 py-1 text-small font-semibold text-accent-ink disabled:opacity-50"
              >
                {bitir.isPending ? 'Bitiriliyor…' : 'Evet, bitir'}
              </button>
              <button
                type="button"
                onClick={() => setSoruyor(false)}
                className="rounded-control border border-line-2 px-2 py-1 text-small text-ink-2 hover:bg-hover hover:text-ink"
              >
                Vazgeç
              </button>
            </>
          ) : (
            <>
              <Link
                to="/konsol/simulasyon"
                className="rounded-control border border-line-2 px-2 py-1 text-small text-ink-2 hover:bg-hover hover:text-ink"
              >
                Tatbikat paneli
              </Link>
              <button
                type="button"
                onClick={() => setSoruyor(true)}
                className="rounded-control border border-mid px-2 py-1 text-small text-ink hover:bg-hover"
              >
                Tatbikatı bitir
              </button>
            </>
          )}
          {bitir.isError && (
            <span role="alert" className="text-small text-crit">
              Bitirilemedi; yeniden dene.
            </span>
          )}
        </span>
      )}
    </div>
  )
}
