import { useMemo, type ReactNode } from 'react'
import { Amac, Bolum, VeriYok } from '@/kabuk/Panel'
import { Micro, Rozet } from '@/kabuk/parcalar'
import { IsaretliFoto, TespitListesi } from '@/kabuk/IsaretliFoto'
import { useHarita } from '@/harita/HaritaKabugu'
import { useKonsol } from '@/durum/konsolDurumu'
import { useSorguAraligi } from '@/durum/zamanDurumu'
import { sn } from '@/lib/sinif'
import { sayi, tarihSaat } from '@/lib/bicim'
import { IHTIYAC_ADI } from '@/veri/sorgular'
import {
  FOTOGRAF_MODELI,
  IHBAR_DURUMU,
  IHBAR_TURU,
  ihbarKonumu,
  useIhbarDurum,
  useIhbarFotografi,
  useIhbarlar,
  type Ihbar,
  type IhbarTuru,
} from '@/veri/ihbar'
import { IHBAR_IKONU, IHTIYAC_IKONU } from '@/veri/ihbarIkon'
import { acikGorev } from '@/veri/gorev'
import { GorevOzetSatiri, SevkBolumu } from './sevk'

/* Konsolda afetzede ihbarının satırı ve ayrıntısı (J-51). Genel durum, kamera,
   metin ve ihtiyaç modları aynı parçaları kullanır: aynı ihbar her yerde aynı
   renkle, aynı adla ve aynı düğmelerle görünür. */

const BILDIRILEN_ACILIYET = {
  LOW: { ad: 'Düşük', ton: 'nötr' },
  MEDIUM: { ad: 'Orta', ton: 'mid' },
  HIGH: { ad: 'Yüksek', ton: 'high' },
  CRITICAL: { ad: 'Kritik', ton: 'crit' },
} as const

const ACILIYET_TONU = (n: number) => (n >= 5 ? 'crit' : n >= 4 ? 'high' : n >= 3 ? 'mid' : 'ok')

/** Türün renkli simgesi. Renk tek başına anlam taşımaz; yanında ad yazılır. */
export function TurSimgesi({ tur, boy = 'kucuk' }: { tur: IhbarTuru | 'sos'; boy?: 'kucuk' | 'buyuk' }) {
  const t = IHBAR_TURU[tur]
  const Ikon = IHBAR_IKONU[tur]
  return (
    <span
      aria-hidden
      className={sn(
        'grid shrink-0 place-items-center rounded-control',
        t.soluk,
        t.metin,
        boy === 'buyuk' ? 'h-9 w-9' : 'h-7 w-7',
      )}
    >
      <Ikon size={boy === 'buyuk' ? 20 : 16} weight="bold" />
    </span>
  )
}

/** Satırın alt yazısı: türüne göre en çok işe yarayan bilgi. */
function altYazi(i: Ihbar): string {
  if (i.tur === 'ihtiyac') {
    const kisi = i.kisiSayisi ? `${sayi(i.kisiSayisi)} kişi` : null
    return [kisi, i.mahalle, i.metin].filter(Boolean).join(' · ')
  }
  if (i.tur === 'metin') return i.metin ?? ''
  const tespit = (i.tespitler ?? []).filter((t) => t.hasar).length
  return [tespit ? `${tespit} işaret` : 'model işaretlemedi', i.mahalle, i.metin].filter(Boolean).join(' · ')
}

