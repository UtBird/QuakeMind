import { useMemo, useState } from 'react'
import { Amac, Bolum, HazirSecenekler, InceAyar, SuAn, Teknik, VeriYok } from '@/kabuk/Panel'
import { Chip, Micro, Rozet } from '@/kabuk/parcalar'
import { useHarita } from '@/harita/HaritaKabugu'
import { sn } from '@/lib/sinif'
import {
  KANALLAR,
  KANAL_BILGI,
  KARISIM_HAZIRLARI,
  useKonsol,
  type KanalId,
} from '@/durum/konsolDurumu'
import { sayi, tarihSaat } from '@/lib/bicim'
import { useSorguAraligi } from '@/durum/zamanDurumu'
import {
  ONCELIK_ADI,
  ONCELIK_TON,
  useOzet,
  useSosCagrilari,
  type SosCagrisi,
} from '@/veri/sorgular'
import { IHBAR_TURU, useIhbarlar, type Ihbar, type IhbarTuru } from '@/veri/ihbar'
import { IhbarDetayi, IhbarSatiri, TurSimgesi } from './ihbarParcalari'
import { GorevOzetSatiri } from './sevk'
import { SosDetayi } from './sos'

/** "Son ihbarlar" satırı: SOS çağrısı ya da afetzede ihbarı (J-51). Uydu
    noktaları ihbar değildir, listede yok; ısı haritasında görünür. */
type Satir = { anahtar: string; zaman: number } & (
  | { tur: 'sos'; sos: SosCagrisi }
  | { tur: IhbarTuru; ihbar: Ihbar }
)

type Suzgec = 'tum' | 'sos' | IhbarTuru
const SUZGECLER: ReadonlyArray<{ id: Suzgec; etiket: string }> = [
  { id: 'tum', etiket: 'Tümü' },
  { id: 'sos', etiket: 'SOS' },
  { id: 'fotograf', etiket: 'Fotoğraf' },
  { id: 'metin', etiket: 'Metin' },
  { id: 'ihtiyac', etiket: 'İhtiyaç' },
]
const LISTE_BOYU = 30

/** Sunucudaki kaynak tipi → ısı kanalı. Sayım tek yerden gelir (özet ucu),
    yoksa aynı çağrı hem nokta hem çağrı olarak iki kez sayılıyor. */
const KAYNAK_KANAL: Record<string, KanalId> = { uydu: 'sat', sos: 'sos', kamera: 'cam', metin: 'nlp' }

/** Kaynak etkisi seviyeleri (J-172): eski kaydırıcı -1..1,5 arası sayı
    gösteriyordu ("×1,0"), ne demek olduğu anlaşılmıyordu. Hazır karışımların
    ara değerleri (ör. -0,6) en yakın seviyede gösterilir. */
const SEVIYELER = [
  { id: 'cikar', ad: 'Çıkar', deger: -1, aciklama: 'Bu kaynağın olduğu yeri soğutur' },
  { id: 'kapali', ad: 'Kapalı', deger: 0, aciklama: 'Bu kaynak ısıyı etkilemez' },
  { id: 'normal', ad: 'Normal', deger: 1, aciklama: 'Öteki kaynaklarla eşit katkı' },
  { id: 'guclu', ad: 'Güçlü', deger: 1.5, aciklama: 'Bu kaynak öne çıkar' },
] as const

function enYakinSeviye(w: number) {
  return SEVIYELER.reduce((en, sv) => (Math.abs(sv.deger - w) < Math.abs(en.deger - w) ? sv : en)).id
}

