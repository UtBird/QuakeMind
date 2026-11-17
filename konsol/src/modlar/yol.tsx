import { useEffect, useMemo, useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Crosshair, WarningCircle } from '@phosphor-icons/react'
import { Amac, Bolum, HazirSecenekler, InceAyar, SuAn, Teknik, VeriYok } from '@/kabuk/Panel'
import { Anahtar, Micro } from '@/kabuk/parcalar'
import { ApiHatasi, apiPost } from '@/veri/istemci'
import { useHarita } from '@/harita/HaritaKabugu'
import { useSorguAraligi } from '@/durum/zamanDurumu'
import { useRota, type RotaSorusu } from '@/durum/rotaDurumu'
import { useEkipler, useSosCagrilari, ONCELIK_ADI } from '@/veri/sorgular'
import { useIhbarlar, ihbarBasligi } from '@/veri/ihbar'
import { useKapanmalar } from '@/veri/katman'
import {
  MANEVRA_ADI,
  useRotaKunyesi,
  type EnYakinYaniti,
  type Guzergah,
} from '@/veri/guzergah'
import { mesafe, sayi, tarihSaat } from '@/lib/bicim'
import { sn } from '@/lib/sinif'

/* ---------------------------------------------------------------------------
   Yol ve rota (J-171). Araç rotası sunucuda, kendi yol ağımızda hesaplanır
   (arac_rotasi.py): tek yönlere, göbeklere ve OSM dönüş yasaklarına uyar, yol
   ortasında U dönüşü yapmaz, sola dönüşü sağa dönüşten pahalı sayar, bilinen
   kapanma ve hasar noktalarından kaçınır. Sevk ve saha ekranları aynı motoru
   kullanır: burada görülen rota ekibin göreceği rotadır.
--------------------------------------------------------------------------- */

const SORULAR: ReadonlyArray<{ id: RotaSorusu; etiket: string }> = [
  { id: 'nokta', etiket: 'İki nokta arası' },
  { id: 'ekip', etiket: 'Ekipten olaya' },
  { id: 'hastane', etiket: 'En yakın hastane' },
  { id: 'toplanma', etiket: 'En yakın toplanma alanı' },
  { id: 'kapali', etiket: 'Kapalı yollar' },
]

const GIRDI = 'mt-1 w-full rounded-control border border-line-2 bg-sunken px-2 py-1.5 text-body text-ink'

function hataMetni(e: unknown): string {
  if (e instanceof ApiHatasi) return e.message
  return e instanceof Error ? e.message : 'Rota hesaplanamadı.'
}

/** Rota isteği: kaçınma açıksa aynı rota kaçınmadan da istenir (farkı göstermek için). */
function useRotaHesabi() {
  const { bas, hedef, kacin, sonucYaz } = useRota()
  return useMutation({
    mutationFn: async () => {
      if (!bas || !hedef) throw new Error('Başlangıç ve hedef seçilmedi.')
      const govde = { basLon: bas.lon, basLat: bas.lat, hedefLon: hedef.lon, hedefLat: hedef.lat }
      const [ana, kiyas] = await Promise.all([
        apiPost<Guzergah>('/api/guzergah', { ...govde, kacin }),
        kacin ? apiPost<Guzergah>('/api/guzergah', { ...govde, kacin: false }).catch(() => null) : null,
      ])
      return { ana, kiyas }
    },
    onSuccess: ({ ana, kiyas }) => sonucYaz(ana, kiyas),
  })
}

function useEnYakinHesabi() {
  const { bas, kacin, soru, adaylarYaz } = useRota()
  return useMutation({
    mutationFn: () => {
      if (!bas) throw new Error('Başlangıç seçilmedi.')
      return apiPost<EnYakinYaniti>('/api/guzergah/en-yakin', {
        basLon: bas.lon,
        basLat: bas.lat,
        tur: soru === 'toplanma' ? 'toplanma' : 'hastane',
        kacin,
      })
    },
    onSuccess: (y) => adaylarYaz(y.yerler, y.kaynak),
  })
}

