import { useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { WarningCircle } from '@phosphor-icons/react'
import { Amac, Bolum, HazirSecenekler, SuAn, Teknik, VeriYok } from '@/kabuk/Panel'
import { Micro, Rozet } from '@/kabuk/parcalar'
import { ApiHatasi, apiPost } from '@/veri/istemci'
import { useHarita } from '@/harita/HaritaKabugu'
import { useCozumleme, type MetinSonucu } from '@/durum/cozumlemeDurumu'
import { useKonsol } from '@/durum/konsolDurumu'
import { useSorguAraligi } from '@/durum/zamanDurumu'
import { sn } from '@/lib/sinif'
import { sayi, tarihSaat } from '@/lib/bicim'
import { IHBAR_DURUMU, useIhbarlar, type Ihbar } from '@/veri/ihbar'
import { DUZEY_ADI, belirsizlikMetni } from '@/veri/metin'
import { IhbarDetayi } from './ihbarParcalari'
import { GorevOzetSatiri } from './sevk'
import {
  ACILIYET_TONU,
  MetinSonucKarti,
  denemeGorunumu,
  ihbarGorunumu,
  kontrolNedeni,
  ucusZoom,
  type MetinGorunumu,
} from './metinKarti'

/* ---------------------------------------------------------------------------
   Metin modu (J-170). Asıl iş afetzedelerden gelen yazılı ihbarların
   kuyruğudur: en acil ve koordinatörün bakması gereken önce. Seçilen ihbar
   sağda tek kartta açılır (metin içinde işaretli adres, kişi, ihtiyaç),
   haritada konumu ve ne kadar sapabileceği çizilir.

   "Metni kendin incelet" ikincil bir araçtır: kayıt açmaz, haritaya yazmaz.
   Eskiden bu deneme analizi işi haritasına nokta bırakıyordu.
--------------------------------------------------------------------------- */

const SUZGECLER = [
  { id: 'acik', etiket: 'Açık' },
  { id: 'kontrol', etiket: 'Bakılması gereken' },
  { id: 'kapandi', etiket: 'Kapanan' },
  { id: 'hepsi', etiket: 'Hepsi' },
] as const
type SuzgecId = (typeof SUZGECLER)[number]['id']

type Satir = { ihbar: Ihbar; g: MetinGorunumu | null; neden: string | null }

const KUYRUK_SINIRI = 60

export function MetinSol() {
  const aralik = useSorguAraligi()
  const ihbar = useIhbarlar(aralik)
  const [suzgec, setSuzgec] = useState<SuzgecId>('acik')
  const secili = useKonsol((d) => d.seciliKayit)
  const kayitSec = useKonsol((d) => d.kayitSec)
  const { ucus } = useHarita()

  const tum = useMemo<Satir[]>(
    () =>
      (ihbar.data ?? [])
        .filter((i) => i.tur === 'metin')
        .map((i) => {
          const g = i.analiz ? ihbarGorunumu(i.analiz) : null
          return { ihbar: i, g, neden: kontrolNedeni(g) }
        }),
    [ihbar.data],
  )
  const acik = tum.filter((s) => s.ihbar.durum !== 'kapandi')
  const bakilacak = acik.filter((s) => s.neden)
  const liste = useMemo(() => {
    const secilen =
      suzgec === 'acik'
        ? tum.filter((s) => s.ihbar.durum !== 'kapandi')
        : suzgec === 'kontrol'
          ? tum.filter((s) => s.ihbar.durum !== 'kapandi' && s.neden)
          : suzgec === 'kapandi'
            ? tum.filter((s) => s.ihbar.durum === 'kapandi')
            : tum
    // Açık önce; sonra en acil; eşitse en yeni.
    return [...secilen].sort(
      (a, b) =>
        Number(a.ihbar.durum === 'kapandi') - Number(b.ihbar.durum === 'kapandi') ||
        (b.g?.aciliyet ?? -1) - (a.g?.aciliyet ?? -1) ||
        b.ihbar.zaman - a.ihbar.zaman,
    )
  }, [tum, suzgec])

  return (
    <>
      <Bolum baslik="Yazılı ihbarlar" ek={<Micro>{`${sayi(acik.length)} açık`}</Micro>} dolgusuz>
        <div className="px-3">
          <Amac>
            Afetzedelerin yazdığı ihbarlar, en acil olan önce. Model kategoriyi, aciliyeti ve metindeki
            adresi çıkardı; seçince metin işaretli olarak sağda açılır.
          </Amac>
          <HazirSecenekler etiket="İhbar süzgeci" secenekler={SUZGECLER} secili={suzgec} onSec={setSuzgec} />
          <SuAn>
            {ihbar.isPending
              ? 'Yükleniyor…'
              : acik.length
                ? `${sayi(acik.length)} açık yazılı ihbar${
                    bakilacak.length ? `; ${sayi(bakilacak.length)} tanesinde modelin sonucuna bakılmalı` : ''
                  }.`
                : 'Seçili zaman aralığında açık yazılı ihbar yok.'}
          </SuAn>
        </div>
        {ihbar.isError ? (
          <div className="px-3 py-3">
            <VeriYok ne="İhbarlar" neden="ihbar ucu yanıt vermedi" />
          </div>
        ) : liste.length ? (
          <div className="mt-2.5 border-t border-line">
            {liste.slice(0, KUYRUK_SINIRI).map((s) => (
              <MetinSatiri
                key={s.ihbar.id}
                satir={s}
                secili={secili?.tip === 'ihbar' && secili.id === s.ihbar.id}
                onSec={() => {
                  kayitSec({ tip: 'ihbar', id: s.ihbar.id })
                  // Metinden çözülen konumda çember sığsın diye düzeye göre.
                  ucus(s.ihbar.lon, s.ihbar.lat, s.ihbar.konumKaynagi === 'metin' ? ucusZoom(s.g?.konumDuzeyi) : 16)
                }}
              />
            ))}
            {liste.length > KUYRUK_SINIRI && (
              <p className="px-3 py-2 text-small text-ink-3">
                {`İlk ${KUYRUK_SINIRI} gösteriliyor (${sayi(liste.length)} ihbar). Zaman aralığını daraltın.`}
              </p>
            )}
          </div>
        ) : (
          !ihbar.isPending && (
            <p className="mt-2.5 border-t border-line px-3 py-2.5 text-small text-ink-3">Bu süzgeçte ihbar yok.</p>
          )
        )}
      </Bolum>
      <KendinIncelet />
    </>
  )
}

function MetinSatiri({ satir, secili, onSec }: { satir: Satir; secili: boolean; onSec: () => void }) {
  const { ihbar: i, g, neden } = satir
  const d = IHBAR_DURUMU[i.durum]
  const konum =
    g && !g.eski
      ? g.konumDuzeyi
        ? [DUZEY_ADI[g.konumDuzeyi], belirsizlikMetni(g.belirsizlikM), g.konumMetin].filter(Boolean).join(' · ')
        : 'Metinde adres yok'
      : (g?.konumMetin ?? null)
  return (
    <button
      type="button"
      onClick={onSec}
      aria-pressed={secili}
      className={sn(
        'block w-full border-b border-l-2 border-b-line px-3 py-2.5 text-left',
        secili ? 'border-l-ihbar-metin bg-raised' : 'border-l-transparent hover:bg-raised',
        i.durum === 'kapandi' && 'opacity-60',
      )}
    >
      <span className="flex items-center justify-between gap-2">
        <span className="flex min-w-0 items-center gap-2">
          {g?.aciliyet != null ? (
            <Rozet ton={ACILIYET_TONU(g.aciliyet)}>{`${g.aciliyet}/5`}</Rozet>
          ) : (
            <Rozet ton="nötr">—</Rozet>
          )}
          <span className="truncate text-small text-ink">{g?.ilgisiz ? 'Afetle ilgisiz' : (g?.kategori ?? i.etiket)}</span>
        </span>
        <Rozet ton={d.ton}>{d.ad}</Rozet>
      </span>
      <span className="mt-1 line-clamp-2 text-small text-ink-2">{i.metin}</span>
      <GorevOzetSatiri gorevler={i.gorevler} olayZamani={i.zaman} bekleyenYaz={false} />
      <span className="mt-1 flex justify-between gap-2 text-small text-ink-3">
        <span className="line-clamp-1">{konum ?? '—'}</span>
        <span className="shrink-0 font-mono">{tarihSaat(i.zaman)}</span>
      </span>
      {neden && i.durum !== 'kapandi' && (
        <span className="mt-1 flex items-center gap-1.5 text-small text-ink-2">
          <WarningCircle size={14} weight="bold" className="shrink-0 text-high" aria-hidden />
          Bak: {neden}
        </span>
      )}
    </button>
  )
}

/* ---- deneme --------------------------------------------------------------- */

const ORNEKLER = [
  { id: 'enkaz', etiket: 'Enkaz' },
  { id: 'medikal', etiket: 'Yaralı' },
  { id: 'ihtiyac', etiket: 'İhtiyaç' },
  { id: 'belirsiz', etiket: 'Adresi belirsiz' },
] as const
type OrnekId = (typeof ORNEKLER)[number]['id']

const ORNEK_METIN: Record<OrnekId, string> = {
  enkaz: 'Armutlu Mahallesi 5. Sokak’ta bina çöktü, iki kişi enkaz altında, ses geliyor.',
  medikal: 'Defne Elektrik mahallesinde yaralı var, kanaması durmuyor, ambulans giremiyor.',
  ihtiyac: 'Sümerler mahallesinde çadırdayız, su ve battaniye bitti, iki bebek var.',
  belirsiz: 'Atatürk Caddesi’nde bir apartman yan yatmış, içeride insanlar var.',
}

const METIN_SINIRI = 1000

function hataMetni(e: unknown): string {
  if (e instanceof ApiHatasi) {
    if (e.durum === 503) return 'Metin modeli şu an çalışmıyor; sunucu yöneticisine haber verin.'
    return e.message
  }
  return e instanceof Error ? e.message : 'Çözümlenemedi.'
}

function KendinIncelet() {
  const [metin, setMetin] = useState('')
  const [ornek, setOrnek] = useState<OrnekId | null>(null)
  const { ucus } = useHarita()
  const metinYaz = useCozumleme((d) => d.metinYaz)
  const kayitSec = useKonsol((d) => d.kayitSec)

  const coz = useMutation({
    mutationFn: (govde: { text: string }) => apiPost<MetinSonucu>('/api/nlp/analyze', govde),
    onSuccess: (sonuc, degisken) => {
      metinYaz(degisken.text, sonuc)
      // Sonuç sağda görünsün: seçili ihbar varsa bırakılır.
      kayitSec(null)
      if (sonuc.konum) ucus(sonuc.konum[1], sonuc.konum[0], ucusZoom(sonuc.konumDuzeyi))
    },
  })
  const kisa = metin.trim().length < 5

  return (
    <Bolum baslik="Metni kendin incelet">
      <Amac>
        Telefonla, telsizle gelen bir ihbarı ya da modelin bir cümleyi nasıl okuduğunu dene. Kayıt
        açılmaz, haritaya nokta yazılmaz.
      </Amac>
      <HazirSecenekler
        etiket="Örnek metinler"
        secenekler={ORNEKLER}
        secili={ornek}
        onSec={(id) => {
          setOrnek(id)
          setMetin(ORNEK_METIN[id])
        }}
      />
      <div className="mt-3 flex items-baseline justify-between gap-2">
        <label className="text-micro ls-micro text-ink-3 uppercase" htmlFor="ihbar-deneme">
          Metin
        </label>
        <span className="text-small text-ink-3">
          {metin.length}/{METIN_SINIRI}
        </span>
      </div>
      <textarea
        id="ihbar-deneme"
        rows={3}
        maxLength={METIN_SINIRI}
        value={metin}
        placeholder="Ne oldu, nerede, kaç kişi?"
        onChange={(e) => {
          setMetin(e.target.value)
          setOrnek(null)
        }}
        className="mt-1.5 w-full resize-none rounded-control border border-line-2 bg-sunken px-2.5 py-2 text-body text-ink"
      />
      <button
        type="button"
        disabled={kisa || coz.isPending}
        onClick={() => coz.mutate({ text: metin.trim() })}
        className="mt-2 w-full rounded-control border border-accent px-3 py-2 text-body font-semibold text-accent hover:bg-accent-soft disabled:opacity-40"
      >
        {coz.isPending ? 'İnceleniyor…' : 'İncelet'}
      </button>
      {coz.isError && (
        <p role="alert" className="mt-2 text-small text-crit">
          {hataMetni(coz.error)}
        </p>
      )}
      <Teknik>
        Kategori BERTurk sınıflandırıcısından gelir (modelin tahmini; seyrek kategorilerde zayıf). Adres
        yerel adres dizininden çözülür (OpenStreetMap: il, ilçe, mahalle, köy, sokak); metin dışarı
        gitmez. Dizinde olmayan ad uydurulmaz, notu düşülür. Hesap başına dakikada 30 inceleme.
      </Teknik>
    </Bolum>
  )
}

/* ---- sağ panel -------------------------------------------------------------- */

export function MetinSag() {
  const aralik = useSorguAraligi()
  const ihbar = useIhbarlar(aralik)
  const secili = useKonsol((d) => d.seciliKayit)
  const deneme = useCozumleme((d) => d.metin)
  const temizle = useCozumleme((d) => d.metinTemizle)

  const seciliIhbar =
    secili?.tip === 'ihbar' ? ihbar.data?.find((i) => i.id === secili.id && i.tur === 'metin') : undefined
  if (seciliIhbar) return <IhbarDetayi ihbar={seciliIhbar} />

  if (deneme) {
    return (
      <Bolum
        baslik="Deneme incelemesi"
        ek={
          <button type="button" onClick={temizle} className="text-small text-ink-3 hover:text-ink">
            Temizle
          </button>
        }
      >
        <p className="mb-3 text-small text-ink-3">
          {`Konsolda incelendi, ${tarihSaat(deneme.zaman)}. Kayıt açılmadı; haritadaki çember yalnız bu ekranda.`}
        </p>
        <MetinSonucKarti metin={deneme.girdi} g={denemeGorunumu(deneme.sonuc)} />
      </Bolum>
    )
  }

  return (
    <Bolum baslik="Yazılı ihbar">
      <Amac>
        Soldaki kuyruktan bir ihbar seç: metin, modelin bulduğu adres, kişi ve ihtiyaçlar işaretli olarak
        burada açılır; haritada konumun ne kadar sapabileceği çizilir.
      </Amac>
      <div className="mt-2">
        <VeriYok ne="Seçili ihbar" neden="henüz seçilmedi" />
      </div>
    </Bolum>
  )
}