/** Sol panel — birleşik ısı haritası karışımı (ARAYUZ §9 sırasıyla). */
export function GenelSol() {
  const aralik = useSorguAraligi()
  const ozet = useOzet(aralik)
  const agirliklar = useKonsol((d) => d.agirliklar)
  const karisim = useKonsol((d) => d.karisim)
  const karisimSec = useKonsol((d) => d.karisimSec)
  const agirlikAyarla = useKonsol((d) => d.agirlikAyarla)

  const sayimlar = useMemo(() => {
    const s: Record<KanalId, number | null> = { sat: null, sos: null, cam: null, nlp: null }
    if (!ozet.data) return s
    for (const k of KANALLAR) s[k] = 0
    for (const [kaynak, adet] of Object.entries(ozet.data.kaynakSayilari)) {
      const kanal = KAYNAK_KANAL[kaynak]
      if (kanal) s[kanal] = adet
    }
    return s
  }, [ozet.data])

  const hazirNot = KARISIM_HAZIRLARI.find((h) => h.id === karisim)?.not
  const acikKanallar = KANALLAR.filter((k) => Math.abs(agirliklar[k]) > 0.05 && (sayimlar[k] ?? 0) > 0)

  return (
    <Bolum baslik="Birleşik ısı haritası" ek={<Micro>{karisim ? 'hazır karışım' : 'özel karışım'}</Micro>}>
      {/* 1 — amaç */}
      <Amac>
        Dört kaynaktan gelen hasar bilgisini tek haritada toplar. Kaynakların ağırlığını
        değiştirerek haritaya farklı sorular sorarsın.
      </Amac>

      {/* 2 — hazır seçenekler */}
      <HazirSecenekler
        etiket="Hazır karışımlar"
        secenekler={KARISIM_HAZIRLARI.map((h) => ({ id: h.id, etiket: h.etiket }))}
        secili={karisim}
        onSec={karisimSec}
      />

      {/* 3 — ince ayar: her kaynak ısıyı ne kadar etkilesin (J-172) */}
      <InceAyar baslik="Her kaynak ısıyı ne kadar etkilesin?">
        {KANALLAR.map((k) => {
          const bilgi = KANAL_BILGI[k]
          const n = sayimlar[k]
          const yok = n === null || n === 0
          const secili = enYakinSeviye(agirliklar[k])
          return (
            <div key={k} className="border-t border-line py-2 first:border-t-0">
              <div className="flex items-start justify-between gap-2">
                <span className="flex min-w-0 items-start gap-2">
                  <span aria-hidden className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: bilgi.renk }} />
                  <span className="min-w-0">
                    <span className="block text-small text-ink">{bilgi.ad}</span>
                    <span className="block text-small text-ink-3">{bilgi.kaynak}</span>
                  </span>
                </span>
                <span className={sn('shrink-0 text-small', yok ? 'text-ink-3' : 'text-ink-2')}>
                  {n === null ? '—' : yok ? 'bu aralıkta yok' : `${sayi(n)} nokta`}
                </span>
              </div>
              <div
                role="radiogroup"
                aria-label={`${bilgi.ad}: ısıya etkisi`}
                className={sn('mt-1.5 grid grid-cols-4 gap-1', yok && 'opacity-40')}
              >
                {SEVIYELER.map((sv) => (
                  <button
                    key={sv.id}
                    type="button"
                    role="radio"
                    aria-checked={secili === sv.id}
                    disabled={yok}
                    title={sv.aciklama}
                    onClick={() => agirlikAyarla(k, sv.deger)}
                    className={sn(
                      'rounded-control border px-1 py-1 text-small transition-colors duration-150 ease-out-qm',
                      secili === sv.id
                        ? 'border-accent bg-accent-soft text-ink'
                        : 'border-line-2 text-ink-2 hover:bg-hover hover:text-ink',
                    )}
                  >
                    {sv.ad}
                  </button>
                ))}
              </div>
            </div>
          )
        })}
        <p className="mt-1.5 text-small text-ink-3">
          <span className="text-ink-2">Normal</span> eşit katkı, <span className="text-ink-2">Güçlü</span> öne
          çıkarır, <span className="text-ink-2">Kapalı</span> yok sayar, <span className="text-ink-2">Çıkar</span>{' '}
          o kaynağın olduğu yeri soğutur (ör. sessiz bölgeler: uydu yıkık gösteriyor ama çağrı yok).
        </p>
      </InceAyar>

      <div className="mt-3">
        <div
          aria-label="Isı ölçeği: düşükten yükseğe"
          role="img"
          className="h-2 rounded-badge"
          style={{
            background:
              'linear-gradient(90deg, var(--heat-0) 0%, var(--heat-1) 18%, var(--heat-2) 42%, var(--heat-3) 63%, var(--heat-4) 82%, var(--heat-5) 100%)',
          }}
        />
        <div className="mt-1 flex justify-between">
          <Micro>yok</Micro>
          <Micro>yoğun</Micro>
        </div>
      </div>

      {/* 4 — şu an ne görüyorum */}
      <SuAn>
        {hazirNot ??
          (acikKanallar.length
            ? `Haritayı ${acikKanallar.map((k) => KANAL_BILGI[k].ad.toLocaleLowerCase('tr')).join(', ')} oluşturuyor.`
            : 'Isı haritası için veri yok; ağırlıklar veri geldiğinde etkili olur.')}
      </SuAn>

      {ozet.isError && (
        <div className="mt-2">
          <VeriYok ne="Isı kanalları" neden="özet ucu yanıt vermedi" />
        </div>
      )}

      {/* 5 — teknik not en altta */}
      <Teknik>
        Ağırlık değişince sunucuya istek gitmez. Her kaynağın yoğunluk ızgarası sunucuda bir kez
        hesaplanır, ağırlıklı karışım ekran kartında yapılır; ölçek mutlaktır, harita kaydırınca
        renkler kaymaz.
      </Teknik>
    </Bolum>
  )
}

