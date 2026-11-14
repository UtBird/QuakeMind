import { useId, useMemo, useState, type FormEvent, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { HazirSecenekler, Teknik, VeriYok } from '@/kabuk/Panel'
import { Micro, Rozet } from '@/kabuk/parcalar'
import { useOturum } from '@/kimlik/oturum'
import { ROL_ADI, type Rol } from '@/kimlik/roller'
import { ApiHatasi } from '@/veri/istemci'
import { useEkipler } from '@/veri/gorev'
import {
  useHesapAc,
  useHesapGuncelle,
  useHesapKayitlari,
  useKullanicilar,
  useSifreSifirla,
  type HesapGuncelleme,
  type HesapKaydi,
  type KullaniciSatiri,
} from '@/veri/kullanici'
import { sayi, tarihSaatYilli } from '@/lib/bicim'
import { sn } from '@/lib/sinif'

/* ---------------------------------------------------------------------------
   Hesap yönetimi — tam sayfa (J-155, J-156, J-157).

   Koordinasyonun bütün hesapları gördüğü, değiştirip KAYDETTİĞİ tek yer:
   · Tablo: herkes; rol, ekip, durum (aktif / askıda / şifre bekliyor), son giriş.
   · Çekmece: seçilen hesabı düzenle (ad, rol, ekip, durum → tek "Kaydet"),
     geçici şifre üret, o kişinin işlem geçmişi.
   · Yeni ekip hesabı: ekip seçilerek açılır; tek seferlik şifre bir kez görünür,
     kişi ilk girişte kendi şifresini koymak zorundadır.
   · Kayıt defteri: kim, kime, ne zaman, ne yaptı (silinmez).

   Kim neyi yapabilir SUNUCU söyler (`verebilecegiRoller`): koordinatör saha
   hesaplarını yönetir, yönetici hepsini; kimse kendi hesabında işlem yapamaz.
   Buradaki kilitler görünümdür; yetkiyi /api/oturum/* uçları denetler.
--------------------------------------------------------------------------- */

const ROL_SIRASI: Rol[] = ['afetzede', 'saha', 'koordinator', 'yonetici']

const ROL_TANIMI: Record<Rol, string> = {
  afetzede: 'Afetzede girişinden girer; yardım çağırır, ihbar gönderir',
  saha: 'Saha ekibi girişinden girer; ekibinin görevlerini görür',
  koordinator: 'Koordinasyon girişinden girer; konsolun tamamını görür',
  yonetici: 'Koordinasyon girişinden girer; ayrıca her rolü verir',
}

const KAPI_ADI: Record<Rol, string> = {
  afetzede: 'Afetzede',
  saha: 'Saha ekibi',
  koordinator: 'Koordinasyon',
  yonetici: 'Koordinasyon',
}

function hataMetni(e: unknown): string {
  if (e instanceof ApiHatasi) {
    if (e.durum === 401) return 'Oturumun kapanmış; yeniden giriş yap.'
    return e.message
  }
  if (e instanceof TypeError) return 'Sunucuya ulaşılamadı.'
  return e instanceof Error ? e.message : 'Bilinmeyen hata.'
}

const dugme =
  'rounded-control border border-line-2 px-2.5 py-1.5 text-small text-ink-2 hover:bg-hover hover:text-ink disabled:opacity-50'
const anaDugme =
  'rounded-control bg-accent px-3 py-2 text-body font-semibold text-accent-ink disabled:opacity-40'
const alanSinifi =
  'mt-1.5 w-full rounded-control border border-line-2 bg-sunken px-2.5 py-2 text-body text-ink disabled:opacity-50'

/* ------------------------------------------------------------ sayfa ---- */

const GRUPLAR = [
  { id: 'hepsi', etiket: 'Tümü' },
  { id: 'saha', etiket: 'Saha ekibi' },
  { id: 'ekipsiz', etiket: 'Ekibe bağlı olmayan saha' },
  { id: 'bekleyen', etiket: 'Şifresini koymamış' },
  { id: 'askida', etiket: 'Askıda' },
  { id: 'koordinasyon', etiket: 'Koordinasyon' },
  { id: 'afetzede', etiket: 'Afetzede' },
] as const
type GrupId = (typeof GRUPLAR)[number]['id']

const SUZGEC: Record<GrupId, (k: KullaniciSatiri) => boolean> = {
  hepsi: () => true,
  saha: (k) => k.rol === 'saha',
  ekipsiz: (k) => k.rol === 'saha' && !k.ekipId && !k.askida,
  bekleyen: (k) => k.sifreDegismeli && !k.askida,
  askida: (k) => k.askida,
  koordinasyon: (k) => k.rol === 'koordinator' || k.rol === 'yonetici',
  afetzede: (k) => k.rol === 'afetzede',
}

type Cekmece = { tur: 'yeni' } | { tur: 'duzenle'; id: string } | null

export function HesapYonetimi() {
  const liste = useKullanicilar()
  const ekipler = useEkipler()
  const [sekme, setSekme] = useState<'hesaplar' | 'defter'>('hesaplar')
  const [grup, setGrup] = useState<GrupId>('hepsi')
  const [arama, setArama] = useState('')
  const [cekmece, setCekmece] = useState<Cekmece>(null)

  const ekipAdi = useMemo(
    () => new Map((ekipler.data ?? []).map((e) => [e.id, e.ad])),
    [ekipler.data],
  )
  const tumu = liste.data?.kullanicilar ?? []
  const aranan = arama.trim().toLocaleLowerCase('tr-TR')
  const gorunen = tumu
    .filter(SUZGEC[grup])
    .filter(
      (k) =>
        !aranan ||
        k.adSoyad.toLocaleLowerCase('tr-TR').includes(aranan) ||
        k.eposta.toLocaleLowerCase('tr-TR').includes(aranan),
    )
  const ekipsizSayi = tumu.filter(SUZGEC.ekipsiz).length
  const secili =
    cekmece?.tur === 'duzenle' ? tumu.find((k) => k.id === cekmece.id) ?? null : null
  const yetkisiz = liste.error instanceof ApiHatasi && liste.error.durum === 403

  return (
    <div className="mx-auto w-full max-w-7xl p-gutter">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-title text-ink">Hesaplar</h1>
          <p className="mt-1 max-w-3xl text-small text-ink-2">
            Ekip ve koordinasyon hesaplarını sen açarsın; afetzedeler kendi hesabını giriş ekranından
            açar. Bir satıra tıkla: rolünü, ekibini ve durumunu değiştir, kaydet. Her işlem kayıt
            defterine yazılır.
          </p>
        </div>
        <button
          type="button"
          disabled={yetkisiz || liste.isPending}
          onClick={() => {
            setSekme('hesaplar')
            setCekmece({ tur: 'yeni' })
          }}
          className={anaDugme}
        >
          Yeni ekip hesabı
        </button>
      </header>

      <div role="tablist" aria-label="Görünüm" className="mt-4 flex gap-1 border-b border-line">
        {(
          [
            ['hesaplar', `Hesaplar · ${sayi(tumu.length)}`],
            ['defter', 'Kayıt defteri'],
          ] as const
        ).map(([id, etiket]) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={sekme === id}
            onClick={() => setSekme(id)}
            className={sn(
              '-mb-px border-b-2 px-3 py-2 text-body transition-colors duration-150 ease-out-qm',
              sekme === id ? 'border-accent text-ink' : 'border-transparent text-ink-2 hover:text-ink',
            )}
          >
            {etiket}
          </button>
        ))}
      </div>

      {sekme === 'defter' ? (
        <KayitDefteri ekipAdi={ekipAdi} />
      ) : yetkisiz ? (
        <div className="mt-4">
          <VeriYok ne="Hesap listesi" neden="bu sayfayı yalnız koordinatör ve yönetici görür" />
        </div>
      ) : (
        <>
          {ekipsizSayi > 0 && grup !== 'ekipsiz' && (
            <div className="mt-3 flex flex-wrap items-center gap-2 rounded-control border border-accent bg-accent-soft px-3 py-2 text-small text-ink">
              <span>
                {sayi(ekipsizSayi)} saha hesabı hiçbir ekibe bağlı değil; bu kişiler görev göremez.
              </span>
              <button type="button" onClick={() => setGrup('ekipsiz')} className={dugme}>
                Göster
              </button>
            </div>
          )}

          <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
            <HazirSecenekler
              etiket="Hesap grupları"
              secenekler={GRUPLAR.map((g) => ({
                ...g,
                etiket: `${g.etiket} · ${sayi(tumu.filter(SUZGEC[g.id]).length)}`,
              }))}
              secili={grup}
              onSec={setGrup}
            />
            <input
              value={arama}
              onChange={(e) => setArama(e.target.value)}
              placeholder="ad ya da e-posta ara"
              aria-label="Ad ya da e-posta ara"
              className="mt-2.5 w-full max-w-xs rounded-control border border-line-2 bg-sunken px-2.5 py-2 text-body text-ink"
            />
          </div>

          <div className="mt-3 flex flex-col gap-gutter genis:flex-row genis:items-start">
            <div className="min-w-0 flex-1 overflow-x-auto rounded-panel border border-line bg-panel">
              {liste.isPending ? (
                <p className="p-3 text-small text-ink-3">Yükleniyor…</p>
              ) : liste.isError ? (
                <div className="p-3">
                  <VeriYok ne="Hesap listesi" neden={hataMetni(liste.error)} />
                </div>
              ) : gorunen.length === 0 ? (
                <div className="p-3">
                  <VeriYok ne="Bu grup" neden={aranan ? 'aramaya uyan hesap yok' : 'bu grupta hesap yok'} />
                </div>
              ) : (
                <HesapTablosu
                  satirlar={gorunen}
                  ekipAdi={ekipAdi}
                  seciliId={secili?.id ?? null}
                  benimId={liste.data?.benimId ?? ''}
                  onSec={(id) => setCekmece({ tur: 'duzenle', id })}
                />
              )}
            </div>

            {cekmece && (
              <aside
                aria-label={cekmece.tur === 'yeni' ? 'Yeni ekip hesabı' : 'Hesabı düzenle'}
                className="w-full shrink-0 rounded-panel border border-line bg-panel genis:sticky genis:top-gutter genis:w-panel-r"
              >
                {cekmece.tur === 'yeni' ? (
                  <YeniHesap
                    verebilir={liste.data?.verebilecegiRoller ?? []}
                    onKapat={() => setCekmece(null)}
                    onAcildi={(id) => setCekmece({ tur: 'duzenle', id })}
                  />
                ) : secili ? (
                  <HesapDuzenle
                    key={secili.id}
                    k={secili}
                    ben={secili.id === liste.data?.benimId}
                    verebilir={liste.data?.verebilecegiRoller ?? []}
                    ekipAdi={ekipAdi}
                    onKapat={() => setCekmece(null)}
                  />
                ) : (
                  <div className="p-3">
                    <VeriYok ne="Seçili hesap" neden="listede yok" />
                  </div>
                )}
              </aside>
            )}
          </div>

          <Teknik>
            Rol, ekip ve durum sunucuda veritabanından okunur; kaydettiğin an geçerlidir. Rolü
            değişen ya da askıya alınan kişinin açık oturumları kapanır. Liste canlı akışla
            tazelenir: başka bir koordinatörün değişikliği de burada görünür.
          </Teknik>
        </>
      )}
    </div>
  )
}

