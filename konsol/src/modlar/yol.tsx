import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { ArrowDown, ArrowUp, Crosshair, WarningCircle, X } from '@phosphor-icons/react'
import { Amac, Bolum, HazirSecenekler, InceAyar, SuAn, Teknik, VeriYok } from '@/kabuk/Panel'
import { Anahtar, Chip, Micro, Rozet } from '@/kabuk/parcalar'
import { ApiHatasi, apiPost } from '@/veri/istemci'
import { useHarita } from '@/harita/HaritaKabugu'
import { useSorguAraligi } from '@/durum/zamanDurumu'
import { EN_COK_DURAK, useRota, type RotaSorusu } from '@/durum/rotaDurumu'
import { useEkipler, useSosCagrilari, ONCELIK_ADI } from '@/veri/sorgular'
import { useIhbarlar, ihbarBasligi } from '@/veri/ihbar'
import {
  KAPANMA_DURUM_ADI,
  useAnalizKapanmaDurumu,
  useKapanmaDurumu,
  useKapanmaListesi,
  type Kapanma,
  type KapanmaDurumu,
} from '@/veri/katman'
import { useOturum } from '@/kimlik/oturum'
import {
  MANEVRA_ADI,
  useRotaKunyesi,
  type EnYakinYaniti,
  type Guzergah,
  type RotaAdimi,
} from '@/veri/guzergah'
import { mesafe, sayi, tarihSaat } from '@/lib/bicim'
import { sn } from '@/lib/sinif'

/* ---------------------------------------------------------------------------
   Yol ve rota (J-171; yeniden düzen: J-190).

   · İki nokta arası: haritaya ilk tıklama başlangıç (A), ikincisi hedef (B).
   · Çok duraklı: her tıklama sıradaki durak; rota 1 → 2 → … sırasıyla.
   · Ekipten olaya, en yakın hastane / toplanma alanı.
   · Kapalı yollar: uydu analizinin bulduğu kapanmalar; durumu (kapalı /
     açıldı / yanlış alarm) buradan değişir, rota anında buna göre hesaplanır.

   Araç rotası sunucuda, kendi yol ağımızda hesaplanır (arac_rotasi.py): tek
   yönlere, göbeklere ve OSM dönüş yasaklarına uyar, kapalı yoldan yalnız başka
   yol yoksa geçer ve bunu söyler. Sevk ve saha ekranları aynı motoru kullanır.
--------------------------------------------------------------------------- */

