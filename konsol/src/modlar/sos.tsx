import { useMemo, useState } from 'react'
import { Amac, Bolum, HazirSecenekler, SuAn, Teknik, VeriYok } from '@/kabuk/Panel'
import { Micro, Rozet } from '@/kabuk/parcalar'
import { useSorguAraligi, useZaman } from '@/durum/zamanDurumu'
import { ONCELIK_ADI, ONCELIK_TON, useSosCagrilari, type SosCagrisi, sosEkBilgi } from '@/veri/sorgular'
import { acikGorev, useEkipler, useSosKapat } from '@/veri/gorev'
import { useKonsol, type SosSuzgeci } from '@/durum/konsolDurumu'
import { useHarita } from '@/harita/HaritaKabugu'
import { sayi, suredir, tarihSaat } from '@/lib/bicim'
import { sn } from '@/lib/sinif'
import { GorevOzetSatiri, SevkBolumu } from './sevk'

const SUZGECLER: ReadonlyArray<{ id: SosSuzgeci; etiket: string }> = [
  { id: 'bekleyen', etiket: 'Ekip bekleyenler' },
  { id: 'kritik', etiket: 'Yalnız kritik' },
  { id: 'atanan', etiket: 'Ekip gidenler' },
  { id: 'tum', etiket: 'Tümü' },
]

/** Süzgeç tek yerde: sol paneldeki sayı ile sağdaki liste aynı kuralı kullanır.
    Eskiden süzgeç yalnız sayıyı değiştiriyordu, liste süzülmüyordu (J-54). */
function suz(cagrilar: SosCagrisi[], suzgec: SosSuzgeci): SosCagrisi[] {
  switch (suzgec) {
    case 'bekleyen':
      return cagrilar.filter((c) => c.durum === 'bekliyor')
    case 'kritik':
      return cagrilar.filter((c) => c.oncelik === 'kritik' && c.durum !== 'kapandi')
    case 'atanan':
      return cagrilar.filter((c) => c.durum === 'atandi')
    default:
      return cagrilar
  }
}

const ONCELIK_SIRASI = { kritik: 0, yuksek: 1, orta: 2 }
const DURUM_SIRASI = { bekliyor: 0, atandi: 1, kapandi: 2 }

/** Önce ekip bekleyenler, sonra aciliyet. Bekleyenlerde en uzun bekleyen
    üstte (sıra), ötekilerde en yeni üstte. */
function sirala(a: SosCagrisi, b: SosCagrisi) {
  const durum = DURUM_SIRASI[a.durum] - DURUM_SIRASI[b.durum]
  if (durum !== 0) return durum
  const oncelik = ONCELIK_SIRASI[a.oncelik] - ONCELIK_SIRASI[b.oncelik]
  if (oncelik !== 0) return oncelik
  return a.durum === 'bekliyor' ? a.zaman - b.zaman : b.zaman - a.zaman
}

export function SosSol() {
  const suzgec = useKonsol((d) => d.sosSuzgeci)
  const suzgecSec = useKonsol((d) => d.sosSuzgeciSec)
  const aralik = useSorguAraligi()
  const sos = useSosCagrilari(aralik)
  const ekipler = useEkipler()

  const liste = sos.data ?? []
  const gorunen = suz(liste, suzgec)
  const bekleyen = liste.filter((c) => c.durum === 'bekliyor').length
  const giden = liste.filter((c) => c.durum === 'atandi').length
  const musait = ekipler.data?.filter((e) => e.musait).length

  return (
    <Bolum
      baslik="Çağrı kuyruğu"
      ek={<Micro>{sos.data ? `${sayi(gorunen.length)} / ${sayi(liste.length)}` : '—'}</Micro>}
    >
      <Amac>
        Hangi çağrıya henüz ekip gitmedi, hangisine kim gidiyor? Kuyruğu ekip durumuna göre daraltır.
      </Amac>

      <HazirSecenekler etiket="Kuyruk süzgeçleri" secenekler={SUZGECLER} secili={suzgec} onSec={suzgecSec} />

      <SuAn>
        {!sos.data
          ? 'Çağrı ucu yanıt vermiyor; kuyruk gösterilemiyor.'
          : `Seçili aralıkta ${sayi(liste.length)} çağrı: ${sayi(bekleyen)} tanesine ekip gitmedi, ${sayi(
              giden,
            )} tanesine ekip gidiyor. ${musait == null ? '' : `Şu an ${sayi(musait)} ekip müsait.`}`}
      </SuAn>

      {sos.isError && (
        <div className="mt-2">
          <VeriYok ne="SOS çağrıları" neden="çağrı ucu yanıt vermedi" />
        </div>
      )}

      {ekipler.data?.length === 0 && (
        <p className="mt-2 text-small text-ink-2">
          Kayıtlı ekip yok: sevk yapılamaz. Ekipler modunda ekip ekle.
        </p>
      )}

      <Teknik>
        Kuyruk yoklamayla değil, canlı akıştaki “yeni-sos” ve “gorev” mesajlarıyla tazelenir. Bekleyen
        çağrılarda en uzun bekleyen üstte.
      </Teknik>
    </Bolum>
  )
}