/* ------------------------------------------------------------ tablo ---- */

function DurumRozeti({ k }: { k: KullaniciSatiri }) {
  if (k.askida) return <Rozet ton="nötr">Askıda</Rozet>
  if (k.sifreDegismeli) return <Rozet ton="accent">Şifre bekliyor</Rozet>
  return <span className="text-small text-ink-2">Aktif</span>
}

function HesapTablosu({
  satirlar,
  ekipAdi,
  seciliId,
  benimId,
  onSec,
}: {
  satirlar: KullaniciSatiri[]
  ekipAdi: Map<string, string>
  seciliId: string | null
  benimId: string
  onSec: (id: string) => void
}) {
  const baslik = 'px-3 py-2 text-left'
  return (
    <table className="w-full min-w-max border-collapse">
      <thead className="border-b border-line">
        <tr>
          <th className={baslik}><Micro>Ad soyad</Micro></th>
          <th className={baslik}><Micro>Rol</Micro></th>
          <th className={baslik}><Micro>Ekip</Micro></th>
          <th className={baslik}><Micro>Durum</Micro></th>
          <th className={baslik}><Micro>Son giriş</Micro></th>
          <th className={baslik}><span className="sr-only">İşlem</span></th>
        </tr>
      </thead>
      <tbody>
        {satirlar.map((k) => (
          <tr
            key={k.id}
            onClick={() => onSec(k.id)}
            aria-selected={seciliId === k.id}
            className={sn(
              'cursor-pointer border-b border-line last:border-b-0',
              seciliId === k.id ? 'bg-raised' : 'hover:bg-hover',
              k.askida && 'opacity-60',
            )}
          >
            <td className="px-3 py-2">
              <span className="block text-body text-ink">
                {k.adSoyad}
                {k.id === benimId && <span className="ml-1.5 text-small text-ink-3">(sen)</span>}
              </span>
              <span className="block text-small text-ink-3">{k.eposta}</span>
            </td>
            <td className="px-3 py-2 text-body text-ink-2">{ROL_ADI[k.rol]}</td>
            <td className="px-3 py-2 text-body">
              {k.rol !== 'saha' ? (
                <span className="text-ink-3">—</span>
              ) : k.ekipId ? (
                <span className="text-ink">{ekipAdi.get(k.ekipId) ?? k.ekipId}</span>
              ) : (
                <span className="font-semibold text-ink">Ekip yok</span>
              )}
            </td>
            <td className="px-3 py-2">
              <DurumRozeti k={k} />
            </td>
            <td className="px-3 py-2 text-small text-ink-2">
              {k.sonGiris ? tarihSaatYilli(k.sonGiris) : 'henüz girmedi'}
            </td>
            <td className="px-3 py-2 text-right">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  onSec(k.id)
                }}
                className={dugme}
              >
                {k.id === benimId ? 'Gör' : 'Düzenle'}
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

/* -------------------------------------------------- tek seferlik şifre ---- */

function GeciciSifreKarti({
  baslik,
  eposta,
  sifre,
  kapi,
  onKapat,
}: {
  baslik: string
  eposta: string
  sifre: string
  kapi: string
  onKapat: () => void
}) {
  const [kopyalandi, setKopyalandi] = useState<boolean | null>(null)
  async function kopyala() {
    try {
      await navigator.clipboard.writeText(`E-posta: ${eposta}\nGeçici şifre: ${sifre}\nGiriş: ${kapi}`)
      setKopyalandi(true)
    } catch {
      setKopyalandi(false)
    }
  }
  return (
    <div role="status" className="rounded-control border border-accent bg-accent-soft px-2.5 py-2.5">
      <p className="text-body font-semibold text-ink">{baslik}</p>
      <dl className="mt-1.5 text-small">
        <div className="flex items-baseline gap-2.5">
          <dt className="w-14 shrink-0 text-ink-3">E-posta</dt>
          <dd className="min-w-0 truncate text-ink">{eposta}</dd>
        </div>
        <div className="mt-1 flex items-baseline gap-2.5">
          <dt className="w-14 shrink-0 text-ink-3">Şifre</dt>
          <dd className="font-mono text-body text-ink select-all">{sifre}</dd>
        </div>
        <div className="mt-1 flex items-baseline gap-2.5">
          <dt className="w-14 shrink-0 text-ink-3">Giriş</dt>
          <dd className="text-ink">“{kapi}” seçilerek</dd>
        </div>
      </dl>
      <p className="mt-1.5 text-small text-ink-2">
        Bu şifre bir daha gösterilmez. Kişi ilk girişte kendi şifresini koymak zorunda.
      </p>
      <div className="mt-2 flex gap-1.5">
        <button type="button" onClick={kopyala} className={sn(anaDugme, 'flex-1 py-1.5')}>
          {kopyalandi ? 'Kopyalandı' : 'Bilgileri kopyala'}
        </button>
        <button type="button" onClick={onKapat} className={dugme}>
          Not aldım
        </button>
      </div>
      {kopyalandi === false && (
        <p className="mt-1.5 text-small text-ink-2">Tarayıcı panoya izin vermedi; şifreyi elle not al.</p>
      )}
    </div>
  )
}

function CekmeceBasligi({ baslik, alt, onKapat }: { baslik: string; alt?: ReactNode; onKapat: () => void }) {
  return (
    <div className="flex items-start justify-between gap-2 border-b border-line px-3 py-2.5">
      <div className="min-w-0">
        <p className="truncate text-subtitle text-ink">{baslik}</p>
        {alt && <p className="truncate text-small text-ink-3">{alt}</p>}
      </div>
      <button type="button" onClick={onKapat} aria-label="Kapat" className={dugme}>
        Kapat
      </button>
    </div>
  )
}

/* ------------------------------------------------------- yeni hesap ---- */

const HESAP_TURLERI = [
  { id: 'saha', etiket: 'Saha ekibi üyesi' },
  { id: 'koordinator', etiket: 'Koordinatör' },
  { id: 'yonetici', etiket: 'Yönetici' },
] as const
type HesapTuru = (typeof HESAP_TURLERI)[number]['id']

function YeniHesap({
  verebilir,
  onKapat,
  onAcildi,
}: {
  verebilir: Rol[]
  onKapat: () => void
  onAcildi: (id: string) => void
}) {
  const kimlik = useId()
  const ekipler = useEkipler()
  const ac = useHesapAc()
  const turler = HESAP_TURLERI.filter((t) => verebilir.includes(t.id))
  const [tur, setTur] = useState<HesapTuru>('saha')
  const [adSoyad, setAdSoyad] = useState('')
  const [eposta, setEposta] = useState('')
  const [ekipId, setEkipId] = useState('')
  const [acilan, setAcilan] = useState<{ id: string; ad: string; eposta: string; sifre: string; rol: Rol } | null>(
    null,
  )

  const eksik = [
    adSoyad.trim().length < 2 && 'ad soyad',
    !eposta.includes('@') && 'e-posta',
  ].filter(Boolean)

  function gonder(e: FormEvent) {
    e.preventDefault()
    if (eksik.length) return
    ac.mutate(
      {
        eposta: eposta.trim(),
        adSoyad: adSoyad.trim(),
        rol: tur,
        ekipId: tur === 'saha' && ekipId ? ekipId : undefined,
      },
      {
        onSuccess: (y) => {
          setAcilan({
            id: y.kullanici.id,
            ad: y.kullanici.adSoyad,
            eposta: y.kullanici.eposta,
            sifre: y.geciciSifre,
            rol: y.kullanici.rol,
          })
          setAdSoyad('')
          setEposta('')
        },
      },
    )
  }

  if (acilan) {
    return (
      <>
        <CekmeceBasligi baslik="Hesap açıldı" alt={`${acilan.ad} · ${ROL_ADI[acilan.rol]}`} onKapat={onKapat} />
        <div className="p-3">
          <GeciciSifreKarti
            baslik="Kişiye ilet"
            eposta={acilan.eposta}
            sifre={acilan.sifre}
            kapi={KAPI_ADI[acilan.rol]}
            onKapat={() => onAcildi(acilan.id)}
          />
          <button type="button" onClick={() => setAcilan(null)} className={sn(dugme, 'mt-2 w-full')}>
            Bir hesap daha aç
          </button>
        </div>
      </>
    )
  }

  return (
    <>
      <CekmeceBasligi baslik="Yeni ekip hesabı" alt="Şifreyi sunucu üretir" onKapat={onKapat} />
      <form onSubmit={gonder} className="p-3" aria-label="Yeni hesap aç">
        <Micro>Hesap türü</Micro>
        <HazirSecenekler
          etiket="Hesap türü"
          secenekler={turler}
          secili={tur}
          onSec={(id) => {
            setTur(id)
            ac.reset()
          }}
        />
        <p className="mt-1.5 text-small text-ink-3">{ROL_TANIMI[tur]}.</p>

        <label htmlFor={`${kimlik}-ad`} className="mt-3 block">
          <Micro>Ad soyad</Micro>
        </label>
        <input
          id={`${kimlik}-ad`}
          value={adSoyad}
          autoComplete="off"
          onChange={(e) => setAdSoyad(e.target.value)}
          className={alanSinifi}
        />

        <label htmlFor={`${kimlik}-ep`} className="mt-3 block">
          <Micro>E-posta</Micro>
        </label>
        <input
          id={`${kimlik}-ep`}
          type="email"
          value={eposta}
          autoComplete="off"
          onChange={(e) => setEposta(e.target.value)}
          className={alanSinifi}
        />

        {tur === 'saha' && (
          <>
            <label htmlFor={`${kimlik}-ekip`} className="mt-3 block">
              <Micro>Ekibi</Micro>
            </label>
            <select
              id={`${kimlik}-ekip`}
              value={ekipId}
              onChange={(e) => setEkipId(e.target.value)}
              className={alanSinifi}
            >
              <option value="">Şimdilik ekip yok</option>
              {(ekipler.data ?? []).map((e) => (
                <option key={e.id} value={e.id}>
                  {e.ad}
                </option>
              ))}
            </select>
            <p className="mt-1 text-small text-ink-3">
              {ekipId
                ? 'Kişi girişte doğrudan bu ekibin görevlerini görür.'
                : 'Ekipsiz saha hesabı görev göremez; sonra bu sayfadan bağlarsın.'}
            </p>
          </>
        )}

        <button
          type="submit"
          disabled={turler.length === 0 || eksik.length > 0 || ac.isPending}
          className={sn(anaDugme, 'mt-3 w-full')}
        >
          {ac.isPending ? 'Açılıyor…' : 'Hesabı aç ve şifre üret'}
        </button>
        {ac.isError && (
          <p role="alert" className="mt-2 text-small text-crit">
            Hesap açılamadı: {hataMetni(ac.error)}
          </p>
        )}
        <p className="mt-2 text-small text-ink-3">
          Koordinatör yalnız saha hesabı açar; koordinatör ve yönetici hesabını yönetici açar.
        </p>
      </form>
    </>
  )
}

/* ------------------------------------------------------ düzenleme ---- */

function HesapDuzenle({
  k,
  ben,
  verebilir,
  ekipAdi,
  onKapat,
}: {
  k: KullaniciSatiri
  ben: boolean
  verebilir: Rol[]
  ekipAdi: Map<string, string>
  onKapat: () => void
}) {
  const kimlik = useId()
  const ekipler = useEkipler()
  const kaydet = useHesapGuncelle()
  const sifirla = useSifreSifirla()
  const gecmis = useHesapKayitlari(k.id)
  const { oturum } = useOturum()

  const yonetir = !ben && verebilir.includes(k.rol)
  const rolSecenekleri = [k.rol, ...ROL_SIRASI.filter((r) => r !== k.rol && verebilir.includes(r))]

  const [ad, setAd] = useState(k.adSoyad)
  const [rol, setRol] = useState<Rol>(k.rol)
  const [ekipId, setEkipId] = useState<string>(k.ekipId ?? '')
  const [askida, setAskida] = useState(k.askida)
  const [sifreSor, setSifreSor] = useState(false)
  const [yeniSifre, setYeniSifre] = useState<string | null>(null)
  const [kaydedildi, setKaydedildi] = useState(false)

  // Rol saha değilse ekip anlamsız: sunucu da ekipten çıkarır.
  const sonEkip = rol === 'saha' ? ekipId || null : null
  const ekipAd = (id: string | null) => (id ? ekipAdi.get(id) ?? id : 'yok')

  const degisiklik: HesapGuncelleme = {}
  const ozet: string[] = []
  if (ad.trim() !== k.adSoyad) {
    degisiklik.adSoyad = ad.trim()
    ozet.push(`ad “${ad.trim()}”`)
  }
  if (rol !== k.rol) {
    degisiklik.rol = rol
    ozet.push(`rol ${ROL_ADI[k.rol]} → ${ROL_ADI[rol]}`)
  }
  // Rol saha'dan çıkıyorsa ekip sunucuda zaten düşer; ayrıca gönderilmez.
  if (rol === 'saha' && sonEkip !== k.ekipId) {
    degisiklik.ekipId = sonEkip
    ozet.push(`ekip ${ekipAd(k.ekipId)} → ${ekipAd(sonEkip)}`)
  } else if (rol !== 'saha' && k.ekipId) {
    ozet.push('ekipten çıkar')
  }
  if (askida !== k.askida) {
    degisiklik.askida = askida
    ozet.push(askida ? 'askıya alınır' : 'yeniden etkinleşir')
  }
  const adGecersiz = ad.trim().length < 2
  const oturumDuser = degisiklik.rol !== undefined || degisiklik.askida !== undefined

  function kaydetGonder() {
    kaydet.mutate(
      { id: k.id, ...degisiklik },
      {
        onSuccess: () => setKaydedildi(true),
      },
    )
  }

  return (
    <>
      <CekmeceBasligi baslik={k.adSoyad} alt={k.eposta} onKapat={onKapat} />
      <div className="p-3">
        <div className="flex flex-wrap items-center gap-1.5">
          <Rozet ton={k.rol === 'afetzede' ? 'nötr' : 'accent'}>{ROL_ADI[k.rol]}</Rozet>
          <DurumRozeti k={k} />
        </div>
        <p className="mt-1.5 text-small text-ink-3">
          {k.olusturuldu ? `Açıldı ${tarihSaatYilli(k.olusturuldu)} · ` : ''}
          {k.sonGiris ? `son giriş ${tarihSaatYilli(k.sonGiris)}` : 'henüz girmedi'}
        </p>
        {k.sifreDegismeli && !k.askida && (
          <p className="mt-1.5 text-small text-ink-2">
            Geçici şifreyle bekliyor: ilk girişte kendi şifresini koyacak.
          </p>
        )}

        {ben ? (
          <p className="mt-3 text-small text-ink-2">
            Bu senin hesabın; rolünü ve durumunu kendin değiştiremezsin.{' '}
            {oturum && (
              <Link to="/sifre-degistir" className="text-accent underline">
                Şifreni değiştir
              </Link>
            )}
          </p>
        ) : !yonetir ? (
          <p className="mt-3 text-small text-ink-2">Bu hesabı yalnız yönetici yönetir.</p>
        ) : (
          <>
            <label htmlFor={`${kimlik}-ad`} className="mt-3 block">
              <Micro>Ad soyad</Micro>
            </label>
            <input
              id={`${kimlik}-ad`}
              value={ad}
              onChange={(e) => {
                setAd(e.target.value)
                setKaydedildi(false)
              }}
              className={alanSinifi}
            />

            <label htmlFor={`${kimlik}-rol`} className="mt-3 block">
              <Micro>Rol</Micro>
            </label>
            <select
              id={`${kimlik}-rol`}
              value={rol}
              onChange={(e) => {
                setRol(e.target.value as Rol)
                setKaydedildi(false)
              }}
              className={alanSinifi}
            >
              {rolSecenekleri.map((r) => (
                <option key={r} value={r}>
                  {ROL_ADI[r]}
                </option>
              ))}
            </select>
            <p className="mt-1 text-small text-ink-3">{ROL_TANIMI[rol]}.</p>

            {rol === 'saha' && (
              <>
                <label htmlFor={`${kimlik}-ekip`} className="mt-3 block">
                  <Micro>Ekibi</Micro>
                </label>
                <select
                  id={`${kimlik}-ekip`}
                  value={ekipId}
                  onChange={(e) => {
                    setEkipId(e.target.value)
                    setKaydedildi(false)
                  }}
                  className={alanSinifi}
                >
                  <option value="">Ekip yok</option>
                  {(ekipler.data ?? []).map((e) => (
                    <option key={e.id} value={e.id}>
                      {e.ad}
                    </option>
                  ))}
                </select>
                {!ekipId && <p className="mt-1 text-small text-ink">Ekipsiz saha hesabı görev göremez.</p>}
              </>
            )}

            <Micro className="mt-3 block">Durum</Micro>
            <div role="radiogroup" aria-label="Hesap durumu" className="mt-1.5 grid grid-cols-2 gap-1.5">
              {(
                [
                  [false, 'Aktif'],
                  [true, 'Askıda'],
                ] as const
              ).map(([deger, etiket]) => (
                <button
                  key={etiket}
                  type="button"
                  role="radio"
                  aria-checked={askida === deger}
                  onClick={() => {
                    setAskida(deger)
                    setKaydedildi(false)
                  }}
                  className={sn(
                    'rounded-control border px-2 py-1.5 text-body',
                    askida === deger ? 'border-accent bg-accent-soft text-ink' : 'border-line-2 text-ink-2 hover:bg-hover',
                  )}
                >
                  {etiket}
                </button>
              ))}
            </div>
            <p className="mt-1 text-small text-ink-3">
              Askıdaki hesap giremez, açık oturumu hemen kapanır; kayıtları silinmez, geri açılabilir.
            </p>

            <div className="mt-3 rounded-control border border-line-2 px-2.5 py-2">
              <p className="text-small text-ink">
                {ozet.length
                  ? `Kaydedince: ${ozet.join(' · ')}.${oturumDuser ? ' Açık oturumu kapanır.' : ''}`
                  : kaydedildi
                    ? 'Kaydedildi.'
                    : 'Değişiklik yok.'}
              </p>
              <div className="mt-2 flex gap-1.5">
                <button
                  type="button"
                  disabled={ozet.length === 0 || adGecersiz || kaydet.isPending}
                  onClick={kaydetGonder}
                  className={sn(anaDugme, 'flex-1 py-1.5')}
                >
                  {kaydet.isPending ? 'Kaydediliyor…' : 'Kaydet'}
                </button>
                <button
                  type="button"
                  disabled={ozet.length === 0 || kaydet.isPending}
                  onClick={() => {
                    setAd(k.adSoyad)
                    setRol(k.rol)
                    setEkipId(k.ekipId ?? '')
                    setAskida(k.askida)
                  }}
                  className={dugme}
                >
                  Geri al
                </button>
              </div>
              {adGecersiz && <p className="mt-1.5 text-small text-ink-2">Ad soyad en az 2 harf olmalı.</p>}
              {kaydet.isError && (
                <p role="alert" className="mt-1.5 text-small text-crit">
                  Kaydedilmedi: {hataMetni(kaydet.error)}
                </p>
              )}
            </div>

            <Micro className="mt-4 block">Şifre</Micro>
            {yeniSifre ? (
              <div className="mt-1.5">
                <GeciciSifreKarti
                  baslik="Yeni geçici şifre"
                  eposta={k.eposta}
                  sifre={yeniSifre}
                  kapi={KAPI_ADI[k.rol]}
                  onKapat={() => setYeniSifre(null)}
                />
              </div>
            ) : sifreSor ? (
              <div className="mt-1.5 rounded-control border border-line-2 px-2.5 py-2">
                <p className="text-small text-ink">
                  Yeni geçici şifre üretilsin mi? Eski şifre hemen geçersiz olur, açık oturumu kapanır;
                  kişi girişte kendi şifresini koymak zorunda kalır.
                </p>
                <div className="mt-2 flex gap-1.5">
                  <button
                    type="button"
                    disabled={sifirla.isPending}
                    onClick={() =>
                      sifirla.mutate(k.id, {
                        onSuccess: (y) => {
                          setYeniSifre(y.geciciSifre)
                          setSifreSor(false)
                        },
                      })
                    }
                    className={sn(anaDugme, 'flex-1 py-1.5')}
                  >
                    {sifirla.isPending ? 'Üretiliyor…' : 'Evet, üret'}
                  </button>
                  <button type="button" onClick={() => setSifreSor(false)} className={dugme}>
                    Vazgeç
                  </button>
                </div>
                {sifirla.isError && (
                  <p role="alert" className="mt-1.5 text-small text-crit">
                    Üretilemedi: {hataMetni(sifirla.error)}
                  </p>
                )}
              </div>
            ) : (
              <button type="button" onClick={() => setSifreSor(true)} className={sn(dugme, 'mt-1.5')}>
                Unuttu: yeni geçici şifre üret
              </button>
            )}
          </>
        )}

        <Micro className="mt-4 block">Geçmiş</Micro>
        <div className="mt-1.5">
          {gecmis.isPending ? (
            <p className="text-small text-ink-3">Yükleniyor…</p>
          ) : gecmis.isError ? (
            <VeriYok ne="Geçmiş" neden={hataMetni(gecmis.error)} />
          ) : (gecmis.data ?? []).length === 0 ? (
            <VeriYok ne="Geçmiş" neden="bu hesapta kayıtlı işlem yok (kayıt defteri 13 Kasım 2026'da başladı)" />
          ) : (
            <ul>
              {gecmis.data!.map((g) => (
                <li key={g.id} className="border-b border-line py-1.5 last:border-b-0">
                  <span className="block text-small text-ink">{islemMetni(g, ekipAdi)}</span>
                  <span className="block text-small text-ink-3">
                    {tarihSaatYilli(g.zaman)} · {g.yapanId === g.hedefId ? 'kendisi' : g.yapanAd ?? 'bilinmiyor'}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </>
  )
}

/* ---------------------------------------------------- kayıt defteri ---- */

function islemMetni(g: HesapKaydi, ekipAdi: Map<string, string>): string {
  const a = g.ayrinti ?? {}
  const rol = (r: unknown) => (typeof r === 'string' && r in ROL_ADI ? ROL_ADI[r as Rol] : String(r ?? '—'))
  const ekip = (e: unknown) => (typeof e === 'string' ? ekipAdi.get(e) ?? e : 'yok')
  switch (g.islem) {
    case 'hesap-acildi':
      return `${rol(a.rol)} hesabı açıldı${a.ekipId ? ` · ekip ${ekip(a.ekipId)}` : ' · ekipsiz'}`
    case 'rol-degisti':
      return `Rol: ${rol(a.once)} → ${rol(a.sonra)}`
    case 'ekip-degisti':
      return `Ekip: ${ekip(a.once)} → ${ekip(a.sonra)}`
    case 'ad-degisti':
      return `Ad: “${String(a.once ?? '')}” → “${String(a.sonra ?? '')}”`
    case 'askiya-alindi':
      return 'Askıya alındı'
    case 'etkinlestirildi':
      return 'Yeniden etkinleştirildi'
    case 'sifre-yenilendi':
      return 'Geçici şifre üretildi'
    case 'sifre-degistirildi':
      return a.geciciydi ? 'Geçici şifre yerine kendi şifresini koydu' : 'Şifresini değiştirdi'
  }
}

function KayitDefteri({ ekipAdi }: { ekipAdi: Map<string, string> }) {
  const defter = useHesapKayitlari(null)
  const baslik = 'px-3 py-2 text-left'
  return (
    <div className="mt-3">
      <p className="text-small text-ink-2">
        Kim, kime, ne zaman, ne yaptı. Kayıtlar silinmez ve değiştirilmez; en yeni 200 işlem.
      </p>
      <div className="mt-3 overflow-x-auto rounded-panel border border-line bg-panel">
        {defter.isPending ? (
          <p className="p-3 text-small text-ink-3">Yükleniyor…</p>
        ) : defter.isError ? (
          <div className="p-3">
            <VeriYok ne="Kayıt defteri" neden={hataMetni(defter.error)} />
          </div>
        ) : (defter.data ?? []).length === 0 ? (
          <div className="p-3">
            <VeriYok ne="Kayıt defteri" neden="henüz hesap işlemi yapılmadı" />
          </div>
        ) : (
          <table className="w-full min-w-max border-collapse">
            <thead className="border-b border-line">
              <tr>
                <th className={baslik}><Micro>Zaman</Micro></th>
                <th className={baslik}><Micro>Yapan</Micro></th>
                <th className={baslik}><Micro>Hesap</Micro></th>
                <th className={baslik}><Micro>İşlem</Micro></th>
              </tr>
            </thead>
            <tbody>
              {defter.data!.map((g) => (
                <tr key={g.id} className="border-b border-line last:border-b-0">
                  <td className="px-3 py-2 text-small text-ink-2">{tarihSaatYilli(g.zaman)}</td>
                  <td className="px-3 py-2 text-body text-ink">
                    {g.yapanId === g.hedefId ? 'Kendisi' : g.yapanAd ?? 'bilinmiyor'}
                  </td>
                  <td className="px-3 py-2">
                    <span className="block text-body text-ink">{g.hedefAd ?? '—'}</span>
                    <span className="block text-small text-ink-3">{g.hedefEposta}</span>
                  </td>
                  <td className="px-3 py-2 text-body text-ink">{islemMetni(g, ekipAdi)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