export function IhbarSatiri({
  ihbar,
  secili,
  onSec,
}: {
  ihbar: Ihbar
  secili: boolean
  onSec: () => void
}) {
  const t = IHBAR_TURU[ihbar.tur]
  const d = IHBAR_DURUMU[ihbar.durum]
  return (
    <button
      type="button"
      onClick={onSec}
      aria-pressed={secili}
      className={sn(
        'flex w-full items-start gap-2.5 border-b border-line px-3 py-2.5 text-left',
        secili ? 'bg-raised' : 'hover:bg-raised',
        ihbar.durum === 'kapandi' && 'opacity-60',
      )}
    >
      <TurSimgesi tur={ihbar.tur} />
      <span className="min-w-0 flex-1">
        <span className="flex items-baseline justify-between gap-2">
          <span className="truncate text-small text-ink">
            <span className={t.metin}>{t.kisa}</span>
            {(ihbar.bildirilenKategoriAdi ?? ihbar.etiket) && ` · ${ihbar.bildirilenKategoriAdi ?? ihbar.etiket}`}
          </span>
          {ihbar.bildirilenAciliyet && (
            <Rozet ton={BILDIRILEN_ACILIYET[ihbar.bildirilenAciliyet].ton}>
              {BILDIRILEN_ACILIYET[ihbar.bildirilenAciliyet].ad}
            </Rozet>
          )}
          <Rozet ton={d.ton}>{d.ad}</Rozet>
        </span>
        <GorevOzetSatiri gorevler={ihbar.gorevler} olayZamani={ihbar.zaman} bekleyenYaz={false} />
        <span className="mt-0.5 flex justify-between gap-2 text-small text-ink-3">
          <span className="line-clamp-1">{altYazi(ihbar)}</span>
          <span className="shrink-0 font-mono">{tarihSaat(ihbar.zaman)}</span>
        </span>
      </span>
    </button>
  )
}

/** Seçili ihbarın ayrıntısı ve işlem düğmeleri. */
export function IhbarDetayi({ ihbar }: { ihbar: Ihbar }) {
  const { ucus } = useHarita()
  const kayitSec = useKonsol((d) => d.kayitSec)
  const durum = useIhbarDurum()
  const t = IHBAR_TURU[ihbar.tur]
  const d = IHBAR_DURUMU[ihbar.durum]
  const giden = (ihbar.gorevler ?? []).filter(acikGorev).length

  return (
    <>
      <Bolum
        baslik="Seçili ihbar"
        ek={
          <button
            type="button"
            onClick={() => kayitSec(null)}
            className="text-small text-ink-3 hover:text-ink"
          >
            Kapat
          </button>
        }
      >
        <div className="flex items-center gap-2.5">
          <TurSimgesi tur={ihbar.tur} boy="buyuk" />
          <div className="min-w-0 flex-1">
            <p className={sn('text-subtitle', t.metin)}>{t.ad}</p>
            <p className="truncate text-small text-ink-2">{ihbar.etiket ?? '—'}</p>
          </div>
          <Rozet ton={d.ton}>{d.ad}</Rozet>
        </div>

        <div className="mt-3">
          {ihbar.tur === 'fotograf' && <FotografAyrintisi ihbar={ihbar} />}
          {ihbar.tur === 'metin' && <MetinAyrintisi ihbar={ihbar} />}
          {ihbar.tur === 'ihtiyac' && <IhtiyacAyrintisi ihbar={ihbar} />}
        </div>

        <dl className="kilav-kv mt-3 gap-x-2.5 gap-y-1.5 text-small">
          {ihbar.tur !== 'metin' && ihbar.metin && (
            <Satir ad="Not">
              <span className="whitespace-pre-line">{ihbar.metin}</span>
            </Satir>
          )}
          {ihbar.bildirilenKategoriAdi && <Satir ad="Bildirilen kategori">{ihbar.bildirilenKategoriAdi}</Satir>}
          {ihbar.bildirilenAciliyet && (
            <Satir ad="Bildirilen aciliyet">{BILDIRILEN_ACILIYET[ihbar.bildirilenAciliyet].ad}</Satir>
          )}
          {ihbar.mahsurSayisi != null && <Satir ad="Bildirilen mahsur">{sayi(ihbar.mahsurSayisi)}</Satir>}
          {ihbar.yaraliSayisi != null && <Satir ad="Bildirilen yaralı">{sayi(ihbar.yaraliSayisi)}</Satir>}
          <Satir ad="Konum">{ihbarKonumu(ihbar)}</Satir>
          <Satir ad="Zaman">
            <span className="font-mono">{tarihSaat(ihbar.zaman)}</span>
          </Satir>
          <Satir ad="Durum">
            {d.ad}
            {ihbar.isleyenAd ? ` · ${ihbar.isleyenAd}` : ''}
            {ihbar.guncellendi ? ` · ${tarihSaat(ihbar.guncellendi)}` : ''}
          </Satir>
          <Satir ad="Kimlik">
            <span className="font-mono">{ihbar.id}</span>
          </Satir>
        </dl>

        <div className="mt-3 grid grid-cols-3 gap-1.5">
          <button
            type="button"
            disabled={ihbar.durum !== 'yeni' || durum.isPending}
            onClick={() => durum.mutate({ id: ihbar.id, durum: 'goruldu' })}
            className="rounded-control border border-line-2 px-2 py-2 text-body text-ink hover:bg-hover disabled:opacity-40"
          >
            Gördüm
          </button>
          <button
            type="button"
            disabled={ihbar.durum === 'kapandi' || durum.isPending}
            onClick={() => durum.mutate({ id: ihbar.id, durum: 'kapandi' })}
            className="rounded-control border border-line-2 px-2 py-2 text-body text-ink hover:bg-hover disabled:opacity-40"
          >
            {ihbar.tur === 'ihtiyac' ? 'Karşılandı' : 'Kapat'}
          </button>
          <button
            type="button"
            onClick={() => ucus(ihbar.lon, ihbar.lat, 16)}
            className="rounded-control border border-line-2 px-2 py-2 text-body text-ink-2 hover:bg-hover hover:text-ink"
          >
            Haritada
          </button>
        </div>
        {durum.isError && (
          <p role="alert" className="mt-2 text-small text-crit">
            {durum.error instanceof Error ? durum.error.message : 'Durum değiştirilemedi.'}
          </p>
        )}
        <p className="mt-2 text-small text-ink-3">
          "Gördüm" afetzedenin ekranında "Görüldü" olarak görünür; kapatılan ihbar yeniden açılmaz.
          {giden ? ` Kapatınca giden ${giden} ekibin görevi de biter.` : ''}
        </p>
      </Bolum>
      <SevkBolumu
        hedefTur="ihbar"
        hedefId={ihbar.id}
        gorevler={ihbar.gorevler ?? []}
        kapali={ihbar.durum === 'kapandi'}
        olayZamani={ihbar.zaman}
      />
    </>
  )
}