export function SosSag() {
  const aralik = useSorguAraligi()
  const sos = useSosCagrilari(aralik)
  const suzgec = useKonsol((d) => d.sosSuzgeci)
  const secili = useKonsol((d) => d.seciliKayit)
  const kayitSec = useKonsol((d) => d.kayitSec)
  const { ucus } = useHarita()

  const seciliId = secili?.tip === 'sos' ? secili.id : null
  const sirali = useMemo(() => [...(sos.data ?? [])].sort(sirala), [sos.data])
  const gorunen = useMemo(() => suz(sirali, suzgec), [sirali, suzgec])
  const seciliCagri = sirali.find((c) => c.id === seciliId) ?? null

  return (
    <>
      {seciliCagri && <SosDetayi cagri={seciliCagri} />}

      <Bolum
        baslik={SUZGECLER.find((s) => s.id === suzgec)?.etiket ?? 'Çağrılar'}
        ek={<Micro>{sayi(gorunen.length)}</Micro>}
        dolgusuz
      >
        {gorunen.length ? (
          <div>
            {gorunen.map((c) => {
              const ek = sosEkBilgi(c)
              return (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => {
                    kayitSec({ tip: 'sos', id: c.id })
                    ucus(c.lon, c.lat, 15)
                  }}
                  className={sn(
                    'block w-full border-b border-line px-3 py-2.5 text-left',
                    seciliId === c.id ? 'bg-raised' : 'hover:bg-raised',
                    c.durum === 'kapandi' && 'opacity-60',
                  )}
                >
                  <span className="flex items-baseline justify-between gap-2">
                    <span className="truncate text-small text-ink">
                      {c.mahalle ?? 'Mahalle bilinmiyor'}
                      <span className="text-ink-3"> · {tarihSaat(c.zaman)}</span>
                      {!!c.guncellemeSayisi && (
                        <span className="text-ink-3"> · {sayi(c.guncellemeSayisi)} kez yeniden gönderdi</span>
                      )}
                    </span>
                    <Rozet ton={c.durum === 'kapandi' ? 'nötr' : ONCELIK_TON[c.oncelik]}>
                      {c.durum === 'kapandi' ? 'Kapandı' : ONCELIK_ADI[c.oncelik]}
                    </Rozet>
                  </span>
                  <GorevOzetSatiri
                    gorevler={c.gorevler}
                    olayZamani={c.zaman}
                    bekleyenYaz={c.durum !== 'kapandi'}
                    eskiEkipId={c.durum === 'atandi' ? c.ekipId : null}
                  />
                  {ek.kisiIhtiyac && (
                    <span className="mt-0.5 block text-small text-ink-2">{ek.kisiIhtiyac}</span>
                  )}
                  {c.metin && (
                    <span className="mt-0.5 line-clamp-2 block text-small text-ink-3">{c.metin}</span>
                  )}
                  {ek.yaklasik && (
                    <span className="mt-0.5 block text-small text-ink">Dikkat: {ek.konum}</span>
                  )}
                </button>
              )
            })}
          </div>
        ) : (
          <div className="px-3 pb-3">
            <VeriYok
              ne="Bu süzgeçte çağrı"
              neden={sos.isError ? 'çağrı ucu yanıt vermedi' : 'seçili zaman aralığında eşleşen çağrı yok'}
            />
          </div>
        )}
      </Bolum>
    </>
  )
}

/** Seçili SOS çağrısı: ne, nerede, kaç kişi, kim gidiyor. Genel durum modu da
    aynı ayrıntıyı gösterir. */