/** Sağ panel — bölge durumu. Sayılar sunucudan gelir, istemci hesap yapmaz. */
export function GenelSag() {
  const aralik = useSorguAraligi()
  const ozet = useOzet(aralik)
  const sos = useSosCagrilari(aralik)
  const ihbar = useIhbarlar(aralik)
  const secili = useKonsol((d) => d.seciliKayit)
  const kayitSec = useKonsol((d) => d.kayitSec)
  const { ucus } = useHarita()
  const [suzgec, setSuzgec] = useState<Suzgec>('tum')

  // Son ihbarlar, en yeni önce: tıklayınca haritada oraya gidilir (J-41).
  // Canlı akışla gelen SOS ve ihbar listeye anında düşer (J-51).
  const satirlar = useMemo<Satir[]>(() => {
    const cagrilar: Satir[] = (sos.data ?? []).map((c) => ({
      anahtar: `sos-${c.id}`,
      zaman: c.zaman,
      tur: 'sos',
      sos: c,
    }))
    const ihbarlar: Satir[] = (ihbar.data ?? []).map((i) => ({
      anahtar: `ihb-${i.id}`,
      zaman: i.zaman,
      tur: i.tur,
      ihbar: i,
    }))
    return [...cagrilar, ...ihbarlar].sort((a, b) => b.zaman - a.zaman)
  }, [sos.data, ihbar.data])

  const sayilar = useMemo(() => {
    const s: Record<Suzgec, number> = { tum: satirlar.length, sos: 0, fotograf: 0, metin: 0, ihtiyac: 0 }
    for (const x of satirlar) s[x.tur] += 1
    return s
  }, [satirlar])
  const gorunen = (suzgec === 'tum' ? satirlar : satirlar.filter((x) => x.tur === suzgec)).slice(0, LISTE_BOYU)

  const seciliCagri =
    secili?.tip === 'sos' ? (sos.data ?? []).find((c) => c.id === secili.id) : undefined
  const seciliIhbar =
    secili?.tip === 'ihbar' ? (ihbar.data ?? []).find((i) => i.id === secili.id) : undefined

  // Yüklenirken "veri yok" yazılmaz (J-174): o, sorgunun hata verdiği anlamına gelir.
  const yok = (q: { isError: boolean }) => (q.isError ? 'veri yok' : 'yükleniyor…')
  const kartlar: Array<[string, string, string]> = [
    [
      'Yıkık yapı',
      ozet.data ? sayi(ozet.data.yikikYapi) : '—',
      ozet.data ? `${sayi(ozet.data.hasarliYapi)} yapı da hasarlı` : yok(ozet),
    ],
    [
      'Kapalı yol',
      ozet.data ? sayi(ozet.data.hasarliYol) : '—',
      ozet.data ? 'uydu analizinden gelen kapanma' : yok(ozet),
    ],
    [
      'Bekleyen SOS',
      ozet.data ? sayi(ozet.data.bekleyenSos) : '—',
      ozet.data ? `${sayi(ozet.data.atananSos)} çağrıya ekip gidiyor` : yok(ozet),
    ],
    [
      'Yeni ihbar',
      ihbar.data ? sayi(ihbar.data.filter((i) => i.durum === 'yeni').length) : '—',
      ihbar.data ? `aralıkta ${sayi(ihbar.data.length)} ihbar` : yok(ihbar),
    ],
    // Ekipler şu anki durumuyla (zaman aralığından bağımsız, J-54).
    [
      'Görevdeki ekip',
      ozet.data?.ekipSayisi != null ? `${sayi(ozet.data.gorevdekiEkip ?? 0)} / ${sayi(ozet.data.ekipSayisi)}` : '—',
      ozet.data?.ekipSayisi != null ? `${sayi(ozet.data.musaitEkip ?? 0)} ekip müsait` : yok(ozet),
    ],
    [
      'Sahadaki kişi',
      ozet.data?.sahadakiKisi != null ? sayi(ozet.data.sahadakiKisi) : '—',
      ozet.data?.sahadakiKisi != null ? 'açık görevlere giden' : yok(ozet),
    ],
  ]

  return (
    <>
      <div className="grid grid-cols-2 gap-px bg-line">
        {kartlar.map(([etiket, deger, alt]) => (
          <div key={etiket} className="bg-panel px-3.5 py-3.5">
            <div className="font-cond text-metric text-ink">{deger}</div>
            <div className="mt-1 text-micro ls-micro text-ink-3 uppercase">{etiket}</div>
            <div className="mt-1 text-small text-ink-3">{alt}</div>
          </div>
        ))}
      </div>
      {seciliCagri && <SosDetayi cagri={seciliCagri} />}
      {seciliIhbar && <IhbarDetayi ihbar={seciliIhbar} />}

      <Bolum baslik="Son ihbarlar" ek={<Micro>{sayi(satirlar.length)}</Micro>} dolgusuz>
        <div role="group" aria-label="İhbar türü" className="flex flex-wrap gap-1.5 px-3 pb-2.5">
          {SUZGECLER.map((s) => (
            <Chip key={s.id} secili={suzgec === s.id} onClick={() => setSuzgec(s.id)}>
              {s.id !== 'tum' && (
                <span
                  aria-hidden
                  className={sn('mr-1.5 inline-block h-2 w-2 rounded-badge', IHBAR_TURU[s.id].zemin)}
                />
              )}
              {s.etiket} {sayi(sayilar[s.id])}
            </Chip>
          ))}
        </div>
        {gorunen.length ? (
          <div className="border-t border-line">
            {gorunen.map((x) =>
              x.tur === 'sos' ? (
                <SosSatiri
                  key={x.anahtar}
                  c={x.sos}
                  secili={seciliCagri?.id === x.sos.id}
                  onSec={() => {
                    kayitSec({ tip: 'sos', id: x.sos.id })
                    ucus(x.sos.lon, x.sos.lat, 15.5)
                  }}
                />
              ) : (
                <IhbarSatiri
                  key={x.anahtar}
                  ihbar={x.ihbar}
                  secili={seciliIhbar?.id === x.ihbar.id}
                  onSec={() => {
                    kayitSec({ tip: 'ihbar', id: x.ihbar.id })
                    ucus(x.ihbar.lon, x.ihbar.lat, 15.5)
                  }}
                />
              ),
            )}
          </div>
        ) : (
          <div className="px-3 py-2">
            <VeriYok ne="İhbar" neden="seçili zaman aralığında kayıt yok" />
          </div>
        )}
      </Bolum>

      <Bolum baslik="Bölge durumu">
        <Amac>Seçili zaman aralığında bölgenin özeti: ne kadar hasar, kaç bekleyen çağrı?</Amac>
        {ozet.isError && (
          <div className="mt-2">
            <VeriYok ne="Bölge özeti" neden="/api/ozet ucu henüz bağlı değil" />
          </div>
        )}
        <Teknik>
          Bu sayılar sunucuda hazır tutulur; istek anında hesaplanmaz. Canlı modda yeni çağrı ve
          ihbar, canlı akış mesajıyla listeye anında düşer; sorgular dakikada bir yenilenmez.
        </Teknik>
      </Bolum>
    </>
  )
}