const SORULAR: ReadonlyArray<{ id: RotaSorusu; etiket: string }> = [
  { id: 'nokta', etiket: 'İki nokta arası' },
  { id: 'duraklar', etiket: 'Çok duraklı' },
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

/** Çok duraklı rota: tek istek, sunucu bacakları aynı motordan geçirir. */
function useDurakHesabi() {
  const { duraklar, kacin, sonucYaz } = useRota()
  return useMutation({
    mutationFn: () =>
      apiPost<Guzergah>('/api/guzergah/duraklar', {
        noktalar: duraklar.map((n) => ({ lon: n.lon, lat: n.lat })),
        kacin,
      }),
    onSuccess: (ana) => sonucYaz(ana, null),
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
  const durak = useDurakHesabi()
  const enYakin = useEnYakinHesabi()

  // Noktalar tamamlanınca rota kendiliğinden hesaplanır (düğmeye ayrıca basmadan).
  const iki = d.soru === 'nokta' || d.soru === 'ekip'
  const tek = d.soru === 'hastane' || d.soru === 'toplanma'
  const cok = d.soru === 'duraklar'
  const ref = useRef({ rota, durak, enYakin })
  ref.current = { rota, durak, enYakin }
  useEffect(() => {
    if (iki && d.bas && d.hedef && !d.sonuc) ref.current.rota.mutate()
  }, [iki, d.bas, d.hedef, d.kacin, d.sonuc])
  useEffect(() => {
    if (cok && d.duraklar.length >= 2 && !d.sonuc) ref.current.durak.mutate()
  }, [cok, d.duraklar, d.kacin, d.sonuc])
  useEffect(() => {
    if (tek && d.bas && !d.adaylar) ref.current.enYakin.mutate()
  }, [tek, d.bas, d.kacin, d.adaylar])

  const hata = rota.isError ? rota.error : durak.isError ? durak.error : enYakin.isError ? enYakin.error : null
  const bekliyor = rota.isPending || durak.isPending || enYakin.isPending

  return (
    <Bolum baslik="Yol ve rota">
      <Amac>
        Ekip oraya hangi yoldan, kaç dakikada gider? Tek yönlere, göbeklere ve dönüş yasaklarına
        uyan, kapalı yollardan geçmeyen araç rotasını çıkarır.
      </Amac>

      <HazirSecenekler etiket="Rota soruları" secenekler={SORULAR} secili={d.soru} onSec={d.soruSec} />

      {d.soru === 'nokta' && <IkiNokta />}
      {cok && <DurakListesi />}
      {d.soru === 'ekip' && <EkiptenOlaya />}
      {tek && (
        <div className="mt-3 grid min-w-0 gap-2">
          <NoktaSatiri hangi="bas" etiket="Nereden" harf="A" />
          <EkipSecimi etiket="ya da bir ekibin konumundan" />
        </div>
      )}
      {d.soru === 'kapali' && <KapanmaYonetimi />}

      {d.soru !== 'kapali' && (
        <InceAyar baslik="Rota kuralları">
          <Anahtar
            acik={d.kacin}
            etiket="Kapalı ve hasarlı yollardan kaçın"
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
              ? `Haritaya tıkla: ${d.secim === 'bas' ? 'başlangıç (A)' : 'hedef (B)'} değişecek.`
              : d.sonuc
                ? `~${d.sonuc.sureDk} dk, yoldan ${mesafe(d.sonuc.mesafeM)}; ayrıntı sağda.`
                : d.soru === 'nokta'
                  ? !d.bas
                    ? 'Haritaya tıkla: önce başlangıç (A).'
                    : 'Haritaya tıkla: şimdi hedef (B). Rota kendiliğinden çıkar.'
                  : cok
                    ? d.duraklar.length < 2
                      ? `Haritaya sırayla tıkla: her tıklama bir durak (en çok ${EN_COK_DURAK}).`
                      : `Haritaya tıklayınca durak eklenir (${d.duraklar.length}/${EN_COK_DURAK}).`
                    : tek
                      ? 'Haritaya tıkla ya da ekip seç; en yakın üç yer yoldan sıralanır.'
                      : 'Ekibi ve olayı seç; rota kendiliğinden çıkar.'}
        </SuAn>
      )}

      <Teknik>
        Rota sunucuda, kendi yol ağımızda (OpenStreetMap) kenar tabanlı Dijkstra ile hesaplanır: tek
        yön, göbek ve OSM dönüş yasakları uygulanır, yol ortasında U dönüşü yapılmaz, sola dönüş
        sağa dönüşten pahalıdır. Kapalı yoldan araç geçmez; başka yol yoksa (ör. hedef kapalı
        sokaktaysa) en az kapanmadan geçer ve bunu söyler. Hasar noktasına yakın yol daha pahalıdır.
        Hızlar yol türüne göre ortalama varsayımdır; trafik verisi yok.
      </Teknik>
    </Bolum>
  )
}

function IkiNokta() {
  const { bas, hedef, noktalariTemizle } = useRota()
  return (
    <div className="mt-3 grid min-w-0 gap-2">
      <NoktaSatiri hangi="bas" etiket="Başlangıç" harf="A" />
      <NoktaSatiri hangi="hedef" etiket="Hedef" harf="B" />
      {(bas || hedef) && (
        <button type="button" onClick={noktalariTemizle} className="justify-self-start text-small text-ink-3 hover:text-ink">
          İki noktayı da temizle
        </button>
      )}
    </div>
  )
}

function Harf({ harf, vurgu }: { harf: string; vurgu: boolean }) {
  return (
    <span
      aria-hidden
      className={sn(
        'grid h-5 w-5 shrink-0 place-items-center rounded-full text-micro font-semibold',
        vurgu ? 'bg-accent text-accent-ink' : 'bg-ink-2 text-ground',
      )}
    >
      {harf}
    </span>
  )
}

function NoktaSatiri({ hangi, etiket, harf }: { hangi: 'bas' | 'hedef'; etiket: string; harf: string }) {
  const { secim, secimAc, noktaYaz } = useRota()
  const nokta = useRota((d) => d[hangi])
  const acik = secim === hangi
  return (
    <div className="min-w-0">
      <Micro>{etiket}</Micro>
      <div className="mt-1 flex items-center gap-1.5">
        <Harf harf={harf} vurgu={hangi === 'bas'} />
        <span className={sn('min-w-0 flex-1 truncate text-small', nokta ? 'text-ink' : 'text-ink-3')}>
          {nokta?.ad ?? 'haritaya tıkla'}
        </span>
        {nokta && (
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
            {acik ? 'Haritaya tıkla…' : 'Değiştir'}
          </button>
        )}
        {nokta && (
          <button
            type="button"
            onClick={() => noktaYaz(hangi, null)}
            aria-label={`${etiket} noktasını sil`}
            className="shrink-0 text-ink-3 hover:text-ink"
          >
            <X size={14} aria-hidden />
          </button>
        )}
      </div>
    </div>
  )
}

function DurakListesi() {
  const { duraklar, durakSil, durakTasi, duraklariTemizle } = useRota()
  return (
    <div className="mt-3">
      <div className="flex items-baseline justify-between gap-2">
        <Micro>{`Duraklar · ${duraklar.length}/${EN_COK_DURAK}`}</Micro>
        {duraklar.length > 0 && (
          <button type="button" onClick={duraklariTemizle} className="text-small text-ink-3 hover:text-ink">
            Hepsini temizle
          </button>
        )}
      </div>
      {duraklar.length === 0 ? (
        <p className="mt-1.5 text-small text-ink-3">
          Henüz durak yok. Haritaya sırayla tıkla; rota bu sırayla gider. Sırayı oklarla değiştirebilirsin.
        </p>
      ) : (
        <ol className="mt-1.5 border-t border-line">
          {duraklar.map((n, i) => (
            <li key={`${n.lon},${n.lat},${i}`} className="flex items-center gap-1.5 border-b border-line py-1.5">
              <Harf harf={String(i + 1)} vurgu={i === 0} />
              <span className="min-w-0 flex-1 truncate font-mono text-small text-ink-2">{n.ad}</span>
              <button
                type="button"
                disabled={i === 0}
                onClick={() => durakTasi(i, -1)}
                aria-label={`${i + 1}. durağı yukarı taşı`}
                className="shrink-0 text-ink-3 hover:text-ink disabled:opacity-30"
              >
                <ArrowUp size={14} aria-hidden />
              </button>
              <button
                type="button"
                disabled={i === duraklar.length - 1}
                onClick={() => durakTasi(i, 1)}
                aria-label={`${i + 1}. durağı aşağı taşı`}
                className="shrink-0 text-ink-3 hover:text-ink disabled:opacity-30"
              >
                <ArrowDown size={14} aria-hidden />
              </button>
              <button
                type="button"
                onClick={() => durakSil(i)}
                aria-label={`${i + 1}. durağı sil`}
                className="shrink-0 text-ink-3 hover:text-ink"
              >
                <X size={14} aria-hidden />
              </button>
            </li>
          ))}
        </ol>
      )}
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

/* ---- kapalı yollar ------------------------------------------------------------ */

/** Kapalı parçanın yoldaki uzunluğu (m); çizgisi yoksa null. */
function uzunlukM(k: Kapanma): number | null {
  const c = k.cizgi
  if (!c || c.length < 2) return null
  let t = 0
  for (let i = 1; i < c.length; i++) {
    const [la1, lo1] = c[i - 1]
    const [la2, lo2] = c[i]
    const kx = 111320 * Math.cos(((la1 + la2) / 2) * (Math.PI / 180))
    t += Math.hypot((lo2 - lo1) * kx, (la2 - la1) * 110574)
  }
  return t
}

/** Aynı yol parçası birden çok analizde kaydedilmiş olabilir: ekranda tek satır
    (sunucu durumu da birlikte değiştirir). En yeni kayıt temsil eder. */
function tekillestir(kayitlar: Kapanma[]): Kapanma[] {
  const m = new Map<string, Kapanma>()
  for (const k of kayitlar) {
    const anahtar = `${k.lon.toFixed(6)},${k.lat.toFixed(6)}`
    const var_ = m.get(anahtar)
    if (!var_ || k.zaman > var_.zaman) m.set(anahtar, k)
  }
  return [...m.values()]
}

const DURUM_TONU: Record<KapanmaDurumu, 'crit' | 'ok' | 'nötr'> = { kapali: 'crit', acildi: 'ok', yanlis: 'nötr' }

function useKapanmalarTekil() {
  const k = useKapanmaListesi(true)
  const tekil = useMemo(() => tekillestir(k.data?.kayitlar ?? []), [k.data])
  return { ...k, tekil }
}

function KapanmaYonetimi() {
  const k = useKapanmalarTekil()
  const { kapanmaSuzgeci, kapanmaSuzgeciSec, acikAnaliz, analizAc, seciliKapanma, kapanmaSec } = useRota()
  const { kutuyaUc, ucus } = useHarita()
  const sayilar = useMemo(() => {
    const s: Record<KapanmaDurumu, number> = { kapali: 0, acildi: 0, yanlis: 0 }
    for (const x of k.tekil) s[x.durum] += 1
    return s
  }, [k.tekil])
  const gruplar = useMemo(() => {
    const suz = kapanmaSuzgeci === 'hepsi' ? k.tekil : k.tekil.filter((x) => x.durum === kapanmaSuzgeci)
    const m = new Map<string, { anahtar: string; kaynak: string; zaman: number; kayitlar: Kapanma[] }>()
    for (const x of suz) {
      const anahtar = x.analizId ?? `${x.kaynak}:${x.id}`
      const g = m.get(anahtar) ?? { anahtar, kaynak: x.kaynak, zaman: 0, kayitlar: [] }
      g.kayitlar.push(x)
      g.zaman = Math.max(g.zaman, x.zaman)
      m.set(anahtar, g)
    }
    return [...m.values()].sort((a, b) => b.zaman - a.zaman)
  }, [k.tekil, kapanmaSuzgeci])

  // Hasar analizinden "Kapalı yolları gözden geçir" ile gelindiyse o analizin
  // kapanmalarına uçulur (bir kez).
  const ucululan = useRef<string | null>(null)
  useEffect(() => {
    if (!acikAnaliz || ucululan.current === acikAnaliz) return
    const g = k.tekil.filter((x) => x.analizId === acikAnaliz)
    if (!g.length) return
    ucululan.current = acikAnaliz
    const lon = g.map((x) => x.lon)
    const lat = g.map((x) => x.lat)
    kutuyaUc([Math.min(...lon) - 0.001, Math.min(...lat) - 0.001, Math.max(...lon) + 0.001, Math.max(...lat) + 0.001])
  }, [acikAnaliz, k.tekil, kutuyaUc])

  if (k.isError) return <div className="mt-3"><VeriYok ne="Kapanmalar" neden="kapanma ucu yanıt vermedi" /></div>
  return (
    <div className="mt-3">
      <p className="text-small text-ink-2">
        Uydu analizinin kapalı bulduğu yol parçaları. Sahada yol açıldıysa ya da hiç kapanmadıysa
        durumunu değiştir; rota hemen buna göre hesaplanır. Haritada bir parçaya tıklayınca sağda açılır.
      </p>
      <div role="group" aria-label="Duruma göre" className="mt-2.5 flex flex-wrap gap-1.5">
        {(['kapali', 'acildi', 'yanlis'] as const).map((d) => (
          <Chip key={d} secili={kapanmaSuzgeci === d} onClick={() => kapanmaSuzgeciSec(d)}>
            {`${KAPANMA_DURUM_ADI[d]} · ${sayi(sayilar[d])}`}
          </Chip>
        ))}
        <Chip secili={kapanmaSuzgeci === 'hepsi'} onClick={() => kapanmaSuzgeciSec('hepsi')}>
          Hepsi
        </Chip>
      </div>

      <details className="mt-2.5">
        <summary className="cursor-pointer text-small text-ink-2 hover:text-ink">Kırmızı neye göre çiziliyor?</summary>
        <div className="mt-1.5 space-y-1 text-small text-ink-2">
          <p>
            Her OSM sokak parçası (iki kavşak arası) yaklaşık 5 m aralıkla örneklenir. Örnek nokta
            modelin hasar maskesine düşerse o kısım kapalı sayılır; kırmızı çizgi o kısımdır.
          </p>
          <p>
            Hasarın yolun üstüne düşmesi gerekir: yandaki bina yıkık olsa da yolun üstünde hasar yoksa
            yol açık sayılır. Bu modelin tahminidir, sahada doğrulanmadı.
          </p>
          <p>Rota, kapalı parçanın üstünde yattığı sokağı kapalı sayar; araç oradan başka yol yoksa geçer.</p>
        </div>
      </details>

      {k.isPending ? (
        <p className="mt-3 text-small text-ink-3">Yükleniyor…</p>
      ) : gruplar.length === 0 ? (
        <p className="mt-3 text-small text-ink-3">
          {kapanmaSuzgeci === 'kapali' ? 'Bilinen kapalı yol yok.' : 'Bu durumda kayıt yok.'}
        </p>
      ) : (
        <ul className="mt-3 border-t border-line">
          {gruplar.map((g) => {
            const acik = acikAnaliz === g.anahtar
            return (
              <li key={g.anahtar} className="border-b border-line">
                <button
                  type="button"
                  aria-expanded={acik}
                  onClick={() => analizAc(acik ? null : g.anahtar)}
                  className="flex w-full justify-between gap-2 px-1 py-1.5 text-left text-small hover:bg-hover"
                >
                  <span className="text-ink">
                    {g.kaynak === 'uydu' ? 'Uydu analizi' : g.kaynak}
                    <span className="text-ink-3">{` · ${sayi(g.kayitlar.length)} parça`}</span>
                  </span>
                  <span className="shrink-0 font-mono text-ink-3">{tarihSaat(g.zaman)}</span>
                </button>
                {acik && (
                  <div className="pb-2">
                    {g.kayitlar[0]?.analizId && <TopluDurum analizId={g.kayitlar[0].analizId} />}
                    <ul>
                      {g.kayitlar.map((x) => {
                        const u = uzunlukM(x)
                        return (
                          <li key={x.id}>
                            <button
                              type="button"
                              aria-pressed={seciliKapanma === x.id}
                              onClick={() => {
                                kapanmaSec(x.id)
                                ucus(x.lon, x.lat, 17)
                              }}
                              className={sn(
                                'flex w-full items-center justify-between gap-2 rounded-control px-2 py-1 text-left text-small',
                                seciliKapanma === x.id ? 'bg-raised' : 'hover:bg-hover',
                              )}
                            >
                              <span className="text-ink-2">{u != null ? `Parça · ${mesafe(u)}` : 'Nokta kaydı'}</span>
                              <Rozet ton={DURUM_TONU[x.durum]}>{KAPANMA_DURUM_ADI[x.durum]}</Rozet>
                            </button>
                          </li>
                        )
                      })}
                    </ul>
                  </div>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}

/** Bir analizin bütün kapanmaları birden: yalnız koordinatör ve yönetici; onaylı. */
function TopluDurum({ analizId }: { analizId: string }) {
  const { oturum } = useOturum()
  const toplu = useAnalizKapanmaDurumu()
  const [soru, setSoru] = useState<KapanmaDurumu | null>(null)
  if (oturum?.rol !== 'koordinator' && oturum?.rol !== 'yonetici') return null
  return (
    <div className="mb-1.5 px-1">
      {soru ? (
        <div className="flex flex-wrap items-center gap-1.5 text-small">
          <span className="text-ink-2">{`Bu analizin bütün parçaları "${KAPANMA_DURUM_ADI[soru]}" olsun mu?`}</span>
          <button
            type="button"
            disabled={toplu.isPending}
            onClick={() => toplu.mutate({ analizId, durum: soru }, { onSuccess: () => setSoru(null) })}
            className="rounded-control bg-accent px-2 py-0.5 text-small font-semibold text-accent-ink disabled:opacity-50"
          >
            Evet
          </button>
          <button type="button" onClick={() => setSoru(null)} className="text-ink-3 hover:text-ink">
            Vazgeç
          </button>
        </div>
      ) : (
        <div className="flex flex-wrap items-center gap-1.5 text-small">
          <span className="text-ink-3">Hepsi:</span>
          {(['acildi', 'yanlis', 'kapali'] as const).map((d) => (
            <button
              key={d}
              type="button"
              onClick={() => setSoru(d)}
              className="rounded-control border border-line-2 px-2 py-0.5 text-ink-2 hover:bg-hover hover:text-ink"
            >
              {KAPANMA_DURUM_ADI[d]}
            </button>
          ))}
        </div>
      )}
      {toplu.isError && (
        <p role="alert" className="mt-1 text-small text-crit">
          {hataMetni(toplu.error)}
        </p>
      )}
    </div>
  )
}

/** Seçili kapanmanın kartı: ne, nereden, ne zaman; durumunu değiştir. */
function KapanmaKarti() {
  const k = useKapanmalarTekil()
  const { seciliKapanma, kapanmaSec } = useRota()
  const durum = useKapanmaDurumu()
  const { ucus } = useHarita()
  const [not, setNot] = useState('')
  // Haritadan seçilen kayıt aynı parçanın başka bir analizdeki kopyası olabilir:
  // kart o parçanın temsilcisini (en yeni kaydı) gösterir.
  const ham = k.data?.kayitlar.find((y) => y.id === seciliKapanma)
  const x = ham
    ? (k.tekil.find((y) => Math.abs(y.lon - ham.lon) < 1e-6 && Math.abs(y.lat - ham.lat) < 1e-6) ?? ham)
    : undefined
  // Başka kapanma seçilince not ve sonuç sıfırlanır.
  useEffect(() => {
    setNot('')
    durum.reset()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seciliKapanma])
  if (!x)
    return (
      <Bolum baslik="Yol kapanması">
        <VeriYok ne="Kapanma" neden={k.isPending ? 'yükleniyor' : 'kayıt bulunamadı'} />
      </Bolum>
    )
  const u = uzunlukM(x)
  return (
    <Bolum baslik="Yol kapanması" ek={<Rozet ton={DURUM_TONU[x.durum]}>{KAPANMA_DURUM_ADI[x.durum]}</Rozet>}>
      <dl className="kilav-kv gap-x-2.5 gap-y-1.5 text-small">
        <dt className="text-ink-3">Kaynak</dt>
        <dd className="text-ink">{x.kaynak === 'uydu' ? 'Uydu analizi (modelin tahmini)' : x.kaynak}</dd>
        <dt className="text-ink-3">Bulundu</dt>
        <dd className="text-ink">{tarihSaat(x.zaman)}</dd>
        {u != null && (
          <>
            <dt className="text-ink-3">Kapalı kısım</dt>
            <dd className="text-ink">{`${mesafe(u)} (yolun hasar düşen kısmı)`}</dd>
          </>
        )}
        {x.durumZaman && (
          <>
            <dt className="text-ink-3">Son değişiklik</dt>
            <dd className="text-ink">
              {`${KAPANMA_DURUM_ADI[x.durum]} · ${tarihSaat(x.durumZaman)}`}
              {x.durumNotu ? ` · “${x.durumNotu}”` : ''}
            </dd>
          </>
        )}
      </dl>

      <p className="mt-2.5 text-small text-ink-2">
        {x.durum === 'kapali'
          ? 'Araç rotası bu sokaktan geçmez. Sahada yol açıksa ya da hiç kapanmadıysa durumunu değiştir.'
          : 'Rota bu kaydı hesaba katmıyor. Yol yeniden kapandıysa "Kapalı" yap.'}
      </p>

      <label className="mt-2.5 block">
        <Micro>Not (isteğe bağlı)</Micro>
        <input
          value={not}
          onChange={(e) => setNot(e.target.value.slice(0, 300))}
          placeholder="ör. ekip geçti, enkaz kaldırıldı"
          className={GIRDI}
        />
      </label>
      <div className="mt-2 grid grid-cols-3 gap-1.5">
        {(['acildi', 'yanlis', 'kapali'] as const).map((d) => (
          <button
            key={d}
            type="button"
            disabled={durum.isPending || x.durum === d}
            onClick={() => durum.mutate({ id: x.id, durum: d, not })}
            className={sn(
              'rounded-control border px-2 py-1.5 text-small disabled:opacity-40',
              d === 'kapali' ? 'border-crit text-ink' : 'border-line-2 text-ink hover:bg-hover',
            )}
          >
            {d === 'acildi' ? 'Yol açıldı' : d === 'yanlis' ? 'Yanlış alarm' : 'Kapalı'}
          </button>
        ))}
      </div>
      {durum.isSuccess && (
        <p role="status" className="mt-2 text-small text-ok">
          Kaydedildi. Rota ve harita güncellendi; işlem kayda geçti.
        </p>
      )}
      {durum.isError && (
        <p role="alert" className="mt-2 text-small text-crit">
          {hataMetni(durum.error)}
        </p>
      )}
      <div className="mt-2.5 flex gap-1.5">
        <button
          type="button"
          onClick={() => ucus(x.lon, x.lat, 18)}
          className="rounded-control border border-line-2 px-2.5 py-1 text-small text-ink-2 hover:bg-hover hover:text-ink"
        >
          Yaklaş
        </button>
        <button
          type="button"
          onClick={() => kapanmaSec(null)}
          className="rounded-control border border-line-2 px-2.5 py-1 text-small text-ink-2 hover:bg-hover hover:text-ink"
        >
          Kapat
        </button>
      </div>
    </Bolum>
  )
}

/* ---- sağ panel -------------------------------------------------------------- */

export function YolSag() {
  const d = useRota()
  if (d.soru === 'kapali') {
    return d.seciliKapanma ? (
      <KapanmaKarti />
    ) : (
      <Bolum baslik="Kapalı yollar">
        <Amac>
          Haritada bir kapalı yol parçasına ya da soldaki listeden bir satıra tıkla: ne zaman, hangi
          analizde bulunduğunu gör, durumunu değiştir.
        </Amac>
        <ul className="mt-2.5 space-y-1.5 text-small text-ink-2">
          <li className="flex items-center gap-2">
            <span aria-hidden className="h-1 w-5 rounded-badge bg-crit" /> Kapalı: araç rotası geçmez
          </li>
          <li className="flex items-center gap-2">
            <span aria-hidden className="h-0 w-5 border-t-2 border-dashed border-ok" /> Açıldı: rota yeniden kullanır
          </li>
          <li className="flex items-center gap-2">
            <span aria-hidden className="h-0 w-5 border-t-2 border-dashed border-ink-3" /> Yanlış alarm: model yanılmış
          </li>
        </ul>
        <Teknik>
          Durum değişikliği aynı parçanın bütün analizlerdeki kayıtlarına uygulanır, işlem kaydına yazılır
          ve canlı akışla bütün ekranlara gider. Kayıt silinmez; geri alınabilir ve modelin yanlış alarm
          oranı ölçülebilir.
        </Teknik>
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
              <VeriYok
                ne="Güzergâh"
                neden={d.soru === 'duraklar' ? 'en az iki durak gerekiyor' : 'henüz başlangıç ve hedef seçilmedi'}
              />
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

/** Rota kapanmadan geçiyorsa NEDEN geçtiğini söyler: uç kapalı sokakta mı,
    yoksa başka yol yok mu. */
function kapanmaUyarisi(r: { kapanmadanGecer: number; baslangicKapanmada?: boolean; hedefKapanmada?: boolean }): string | null {
  if (!r.kapanmadanGecer) return null
  if (r.baslangicKapanmada && r.hedefKapanmada)
    return 'Başlangıç da hedef de kapalı sokağın üstünde; o kısımlardan geçmek kaçınılmaz. Ekip son kısmı yaya ya da enkazı kaldırarak geçebilir.'
  if (r.hedefKapanmada)
    return 'Hedef kapalı bir sokağın üstünde; son kısımdan geçmek kaçınılmaz. Ekip araçtan inip yürümek zorunda kalabilir.'
  if (r.baslangicKapanmada)
    return 'Başlangıç kapalı bir sokağın üstünde; ilk kısımdan geçmek kaçınılmaz.'
  return `Başka yol olmadığı için rota bilinen ${r.kapanmadanGecer} kapanmadan geçiyor. Ekip orada araçtan inmek zorunda kalabilir.`
}

function Adimlar({ adimlar }: { adimlar: RotaAdimi[] }) {
  return (
    <ol className="mt-1.5">
      {adimlar.map((a, i) => (
        <li key={i} className="flex justify-between gap-2 border-t border-line py-1.5 text-small">
          <span className="min-w-0">
            <span className="text-ink-2">{a.manevra === 'basla' ? `Başla${a.yon ? `, ${a.yon}` : ''}` : MANEVRA_ADI[a.manevra]}</span>
            <span className="text-ink">{` · ${a.ad}`}</span>
          </span>
          <span className="shrink-0 font-mono text-ink-3">{mesafe(a.uzunlukM)}</span>
        </li>
      ))}
    </ol>
  )
}

function RotaKarti({ r, kiyas, kacin }: { r: Guzergah; kiyas: Guzergah | null; kacin: boolean }) {
  const kunye = useRotaKunyesi()
  const sehir = kunye.data?.sehirler.find((s) => s.id === r.ag)?.ad
  const fark = kiyas ? { dk: r.sureDk - kiyas.sureDk, m: r.mesafeM - kiyas.mesafeM } : null
  const uyari = kapanmaUyarisi(r)
  return (
    <Bolum baslik={r.bacaklar ? `Güzergâh · ${r.bacaklar.length + 1} durak` : 'Güzergâh'}>
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

      {uyari && !r.bacaklar && (
        <p role="note" className="mt-2 flex items-start gap-2 rounded-control border border-crit px-2.5 py-2 text-small text-ink">
          <WarningCircle size={16} weight="bold" className="mt-0.5 shrink-0 text-crit" aria-hidden />
          {uyari}
        </p>
      )}
      {r.riskliM > 0 && (
        <p className="mt-2 flex items-start gap-2 rounded-control border border-high px-2.5 py-2 text-small text-ink">
          <WarningCircle size={16} weight="bold" className="mt-0.5 shrink-0 text-high" aria-hidden />
          {`Rotanın ${mesafe(r.riskliM)} kadarı bilinen hasar noktalarına 400 m'den yakın.`}
        </p>
      )}

      {r.bacaklar ? (
        <>
          <Micro className="mt-3 block">Bacaklar</Micro>
          <ol className="mt-1.5">
            {r.bacaklar.map((b, i) => {
              const u = kapanmaUyarisi(b)
              return (
                <li key={i} className="border-t border-line py-1.5 text-small">
                  <details>
                    <summary className="flex cursor-pointer justify-between gap-2">
                      <span className="text-ink">{`${i + 1} → ${i + 2}`}</span>
                      <span className="font-mono text-ink-2">{`~${b.sureDk} dk · ${mesafe(b.mesafeM)}`}</span>
                    </summary>
                    {u && <p className="mt-1 text-small text-crit">{u}</p>}
                    {b.adimlar && b.adimlar.length > 0 && <Adimlar adimlar={b.adimlar} />}
                  </details>
                </li>
              )
            })}
          </ol>
        </>
      ) : (
        <>
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
                <dd className="text-ink">{`${sayi(r.hasar.kapanma)} kapalı yol, ${sayi(r.hasar.hasarNoktasi)} hasar noktası (bölgede)`}</dd>
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
              <Adimlar adimlar={r.adimlar} />
            </>
          )}
        </>
      )}

      <Teknik>
        {`Yol ağı: OpenStreetMap${kunye.data ? ` (${kunye.data.osm})` : ''}. Süre: yol türüne göre ortalama hız ve kavşakta dönüş bedeli (sola ${kunye.data?.donusBedeliSn.sol ?? 9} sn, sağa ${kunye.data?.donusBedeliSn.sag ?? 4} sn); ikisi de varsayımdır, ölçülmedi, trafik verisi yok.`}
        {r.aramaMs != null ? ` Arama ${r.aramaMs} ms.` : ''}
      </Teknik>
    </Bolum>
  )
}