export function YolSol() {
  const d = useRota()
  const rota = useRotaHesabi()
  const enYakin = useEnYakinHesabi()
  const { ucus } = useHarita()

  // Noktalar tamamlanınca rota kendiliğinden hesaplanır (düğmeye ayrıca basmadan).
  const iki = d.soru === 'nokta' || d.soru === 'ekip'
  const tek = d.soru === 'hastane' || d.soru === 'toplanma'
  const rotaRef = useRef(rota)
  rotaRef.current = rota
  const enYakinRef = useRef(enYakin)
  enYakinRef.current = enYakin
  useEffect(() => {
    if (iki && d.bas && d.hedef && !d.sonuc) rotaRef.current.mutate()
  }, [iki, d.bas, d.hedef, d.kacin, d.sonuc])
  useEffect(() => {
    if (tek && d.bas && !d.adaylar) enYakinRef.current.mutate()
  }, [tek, d.bas, d.kacin, d.adaylar])

  const hata = rota.isError ? rota.error : enYakin.isError ? enYakin.error : null
  const bekliyor = rota.isPending || enYakin.isPending

  return (
    <Bolum baslik="Yol ve rota">
      <Amac>
        Ekip oraya hangi yoldan, kaç dakikada gider? Tek yönlere, göbeklere ve dönüş yasaklarına
        uyan, bilinen kapanmalardan kaçan araç rotasını çıkarır.
      </Amac>

      <HazirSecenekler etiket="Rota soruları" secenekler={SORULAR} secili={d.soru} onSec={d.soruSec} />

      {d.soru === 'nokta' && (
        <div className="mt-3 grid min-w-0 gap-2">
          <NoktaSatiri hangi="bas" etiket="Başlangıç" />
          <NoktaSatiri hangi="hedef" etiket="Hedef" />
        </div>
      )}
      {d.soru === 'ekip' && <EkiptenOlaya />}
      {tek && (
        <div className="mt-3 grid min-w-0 gap-2">
          <NoktaSatiri hangi="bas" etiket="Nereden" />
          <EkipSecimi etiket="ya da bir ekibin konumundan" />
        </div>
      )}
      {d.soru === 'kapali' && <KapaliYollar ucus={ucus} />}

      {d.soru !== 'kapali' && (
        <InceAyar baslik="Rota kuralları">
          <Anahtar
            acik={d.kacin}
            etiket="Hasarlı ve kapalı yollardan kaçın"
            onDegis={() => d.kacinYaz(!d.kacin)}
          />
        </InceAyar>
      )}

      {hata != null && (
        <p role="alert" className="mt-2 text-small text-crit">
          {hataMetni(hata)}
        </p>
      )}

      {d.soru !== 'kapali' && (
        <SuAn>
          {bekliyor
            ? 'Rota hesaplanıyor…'
            : d.secim
              ? `Haritaya tıkla: ${d.secim === 'bas' ? 'başlangıç' : 'hedef'} noktası seçiliyor.`
              : d.sonuc
                ? `~${d.sonuc.sureDk} dk, yoldan ${mesafe(d.sonuc.mesafeM)}; ayrıntı sağda.`
                : tek
                  ? 'Başlangıcı seç; en yakın üç yer yoldan sıralanır.'
                  : 'Başlangıç ve hedefi seç; rota kendiliğinden çıkar.'}
        </SuAn>
      )}

      <Teknik>
        Rota sunucuda, kendi yol ağımızda (OpenStreetMap) kenar tabanlı Dijkstra ile hesaplanır: tek
        yön, göbek ve OSM dönüş yasakları uygulanır, yol ortasında U dönüşü yapılmaz, sola dönüş
        sağa dönüşten pahalıdır. Kapanmadaki yol 20 kat, hasar noktasına yakın yol daha pahalı
        sayılır; başka yol yoksa rota yine bulunur ve bunu söyler. Hızlar yol türüne göre ortalama
        varsayımdır; trafik verisi yok. Sevk ve saha ekranları aynı rotayı kullanır.
      </Teknik>
    </Bolum>
  )
}

function NoktaSatiri({ hangi, etiket }: { hangi: 'bas' | 'hedef'; etiket: string }) {
  const { secim, secimAc, noktaYaz } = useRota()
  const nokta = useRota((d) => d[hangi])
  const acik = secim === hangi
  return (
    <div className="min-w-0">
      <Micro>{etiket}</Micro>
      <div className="mt-1 flex items-center gap-1.5">
        <span className={sn('min-w-0 flex-1 truncate text-small', nokta ? 'text-ink' : 'text-ink-3')}>
          {nokta?.ad ?? 'seçilmedi'}
        </span>
        <button
          type="button"
          aria-pressed={acik}
          onClick={() => secimAc(acik ? null : hangi)}
          className={sn(
            'flex shrink-0 items-center gap-1 rounded-control border px-2 py-1 text-small',
            acik ? 'border-accent bg-accent-soft text-ink' : 'border-line-2 text-ink-2 hover:bg-hover hover:text-ink',
          )}
        >
          <Crosshair size={14} aria-hidden />
          {acik ? 'Haritaya tıkla…' : 'Haritada seç'}
        </button>
        {nokta && (
          <button
            type="button"
            onClick={() => noktaYaz(hangi, null)}
            className="shrink-0 text-small text-ink-3 hover:text-ink"
          >
            Sil
          </button>
        )}
      </div>
    </div>
  )
}

