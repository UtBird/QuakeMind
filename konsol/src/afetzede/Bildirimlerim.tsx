import { useMemo, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { CaretDown, ListChecks } from '@phosphor-icons/react'
import { useCanliAkisDurumu } from '@/canli/canliAkis'
import { Rozet } from '@/kabuk/parcalar'
import { IHTIYAC_ADI, type SosCagrisi } from '@/veri/sorgular'
import { sayi, tarihSaat } from '@/lib/bicim'
import { sn } from '@/lib/sinif'
import { IHBAR_DURUMU, IHBAR_TURU, ihbarKonumu, type Ihbar, type IhbarTuru } from '@/veri/ihbar'
import { IHBAR_IKONU } from '@/veri/ihbarIkon'
import { DURUM_ETIKETI } from './etiketler'
import { acikGorev } from '@/veri/gorev'
import { GelenEkipKarti, afetzedeDurumu } from './GelenEkip'
import { IlkAdimlar } from './parcalar'

/* ---------------------------------------------------------------------------
   Bildirimlerim (J-51): afetzedenin son 7 günde gönderdiği SOS çağrıları ve
   ihbarları, durumlarıyla. Koordinasyon ihbarı görünce ("Görüldü") ya da ekip
   atanınca satır canlı akışla kendiliğinden değişir; yoklama yoktur.
   Boşken sol sütun boş kalmasın diye deprem sonrası ilk adımlar yazar.
--------------------------------------------------------------------------- */

type Satir =
  | { anahtar: string; zaman: number; tur: 'sos'; sos: SosCagrisi }
  | { anahtar: string; zaman: number; tur: IhbarTuru; ihbar: Ihbar }

type Props = {
  cagrilar: SosCagrisi[]
  ihbarlar: Ihbar[]
  yukleniyor: boolean
  hata: boolean
  onizleme: boolean
}

export function Bildirimlerim({ cagrilar, ihbarlar, yukleniyor, hata, onizleme }: Props) {
  const qc = useQueryClient()
  const akis = useCanliAkisDurumu((d) => d.durum)
  const [acik, setAcik] = useState<string | null>(null)

  const satirlar = useMemo<Satir[]>(
    () =>
      [
        ...cagrilar.map((c) => ({ anahtar: `sos-${c.id}`, zaman: c.zaman, tur: 'sos' as const, sos: c })),
        ...ihbarlar.map((i) => ({ anahtar: `ihb-${i.id}`, zaman: i.zaman, tur: i.tur, ihbar: i })),
      ].sort((a, b) => b.zaman - a.zaman),
    [cagrilar, ihbarlar],
  )

  return (
    <section
      aria-label="Bildirimlerim"
      className="flex min-h-40 flex-col rounded-panel border border-line bg-panel genis:min-h-0 genis:flex-1"
    >
      <header className="flex shrink-0 items-center justify-between gap-2 border-b border-line px-3.5 py-2.5">
        <h2 className="flex items-center gap-2 text-subtitle text-ink">
          <ListChecks size={20} className="text-ink-2" aria-hidden />
          {onizleme ? 'Gönderilenler' : 'Bildirimlerim'}
          {satirlar.length > 0 && <span className="text-body text-ink-3">{sayi(satirlar.length)}</span>}
        </h2>
        {akis !== 'bagli' ? (
          <button
            type="button"
            onClick={() => {
              void qc.invalidateQueries({ queryKey: ['sos'] })
              void qc.invalidateQueries({ queryKey: ['ihbar'] })
            }}
            className="h-8 rounded-control border border-line-2 px-2.5 text-small text-ink-2 hover:bg-hover"
            title="Canlı bağlantı yok; durumlar kendiliğinden değişmeyebilir"
          >
            Bağlantı yok · yenile
          </button>
        ) : (
          <span className="text-small text-ink-3">durumlar canlı</span>
        )}
      </header>

      <div className="min-h-0 flex-1 overflow-auto">
        {yukleniyor ? (
          <p className="px-3.5 py-3 text-small text-ink-3">Yükleniyor…</p>
        ) : hata ? (
          <p role="alert" className="px-3.5 py-3 text-small text-crit">
            Gönderdiklerin alınamadı. Bağlantın dönünce yenile.
          </p>
        ) : satirlar.length === 0 ? (
          <Bos />
        ) : (
          <ul>
            {satirlar.map((s) => (
              <SatirOgesi
                key={s.anahtar}
                s={s}
                acik={acik === s.anahtar}
                degistir={() => setAcik((a) => (a === s.anahtar ? null : s.anahtar))}
              />
            ))}
          </ul>
        )}
        {onizleme && satirlar.length > 0 && (
          <p className="px-3.5 py-2 text-small text-ink-3">
            Önizleme: sunucu bu role bütün kayıtları verir. Afetzede yalnız kendi gönderdiklerini görür.
          </p>
        )}
      </div>
    </section>
  )
}

function SatirOgesi({ s, acik, degistir }: { s: Satir; acik: boolean; degistir: () => void }) {
  const t = IHBAR_TURU[s.tur]
  const Ikon = IHBAR_IKONU[s.tur]
  // Ekip giderse satır ekibin durumunu gösterir: kim, kaç kişi, hangi aşamada (J-54).
  const gorevler = s.tur === 'sos' ? s.sos.gorevler : s.ihbar.gorevler
  const gelenler = (gorevler ?? []).filter(acikGorev)
  // İhbarda ekip bir kez gittiyse (bitirdi ya da gelemedi dahil) durum ekipten
  // anlatılır; eskiden yalnız açık görev bakılıyordu, ekip bitirince afetzede
  // "İhbar işlendi" görüyor, kimin geldiğini görmüyordu (J-174).
  const ekipDurumu =
    s.tur === 'sos' || (gorevler ?? []).length
      ? afetzedeDurumu(
          gorevler,
          s.tur === 'sos' ? s.sos.durum === 'kapandi' : s.ihbar.durum === 'kapandi',
          s.tur === 'sos' && s.sos.durum === 'atandi',
        )
      : null
  const durum = ekipDurumu
    ? { ad: ekipDurumu.baslik, ton: ekipDurumu.ton, aciklama: ekipDurumu.aciklama }
    : IHBAR_DURUMU[(s as Extract<Satir, { ihbar: Ihbar }>).ihbar.durum]
  const ozet =
    s.tur === 'sos'
      ? s.sos.durumSecildi === false
        ? 'Durum seçilmedi'
        : DURUM_ETIKETI[s.sos.oncelik]
      : (s.ihbar.etiket ?? '')
  const kapandi = s.tur === 'sos' ? s.sos.durum === 'kapandi' : s.ihbar.durum === 'kapandi'

  return (
    <li className={sn('border-b border-line last:border-b-0', kapandi && 'opacity-70')}>
      <button
        type="button"
        aria-expanded={acik}
        onClick={degistir}
        className="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-left hover:bg-hover"
      >
        <span aria-hidden className={sn('grid h-9 w-9 shrink-0 place-items-center rounded-control', t.soluk, t.metin)}>
          <Ikon size={20} weight="bold" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-body text-ink">
            <span className={t.metin}>{t.kisa}</span>
            {ozet ? ` · ${ozet}` : ''}
          </span>
          <span className="block font-mono text-small text-ink-3">{tarihSaat(s.zaman)}</span>
        </span>
        <Rozet ton={durum.ton}>{durum.ad}</Rozet>
        <CaretDown size={14} className={sn('shrink-0 text-ink-3', acik && 'rotate-180')} aria-hidden />
      </button>
      {acik && (
        <div className="px-3.5 pb-2.5 text-small text-ink-2">
          <p>{durum.aciklama}</p>
          {gelenler.map((g) => (
            <div key={g.id} className="mt-1.5">
              <GelenEkipKarti gorev={g} />
            </div>
          ))}
          {s.tur === 'sos' ? <SosAyrinti c={s.sos} /> : <IhbarAyrinti i={s.ihbar} />}
        </div>
      )}
    </li>
  )
}

function SosAyrinti({ c }: { c: SosCagrisi }) {
  return (
    <>
      {(c.kisiSayisi || c.ihtiyaclar?.length) && (
        <p>
          {[c.kisiSayisi ? `${sayi(c.kisiSayisi)} kişi` : null, c.ihtiyaclar?.map((i) => IHTIYAC_ADI[i] ?? i).join(', ')]
            .filter(Boolean)
            .join(' · ')}
        </p>
      )}
      {c.metin && <p className="text-ink-3">“{c.metin}”</p>}
    </>
  )
}

function IhbarAyrinti({ i }: { i: Ihbar }) {
  const hasarli = (i.tespitler ?? []).filter((t) => t.hasar).length
  return (
    <>
      {i.tur === 'fotograf' && <p>{hasarli ? `Model ${hasarli} yer işaretledi.` : 'Model hasar işaretlemedi.'}</p>}
      {i.tur === 'metin' && i.analiz && !i.analiz.ilgisiz && (
        <p>
          Model: {i.analiz.kategori}
          {i.analiz.aciliyet != null ? ` · aciliyet ${i.analiz.aciliyet}/5` : ''}
        </p>
      )}
      {i.tur === 'ihtiyac' && i.kisiSayisi ? <p>{sayi(i.kisiSayisi)} kişi</p> : null}
      {i.metin && <p className="text-ink-3">“{i.metin}”</p>}
      <p className="text-ink-3">{ihbarKonumu(i)}</p>
    </>
  )
}

/** Hiç kayıt yokken: ne olacağını ve deprem sonrası ilk adımları yazar. */
function Bos() {
  return (
    <div className="px-3.5 py-3 text-small text-ink-2">
      <p className="text-body text-ink">Henüz çağrı ya da ihbar göndermedin.</p>
      <p className="mt-0.5">
        Gönderdiklerin burada durumlarıyla görünür. Ekip atanınca ya da koordinasyon ihbarını görünce
        satır kendiliğinden değişir.
      </p>
      {/* ≥ 1600 px'te ilk adımlar duyuru sütununun altında; iki kez yazılmasın. */}
      <IlkAdimlar className="mt-3 uclu:hidden" />
    </div>
  )
}