function Satir({ ad, children }: { ad: string; children: ReactNode }) {
  return (
    <>
      <dt className="text-ink-3">{ad}</dt>
      <dd className="text-ink">{children}</dd>
    </>
  )
}

function FotografAyrintisi({ ihbar }: { ihbar: Ihbar }) {
  const foto = useIhbarFotografi(ihbar.fotografVar ? ihbar.id : null)
  const tespitler = ihbar.tespitler ?? []
  const hasarli = tespitler.filter((t) => t.hasar)
  return (
    <>
      {foto.data ? (
        <IsaretliFoto veri={foto.data.veri} en={foto.data.en} boy={foto.data.boy} tespitler={tespitler} />
      ) : (
        <div className="grid h-40 place-items-center rounded-control bg-sunken text-small text-ink-3">
          {foto.isError ? 'Fotoğraf alınamadı.' : 'Fotoğraf yükleniyor…'}
        </div>
      )}
      <p className="mt-2 text-small text-ink-2">
        Afetzedenin seçtiği model: {ihbar.model ? FOTOGRAF_MODELI[ihbar.model].ad : '—'}.{' '}
        {hasarli.length ? `${hasarli.length} yer işaretledi.` : 'Model hasar işaretlemedi; fotoğrafa bakın.'}
      </p>
      <div className="mt-1">
        <TespitListesi tespitler={tespitler} />
      </div>
      <p className="mt-1.5 text-small text-ink-3">
        Modelin tahminidir; sahada doğrulanmadı. Model mAP değeri henüz ölçülmedi.
      </p>
    </>
  )
}

function MetinAyrintisi({ ihbar }: { ihbar: Ihbar }) {
  const a = ihbar.analiz
  return (
    <>
      <blockquote className="rounded-control border border-line-2 bg-sunken px-2.5 py-2 text-body whitespace-pre-line text-ink">
        {ihbar.metin}
      </blockquote>
      {!a ? (
        <p className="mt-2 text-small text-ink-2">Model incelemedi (afetzede incelemeden gönderdi).</p>
      ) : a.ilgisiz ? (
        <p className="mt-2 text-small text-ink-2">Model bu metni afetle ilgisiz buldu; afetzede yine de gönderdi.</p>
      ) : (
        <dl className="kilav-kv mt-2 gap-x-2.5 gap-y-1.5 text-small">
          <Satir ad="Kategori">{a.kategori ?? '—'}</Satir>
          <Satir ad="Aciliyet">
            {a.aciliyet != null ? <Rozet ton={ACILIYET_TONU(a.aciliyet)}>{`${a.aciliyet}/5`}</Rozet> : '—'}
          </Satir>
          <Satir ad="Model güveni">{a.guven != null ? `%${Math.round(a.guven * 100)}` : '—'}</Satir>
          <Satir ad="Adres">{a.konumMetin ?? 'metinde adres bulunamadı'}</Satir>
        </dl>
      )}
    </>
  )
}