function EkipSecimi({ etiket }: { etiket: string }) {
  const ekipler = useEkipler()
  const { noktaYaz } = useRota()
  const konumlu = (ekipler.data ?? []).filter((e) => e.lon != null && e.lat != null)
  return (
    <label className="block">
      <Micro>{etiket}</Micro>
      <select
        className={GIRDI}
        value=""
        onChange={(e) => {
          const ek = konumlu.find((x) => x.id === e.target.value)
          if (ek) noktaYaz('bas', { lon: ek.lon!, lat: ek.lat!, ad: `${ek.ad} (son konumu)` })
        }}
      >
        <option value="">{konumlu.length ? 'Ekip seç…' : 'Konumunu paylaşan ekip yok'}</option>
        {konumlu.map((e) => (
          <option key={e.id} value={e.id}>
            {e.ad}
            {e.yerAdi ? ` · ${e.yerAdi}` : ''}
          </option>
        ))}
      </select>
    </label>
  )
}

function EkiptenOlaya() {
  const aralik = useSorguAraligi()
  const sos = useSosCagrilari(aralik)
  const ihbar = useIhbarlar(aralik)
  const { bas, hedef, noktaYaz } = useRota()
  const olaylar = useMemo(() => {
    const s = (sos.data ?? [])
      .filter((c) => c.durum !== 'kapandi')
      .map((c) => ({
        id: `sos:${c.id}`,
        lon: c.lon,
        lat: c.lat,
        ad: `SOS · ${ONCELIK_ADI[c.oncelik]}${c.mahalle ? ` · ${c.mahalle}` : ''}`,
        zaman: c.zaman,
      }))
    const i = (ihbar.data ?? [])
      .filter((x) => x.durum !== 'kapandi')
      .map((x) => ({ id: `ihbar:${x.id}`, lon: x.lon, lat: x.lat, ad: ihbarBasligi(x), zaman: x.zaman }))
    return [...s, ...i].sort((a, b) => b.zaman - a.zaman).slice(0, 60)
  }, [sos.data, ihbar.data])
  return (
    <div className="mt-3 grid min-w-0 gap-2">
      <EkipSecimi etiket="Ekip" />
      {bas && <p className="text-small text-ink-2">Başlangıç: {bas.ad}</p>}
      <label className="block">
        <Micro>Olay</Micro>
        <select
          className={GIRDI}
          value=""
          onChange={(e) => {
            const o = olaylar.find((x) => x.id === e.target.value)
            if (o) noktaYaz('hedef', { lon: o.lon, lat: o.lat, ad: `${o.ad} (${tarihSaat(o.zaman)})` })
          }}
        >
          <option value="">{olaylar.length ? 'Açık SOS ya da ihbar seç…' : 'Açık SOS ya da ihbar yok'}</option>
          {olaylar.map((o) => (
            <option key={o.id} value={o.id}>
              {o.ad} · {tarihSaat(o.zaman)}
            </option>
          ))}
        </select>
      </label>
      {hedef && <p className="text-small text-ink-2">Hedef: {hedef.ad}</p>}
    </div>
  )
}