export function SosDetayi({ cagri: c }: { cagri: SosCagrisi }) {
  const kayitSec = useKonsol((d) => d.kayitSec)
  const simdi = useZaman((z) => z.simdi)
  const { ucus } = useHarita()
  const kapat = useSosKapat()
  const [kapatSor, setKapatSor] = useState(false)
  const ek = sosEkBilgi(c)
  const kapali = c.durum === 'kapandi'
  const acik = (c.gorevler ?? []).filter(acikGorev)
  const bekliyor = suredir(c.zaman, simdi)

  return (
    <>
      <Bolum
        baslik="Seçili çağrı"
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
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-subtitle text-ink">SOS çağrısı · {c.mahalle ?? 'mahalle bilinmiyor'}</p>
            <p className="font-mono text-small text-ink-3">{c.id}</p>
          </div>
          <Rozet ton={kapali ? 'nötr' : ONCELIK_TON[c.oncelik]}>
            {kapali ? 'Kapandı' : ONCELIK_ADI[c.oncelik]}
          </Rozet>
        </div>

        <dl className="kilav-kv mt-2.5 gap-x-2.5 gap-y-1.5 text-small">
          <dt className="text-ink-3">Durum</dt>
          <dd className="text-ink">
            {kapali
              ? 'Kapandı'
              : acik.length
                ? `${acik.length} ekip gidiyor`
                : c.durum === 'atandi'
                  ? 'Ekip atanmış (eski kayıt)'
                  : `Ekip bekliyor${bekliyor ? ` · ${bekliyor}` : ''}`}
          </dd>
          {ek.kisiIhtiyac && (
            <>
              <dt className="text-ink-3">Kişi, ihtiyaç</dt>
              <dd className="text-ink">{ek.kisiIhtiyac}</dd>
            </>
          )}
          {c.metin && (
            <>
              <dt className="text-ink-3">Not</dt>
              <dd className="whitespace-pre-line text-ink">{c.metin}</dd>
            </>
          )}
          <dt className="text-ink-3">Konum</dt>
          <dd className={sn(ek.yaklasik ? 'text-ink' : 'text-ink-2')}>
            {ek.konum ?? 'Konumun kaynağı bilinmiyor'}
            <span className="block font-mono text-ink-3">
              {c.lat.toFixed(5)}, {c.lon.toFixed(5)}
            </span>
          </dd>
          <dt className="text-ink-3">Geldi</dt>
          <dd className="font-mono text-ink">{tarihSaat(c.zaman)}</dd>
          {!!c.guncellemeSayisi && (
            <>
              <dt className="text-ink-3">Yeniden gönderdi</dt>
              <dd className="text-ink">
                {sayi(c.guncellemeSayisi)} kez
                {c.sonGuncelleme ? <span className="font-mono"> · son {tarihSaat(c.sonGuncelleme)}</span> : null}
                <span className="block text-small text-ink-3">Yeni çağrı açılmadı; konum ve bilgiler güncellendi.</span>
              </dd>
            </>
          )}
        </dl>

        <div className="mt-3 flex gap-2">
          <button
            type="button"
            onClick={() => ucus(c.lon, c.lat, 15.5)}
            className="flex-1 rounded-control border border-line-2 px-3 py-2 text-body text-ink-2 hover:bg-hover hover:text-ink"
          >
            Haritada göster
          </button>
          {!kapali && !kapatSor && (
            <button
              type="button"
              onClick={() => setKapatSor(true)}
              className="rounded-control border border-line-2 px-3 py-2 text-body text-ink-2 hover:bg-hover hover:text-ink"
            >
              Çağrıyı kapat…
            </button>
          )}
        </div>
        {kapatSor && (
          <div className="mt-2 rounded-control border border-line-2 p-2 text-small">
            <p className="text-ink">
              Çağrı kapanır ve yeniden açılmaz.
              {acik.length
                ? ` Giden ${acik.length} ekibin görevi de biter (olay yerindeki "bitti", yoldaki "iptal").`
                : ''}
            </p>
            <div className="mt-2 flex gap-1.5">
              <button
                type="button"
                disabled={kapat.isPending}
                onClick={() => kapat.mutate(c.id, { onSuccess: () => setKapatSor(false) })}
                className="h-9 flex-1 rounded-control bg-accent px-2.5 text-body font-semibold text-accent-ink hover:bg-accent-deep hover:text-ink disabled:opacity-40"
              >
                Kapat
              </button>
              <button
                type="button"
                onClick={() => setKapatSor(false)}
                className="h-9 rounded-control border border-line-2 px-2.5 text-body text-ink-2 hover:bg-hover hover:text-ink"
              >
                Vazgeç
              </button>
            </div>
            {kapat.isError && (
              <p role="alert" className="mt-2 text-crit">
                {kapat.error instanceof Error ? kapat.error.message : 'Çağrı kapatılamadı.'}
              </p>
            )}
          </div>
        )}
      </Bolum>
      <SevkBolumu
        hedefTur="sos"
        hedefId={c.id}
        gorevler={c.gorevler ?? []}
        kapali={kapali}
        olayZamani={c.zaman}
        eskiEkipId={c.durum === 'atandi' ? c.ekipId : null}
      />
    </>
  )
}