function IhtiyacAyrintisi({ ihbar }: { ihbar: Ihbar }) {
  return (
    <>
      <ul className="flex flex-wrap gap-1.5">
        {(ihbar.ihtiyaclar ?? []).map((i) => {
          const Ikon = IHTIYAC_IKONU[i]
          return (
            <li
              key={i}
              className="flex items-center gap-1.5 rounded-control border border-ihbar-ihtiyac px-2 py-1 text-body text-ink"
            >
              <Ikon size={16} className="text-ihbar-ihtiyac" aria-hidden />
              {IHTIYAC_ADI[i]}
            </li>
          )
        })}
      </ul>
      <p className="mt-2 text-small text-ink-2">
        {ihbar.kisiSayisi ? `${sayi(ihbar.kisiSayisi)} kişi için.` : 'Kişi sayısı yazılmadı.'}
      </p>
    </>
  )
}

/** Liste başlığı: sayı ve "yeni" sayısı. */
export function IhbarSayaci({ liste }: { liste: Ihbar[] }) {
  const yeni = liste.filter((i) => i.durum === 'yeni').length
  return (
    <Micro>
      {sayi(liste.length)} ihbar{yeni ? ` · ${sayi(yeni)} yeni` : ''}
    </Micro>
  )
}

/** Bir türün afetzedelerden gelen ihbarları: modun "uygun yeri" (J-51).
    Kamera modunda fotoğraflar, metin modunda yazılı ihbarlar, ihtiyaç
    modunda talepler. Yeni olan önce; canlı akışla anında düşer. */
export function GelenIhbarlar({
  tur,
  baslik,
  amac,
  suz,
  sinir = 20,
}: {
  tur: IhbarTuru
  baslik: string
  amac: string
  suz?: (i: Ihbar) => boolean
  sinir?: number
}) {
  const aralik = useSorguAraligi()
  const ihbar = useIhbarlar(aralik)
  const secili = useKonsol((d) => d.seciliKayit)
  const kayitSec = useKonsol((d) => d.kayitSec)
  const { ucus } = useHarita()

  const liste = useMemo(
    () =>
      (ihbar.data ?? [])
        .filter((i) => i.tur === tur && (!suz || suz(i)))
        // Önce işlenmemişler, sonra en yeni.
        .sort((a, b) => Number(a.durum === 'kapandi') - Number(b.durum === 'kapandi') || b.zaman - a.zaman),
    [ihbar.data, tur, suz],
  )
  const seciliIhbar =
    secili?.tip === 'ihbar' ? liste.find((i) => i.id === secili.id) : undefined

  return (
    <>
      {seciliIhbar && <IhbarDetayi ihbar={seciliIhbar} />}
      <Bolum baslik={baslik} ek={<IhbarSayaci liste={liste} />} dolgusuz>
        <div className="px-3 pb-2.5">
          <Amac>{amac}</Amac>
        </div>
        {ihbar.isError ? (
          <div className="px-3 pb-3">
            <VeriYok ne="İhbarlar" neden="ihbar ucu yanıt vermedi" />
          </div>
        ) : liste.length ? (
          <div className="border-t border-line">
            {liste.slice(0, sinir).map((i) => (
              <IhbarSatiri
                key={i.id}
                ihbar={i}
                secili={seciliIhbar?.id === i.id}
                onSec={() => {
                  kayitSec({ tip: 'ihbar', id: i.id })
                  ucus(i.lon, i.lat, 16)
                }}
              />
            ))}
          </div>
        ) : (
          <p className="border-t border-line px-3 py-2.5 text-small text-ink-3">
            {ihbar.isPending ? 'Yükleniyor…' : 'Seçili zaman aralığında bu türde ihbar yok.'}
          </p>
        )}
      </Bolum>
    </>
  )
}