function KapaliYollar({ ucus }: { ucus: (lon: number, lat: number, z: number) => void }) {
  const k = useKapanmalar(true)
  // Bir uydu analizi onlarca kapanma bulur: satır analiz başına (sayı, saat, alanın ortası).
  const gruplar = useMemo(() => {
    const m = new Map<string, { anahtar: string; kaynak: string; sayi: number; zaman: number; lon: number; lat: number }>()
    for (const x of k.data?.kayitlar ?? []) {
      const anahtar = x.analizId ?? `${x.kaynak}:${x.id}`
      const g = m.get(anahtar)
      if (g) {
        g.sayi += 1
        g.lon += x.lon
        g.lat += x.lat
        g.zaman = Math.max(g.zaman, x.zaman)
      } else m.set(anahtar, { anahtar, kaynak: x.kaynak, sayi: 1, zaman: x.zaman, lon: x.lon, lat: x.lat })
    }
    return [...m.values()]
      .map((g) => ({ ...g, lon: g.lon / g.sayi, lat: g.lat / g.sayi }))
      .sort((a, b) => b.zaman - a.zaman)
  }, [k.data])
  const toplam = k.data?.kayitlar.length ?? 0
  if (k.isError) return <div className="mt-3"><VeriYok ne="Kapanmalar" neden="kapanma ucu yanıt vermedi" /></div>
  return (
    <div className="mt-3">
      <SuAn>
        {k.isPending
          ? 'Yükleniyor…'
          : toplam
            ? `${sayi(toplam)} bilinen yol kapanması, ${sayi(gruplar.length)} kaynaktan. Rota bunlardan kaçınır; haritada kırmızı.`
            : 'Bilinen yol kapanması yok.'}
      </SuAn>
      {gruplar.length > 0 && (
        <ul className="mt-2 border-t border-line">
          {gruplar.map((g) => (
            <li key={g.anahtar}>
              <button
                type="button"
                onClick={() => ucus(g.lon, g.lat, g.sayi > 1 ? 14 : 17)}
                className="flex w-full justify-between gap-2 border-b border-line px-1 py-1.5 text-left text-small hover:bg-hover"
              >
                <span className="text-ink">
                  {g.kaynak === 'uydu' ? 'Uydu analizi' : g.kaynak}
                  <span className="text-ink-3">{` · ${sayi(g.sayi)} kapalı yol`}</span>
                </span>
                <span className="shrink-0 font-mono text-ink-3">{tarihSaat(g.zaman)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

/* ---- sağ panel -------------------------------------------------------------- */

export function YolSag() {
  const d = useRota()
  if (d.soru === 'kapali') {
    return (
      <Bolum baslik="Kapalı yollar">
        <Amac>
          Uydu analizinin bulduğu kapanmalar. Modelin tahminidir, sahada doğrulanmadı. Rota bu
          noktaların 25 m'sindeki yolu 20 kat pahalı sayar; başka yol yoksa yine geçer ve söyler.
        </Amac>
      </Bolum>
    )
  }
  return (
    <>
      {d.adaylar && <Adaylar />}
      {d.sonuc ? (
        <RotaKarti r={d.sonuc} kiyas={d.kiyas} kacin={d.kacin} />
      ) : (
        !d.adaylar && (
          <Bolum baslik="Güzergâh">
            <Amac>Seçilen rotanın süresi, uzunluğu, üzerindeki kapanma ve hasar, adım adım tarif.</Amac>
            <div className="mt-2">
              <VeriYok ne="Güzergâh" neden="henüz başlangıç ve hedef seçilmedi" />
            </div>
          </Bolum>
        )
      )}
    </>
  )
}

function Adaylar() {
  const { adaylar, adayKaynagi, seciliAday, adaySec, soru } = useRota()
  if (!adaylar) return null
  return (
    <Bolum baslik={soru === 'toplanma' ? 'En yakın toplanma alanları' : 'En yakın hastaneler'} dolgusuz>
      {adaylar.length === 0 ? (
        <p className="px-3 pb-3 text-small text-ink-3">
          Şehrin yol ağında yoldan ulaşılabilen yer bulunamadı.
        </p>
      ) : (
        <ul className="border-t border-line">
          {adaylar.map((a, i) => (
            <li key={`${a.lon},${a.lat}`}>
              <button
                type="button"
                aria-pressed={i === seciliAday}
                onClick={() => adaySec(i)}
                className={sn(
                  'flex w-full items-start justify-between gap-2 border-b border-line px-3 py-2 text-left',
                  i === seciliAday ? 'bg-raised' : 'hover:bg-raised',
                )}
              >
                <span className="min-w-0">
                  <span className="block truncate text-small text-ink">{a.ad}</span>
                  <span className="block text-small text-ink-3">
                    {`yoldan ${mesafe(a.mesafeM)} · kuş uçuşu ${mesafe(a.kusUcusuM)}`}
                    {a.kapanmadanGecer ? ' · kapanmadan geçiyor' : ''}
                  </span>
                </span>
                <span className="shrink-0 font-mono text-small text-ink">{`~${a.sureDk} dk`}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {adayKaynagi && <p className="px-3 py-2 text-small text-ink-3">{adayKaynagi}</p>}
    </Bolum>
  )
}

function RotaKarti({ r, kiyas, kacin }: { r: Guzergah; kiyas: Guzergah | null; kacin: boolean }) {
  const kunye = useRotaKunyesi()
  const sehir = kunye.data?.sehirler.find((s) => s.id === r.ag)?.ad
  const fark = kiyas ? { dk: r.sureDk - kiyas.sureDk, m: r.mesafeM - kiyas.mesafeM } : null
  return (
    <Bolum baslik="Güzergâh">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-metric text-ink">{`~${r.sureDk} dk`}</span>
        <span className="text-small text-ink-2">{`yoldan ${mesafe(r.mesafeM)}`}</span>
      </div>
      <p className="mt-0.5 text-small text-ink-3">
        {[
          r.kusUcusuM != null ? `kuş uçuşu ${mesafe(r.kusUcusuM)}` : null,
          r.donus ? `${r.donus.sol} sola, ${r.donus.sag} sağa dönüş` : null,
          r.ag ? (r.ag === 'genel' ? 'şehirler arası ağ' : `${sehir ?? r.ag} yol ağı`) : null,
        ]
          .filter(Boolean)
          .join(' · ')}
      </p>

      {r.kapanmadanGecer > 0 && (
        <p role="note" className="mt-2 flex items-start gap-2 rounded-control border border-crit px-2.5 py-2 text-small text-ink">
          <WarningCircle size={16} weight="bold" className="mt-0.5 shrink-0 text-crit" aria-hidden />
          {`Başka yol olmadığı için rota bilinen ${r.kapanmadanGecer} kapanmadan geçiyor. Ekip orada araçtan inmek zorunda kalabilir.`}
        </p>
      )}
      {r.riskliM > 0 && (
        <p className="mt-2 flex items-start gap-2 rounded-control border border-high px-2.5 py-2 text-small text-ink">
          <WarningCircle size={16} weight="bold" className="mt-0.5 shrink-0 text-high" aria-hidden />
          {`Rotanın ${mesafe(r.riskliM)} kadarı bilinen hasar noktalarına 400 m'den yakın.`}
        </p>
      )}

      <dl className="kilav-kv mt-3 gap-x-2.5 gap-y-1.5 text-small">
        <dt className="text-ink-3">Kaçınma</dt>
        <dd className="text-ink">
          {!kacin
            ? 'Kapalı: hasar ve kapanma yok sayıldı'
            : fark == null
              ? 'Açık'
              : fark.dk === 0 && Math.abs(fark.m) < 50
                ? 'Açık · kaçınmak rotayı değiştirmedi'
                : `Açık · kaçınmanın bedeli ${fark.dk >= 0 ? '+' : ''}${fark.dk} dk, ${fark.m >= 0 ? '+' : '−'}${mesafe(Math.abs(fark.m))}`}
        </dd>
        {r.hasar && (
          <>
            <dt className="text-ink-3">Bilinen</dt>
            <dd className="text-ink">{`${sayi(r.hasar.kapanma)} kapanma, ${sayi(r.hasar.hasarNoktasi)} hasar noktası (bölgede)`}</dd>
          </>
        )}
        {r.baglantiM > 30 && (
          <>
            <dt className="text-ink-3">Yola bağlantı</dt>
            <dd className="text-ink">{`Başlangıç en yakın araç yoluna ${mesafe(r.baglantiM)}`}</dd>
          </>
        )}
      </dl>

      {r.adimlar && r.adimlar.length > 0 && (
        <>
          <Micro className="mt-3 block">Adım adım</Micro>
          <ol className="mt-1.5">
            {r.adimlar.map((a, i) => (
              <li key={i} className="flex justify-between gap-2 border-t border-line py-1.5 text-small">
                <span className="min-w-0">
                  <span className="text-ink-2">{a.manevra === 'basla' ? `Başla${a.yon ? `, ${a.yon}` : ''}` : MANEVRA_ADI[a.manevra]}</span>
                  <span className="text-ink">{` · ${a.ad}`}</span>
                </span>
                <span className="shrink-0 font-mono text-ink-3">{mesafe(a.uzunlukM)}</span>
              </li>
            ))}
          </ol>
        </>
      )}

      <Teknik>
        {`Yol ağı: OpenStreetMap${kunye.data ? ` (${kunye.data.osm})` : ''}. Süre: yol türüne göre ortalama hız ve kavşakta dönüş bedeli (sola ${kunye.data?.donusBedeliSn.sol ?? 9} sn, sağa ${kunye.data?.donusBedeliSn.sag ?? 4} sn); ikisi de varsayımdır, ölçülmedi, trafik verisi yok.`}
        {r.aramaMs != null ? ` Arama ${r.aramaMs} ms.` : ''}
      </Teknik>
    </Bolum>
  )
}