function SosSatiri({ c, secili, onSec }: { c: SosCagrisi; secili: boolean; onSec: () => void }) {
  const kapali = c.durum === 'kapandi'
  return (
    <button
      type="button"
      onClick={onSec}
      aria-pressed={secili}
      className={sn(
        'flex w-full items-start gap-2.5 border-b border-line px-3 py-2.5 text-left',
        secili ? 'bg-raised' : 'hover:bg-raised',
        c.durum === 'kapandi' && 'opacity-60',
      )}
    >
      <TurSimgesi tur="sos" />
      <span className="min-w-0 flex-1">
        <span className="flex items-baseline justify-between gap-2">
          <span className="truncate text-small text-ink">
            <span className="text-ihbar-sos">SOS</span>
            {c.mahalle ? ` · ${c.mahalle}` : ''}
          </span>
          <Rozet ton={kapali ? 'nötr' : ONCELIK_TON[c.oncelik]}>{kapali ? 'Kapandı' : ONCELIK_ADI[c.oncelik]}</Rozet>
        </span>
        <GorevOzetSatiri
          gorevler={c.gorevler}
          olayZamani={c.zaman}
          bekleyenYaz={!kapali}
          eskiEkipId={c.durum === 'atandi' ? c.ekipId : null}
        />
        <span className="mt-0.5 flex justify-between gap-2 text-small text-ink-3">
          <span className="line-clamp-1">{c.metin ?? c.id}</span>
          <span className="shrink-0 font-mono">{tarihSaat(c.zaman)}</span>
        </span>
      </span>
    </button>
  )
}
