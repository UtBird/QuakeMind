import { Fragment, useState } from 'react'
import { CaretDown, CaretRight } from '@phosphor-icons/react'
import { HazirSecenekler, VeriYok } from '@/kabuk/Panel'
import { Micro, Rozet } from '@/kabuk/parcalar'
import { ROL_ADI } from '@/kimlik/roller'
import { ApiHatasi } from '@/veri/istemci'
import {
  ISLEM_GRUPLARI,
  ISLEM_TURU,
  useIslemKayitlari,
  useSonZincirDenetimi,
  useZinciriDogrula,
  type IslemGrubu,
  type IslemKaydi,
  type ZincirDenetimi,
} from '@/veri/islemKaydi'
import { sayi, tarihSaatYilli } from '@/lib/bicim'
import { sn } from '@/lib/sinif'

/* İşlem kaydı (J-165): kim, ne zaman, ne yaptı.

   Analizler (kamera, metin, hasar, tatbikat), sevk ve görev adımları, SOS ve
   ihbar kapatma, ekip tanımı ve bildirimler tek listede. Kayıt silinmez ve
   değiştirilmez (veritabanı tetikleyicisi reddeder). Fotoğraf saklanmaz,
   yalnız sonucun özeti. Hesap işlemleri ayrı defterde (J-157). */

function hataMetni(e: unknown): string {
  if (e instanceof ApiHatasi && e.durum === 403) return 'bu kaydı yalnız koordinatör ve yönetici görür'
  return e instanceof Error ? e.message : 'sunucu yanıt vermedi'
}

/** Ayrıntı alanının okunur adı; bilinmeyen anahtar olduğu gibi yazılır. */
const ALAN_ADI: Record<string, string> = {
  model: 'Model',
  modeller: 'Çalışan modeller',
  tespitSayisi: 'Tespit sayısı',
  siniflar: 'Sınıflar',
  enYuksekGuven: 'En yüksek güven (%)',
  durum: 'Durum',
  en: 'Genişlik (px)',
  boy: 'Yükseklik (px)',
  sureMs: 'Süre (ms)',
  konumVar: 'Konum gönderildi mi',
  tespitler: 'Tespitler',
  metin: 'Metin',
  ilgili: 'Afetle ilgili mi',
  kategori: 'Kategori',
  aciliyet: 'Aciliyet',
  guven: 'Güven',
  konumMetin: 'Bulunan konum',
  konum: 'Koordinat',
  sehir: 'Şehir',
  kaynak: 'Kaynak',
  goruntu: 'Görüntü',
  kutu: 'Alan',
  yakinCekim: 'Yakın çekim',
  kapaliYol: 'Kapalı yol parçası',
  acikYol: 'Açık yol parçası',
  hasarOrani: 'Hasar oranı',
  zoom: 'Kullanılan zoom',
  istenenZoom: 'İstenen zoom',
  esik: 'Eşik',
  hata: 'Hata',
  alan: 'Alan',
  katman: 'Katman',
  silinenHasarNoktasi: 'Silinen tatbikat noktası',
  gorevId: 'Görev',
  ekipId: 'Ekip',
  kisiSayisi: 'Kişi sayısı',
  bitenGorevler: 'Biten görevler',
  oncelik: 'Öncelik',
  tur: 'Tür',
  degisen: 'Değişenler',
  eklenen: 'Eklenen hesaplar',
  cikan: 'Çıkarılan hesaplar',
  onem: 'Önem',
  baslik: 'Başlık',
  // J-166
  kapi: 'Giriş kapısı',
  ip: 'Bağlanan adres',
  tarayici: 'Tarayıcı',
  yonlendirilen: 'Vekilin ilettiği adres (doğrulanmamış)',
  neden: 'Neden',
  eposta: 'Denenen e-posta',
  kayitSayisi: 'Kayıt sayısı',
  hesapSayisi: 'Hesap sayısı',
  noktaSayisi: 'Nokta sayısı',
  oncekiNoktaDk: 'Önceki noktadan bu yana (dk)',
}

/** Sunucunun durum kodları okunur hâliyle (kamera, görev, ihbar). */
const DURUM_ADI: Record<string, string> = {
  CRITICAL_EVACUATE: 'ağır ya da orta yapı hasarı sınıfı',
  CRACK_FOUND: 'çatlak bulundu (derece belirsiz)',
  SAFE_SURFACE: 'yalnız hasarsız sınıfı',
  NO_DETECTION: 'tespit yok',
  atandi: 'atandı',
  yolda: 'yolda',
  'olay-yerinde': 'olay yerinde',
  tamamlandi: 'tamamlandı',
  iptal: 'iptal',
  goruldu: 'görüldü',
  kapandi: 'kapandı',
  // Görüntüleme kaynakları (J-166)
  sos_listesi: 'SOS listesi',
  ihbar_listesi: 'İhbar listesi',
  ihbar_fotografi: 'İhbar fotoğrafı',
  kullanici_listesi: 'Kullanıcı listesi',
  hesap_defteri: 'Hesap defteri',
  islem_kaydi: 'İşlem kaydı',
  konum_gecmisi: 'Ekip konum geçmişi',
}

function tekDeger(v: unknown): string {
  if (v == null) return '—'
  if (typeof v === 'boolean') return v ? 'evet' : 'hayır'
  if (typeof v === 'number') return Number.isInteger(v) ? String(v) : String(Math.round(v * 1000) / 1000)
  if (typeof v === 'string') return DURUM_ADI[v] ?? v
  if (Array.isArray(v)) return v.map(tekDeger).join(', ')
  return Object.entries(v as Record<string, unknown>)
    .map(([a, b]) => `${a}: ${tekDeger(b)}`)
    .join(', ')
}

/** Nesne dizisi (ör. kamera tespitleri) satır satır; ötekiler tek satır. */
function Deger({ v }: { v: unknown }) {
  if (Array.isArray(v) && v.some((x) => x != null && typeof x === 'object')) {
    const ilk = v.slice(0, 20)
    return (
      <ol className="list-decimal pl-4">
        {ilk.map((x, i) => (
          <li key={i} className="font-mono text-small">
            {tekDeger(x)}
          </li>
        ))}
        {v.length > ilk.length && <li className="list-none text-ink-3">… {v.length - ilk.length} satır daha</li>}
      </ol>
    )
  }
  const metin = tekDeger(v)
  return <>{metin.length > 600 ? `${metin.slice(0, 600)}…` : metin}</>
}

function Ayrinti({ k }: { k: IslemKaydi }) {
  const alanlar = Object.entries(k.ayrinti ?? {})
  return (
    <dl className="grid max-w-5xl grid-cols-1 gap-x-4 gap-y-1 text-small whitespace-normal lg:grid-cols-2">
      <div className="flex gap-2">
        <dt className="shrink-0 text-ink-3">Kayıt no</dt>
        <dd className="font-mono text-ink">{k.id}</dd>
      </div>
      {k.hash && (
        <div className="flex min-w-0 gap-2" title={`Özet: ${k.hash}
Önceki: ${k.oncekiHash ?? '—'}`}>
          <dt className="shrink-0 text-ink-3">Zincir özeti</dt>
          <dd className="min-w-0 font-mono break-all text-ink">
            {k.hash.slice(0, 16)}… ← {k.oncekiHash ? `${k.oncekiHash.slice(0, 16)}…` : '—'}
          </dd>
        </div>
      )}
      {k.hedefTur && (
        <div className="flex gap-2">
          <dt className="shrink-0 text-ink-3">Hedef</dt>
          <dd className="min-w-0 font-mono break-all text-ink">
            {k.hedefTur} · {k.hedefId}
          </dd>
        </div>
      )}
      {alanlar.map(([ad, v]) => (
        <div
          key={ad}
          className={sn('flex min-w-0 gap-2', Array.isArray(v) && v.some((x) => typeof x === 'object') && 'lg:col-span-2')}
        >
          <dt className="shrink-0 text-ink-3">{ALAN_ADI[ad] ?? ad}</dt>
          <dd className="min-w-0 break-words text-ink">
            <Deger v={v} />
          </dd>
        </div>
      ))}
    </dl>
  )
}

export function IslemKaydiGorunumu() {
  const [grup, setGrup] = useState<IslemGrubu>('hepsi')
  const [acik, setAcik] = useState<number | null>(null)
  const kayit = useIslemKayitlari(grup)
  const satirlar = kayit.data?.pages.flatMap((s) => s.kayitlar) ?? []
  const baslik = 'px-3 py-2 text-left'

  return (
    <div className="mt-3">
      <p className="max-w-3xl text-small text-ink-2">
        Kim, ne zaman, ne yaptı: analizler, ekip gönderme ve görev adımları, SOS ve ihbar kapatma, ekip
        tanımı, bildirimler, girişler (başarısızlar dahil), konum paylaşımının başlaması ve kişisel veri
        içeren ekranların açılması (aynı kişi aynı ekranı 10 dakikada bir kez yazılır). Kayıtlar silinmez
        ve değiştirilmez. Analiz kayıtlarında fotoğraf saklanmaz, yalnız sonucun özeti durur. Hesap
        işlemleri "Hesap defteri" sekmesinde.
      </p>
      <ZincirPaneli />
      <HazirSecenekler etiket="İşlem türü" secenekler={ISLEM_GRUPLARI} secili={grup} onSec={setGrup} />

      <div className="mt-3 overflow-x-auto rounded-panel border border-line bg-panel">
        {kayit.isPending ? (
          <p className="p-3 text-small text-ink-3">Yükleniyor…</p>
        ) : kayit.isError ? (
          <div className="p-3">
            <VeriYok ne="İşlem kaydı" neden={hataMetni(kayit.error)} />
          </div>
        ) : satirlar.length === 0 ? (
          <div className="p-3">
            <VeriYok
              ne="İşlem kaydı"
              neden={grup === 'hepsi' ? 'henüz kayıt yok; kayıt tutma bu sürümle başladı' : 'bu türde kayıt yok'}
            />
          </div>
        ) : (
          // min-w-max yok: açılan ayrıntının uzun satırı tabloyu yana genişletmesin.
          <table className="w-full border-collapse">
            <thead className="border-b border-line">
              <tr>
                <th className={baslik}>
                  <span className="sr-only">Ayrıntı</span>
                </th>
                <th className={baslik}>
                  <Micro>Zaman</Micro>
                </th>
                <th className={baslik}>
                  <Micro>Yapan</Micro>
                </th>
                <th className={baslik}>
                  <Micro>İşlem</Micro>
                </th>
                <th className={baslik}>
                  <Micro>Ne oldu</Micro>
                </th>
              </tr>
            </thead>
            <tbody>
              {satirlar.map((k) => {
                const tur = ISLEM_TURU[k.tur] ?? { ad: k.tur }
                const ayrintiVar = !!k.hedefTur || Object.keys(k.ayrinti ?? {}).length > 0
                const genis = acik === k.id
                return (
                  <Fragment key={k.id}>
                    <tr
                      className="cursor-pointer border-b border-line last:border-b-0 hover:bg-hover"
                      onClick={() => ayrintiVar && setAcik(genis ? null : k.id)}
                    >
                      <td className="w-8 px-3 py-2 align-top text-ink-3">
                        {ayrintiVar && (
                          <button
                            type="button"
                            aria-expanded={genis}
                            aria-label={genis ? 'Ayrıntıyı kapat' : 'Ayrıntıyı aç'}
                            onClick={(e) => {
                              e.stopPropagation()
                              setAcik(genis ? null : k.id)
                            }}
                            className="grid h-6 w-6 place-items-center rounded-control hover:bg-raised hover:text-ink"
                          >
                            {genis ? <CaretDown size={14} aria-hidden /> : <CaretRight size={14} aria-hidden />}
                          </button>
                        )}
                      </td>
                      <td className="px-3 py-2 align-top text-small whitespace-nowrap text-ink-2">
                        {tarihSaatYilli(k.zaman)}
                      </td>
                      <td className="px-3 py-2 align-top whitespace-nowrap">
                        <span className="block text-body text-ink">{k.yapanAd ?? (k.yapanId ? 'bilinmiyor' : 'Sistem')}</span>
                        {k.yapanRol && <span className="block text-small text-ink-3">{ROL_ADI[k.yapanRol]}</span>}
                      </td>
                      <td className="px-3 py-2 align-top whitespace-nowrap">
                        <Rozet ton={tur.hata ? 'high' : 'nötr'}>{tur.ad}</Rozet>
                      </td>
                      <td className="w-full px-3 py-2 align-top text-body text-ink">{k.ozet}</td>
                    </tr>
                    {genis && (
                      <tr className="border-b border-line bg-sunken">
                        <td />
                        <td colSpan={4} className="px-3 py-2.5">
                          <Ayrinti k={k} />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {kayit.hasNextPage && (
        <button
          type="button"
          onClick={() => void kayit.fetchNextPage()}
          disabled={kayit.isFetchingNextPage}
          className="mt-3 h-9 rounded-control border border-line-2 px-3 text-body text-ink-2 hover:bg-hover hover:text-ink disabled:opacity-40"
        >
          {kayit.isFetchingNextPage ? 'Getiriliyor…' : 'Daha eski kayıtlar'}
        </button>
      )}
    </div>
  )
}

/** Hash zinciri (J-166): son doğrulama ve yeniden doğrulama. Doğrulama kendiliğinden
    koşmaz; tam tarama 100 bin kayıtta ~3 sn sürer (ölçüldü), artımlısı milisaniyeler. */
function ZincirPaneli() {
  const son = useSonZincirDenetimi()
  const dogrula = useZinciriDogrula()
  const sonuc: ZincirDenetimi | null | undefined = dogrula.data ?? son.data
  const dugme =
    'h-8 rounded-control border border-line-2 px-2.5 text-small text-ink-2 hover:bg-hover hover:text-ink disabled:opacity-40'

  return (
    <div className="mt-3 rounded-panel border border-line bg-panel px-3 py-2.5">
      <div className="flex flex-wrap items-center gap-2">
        <Micro>Kayıt zinciri</Micro>
        {sonuc == null ? (
          <Rozet ton="nötr">henüz doğrulanmadı</Rozet>
        ) : sonuc.saglam ? (
          <Rozet ton="ok">sağlam</Rozet>
        ) : (
          <Rozet ton="crit">bozuk</Rozet>
        )}
        <span className="flex-1" />
        <button type="button" className={dugme} disabled={dogrula.isPending} onClick={() => dogrula.mutate(false)}>
          {dogrula.isPending ? 'Doğrulanıyor…' : 'Yeni kayıtları doğrula'}
        </button>
        <button type="button" className={dugme} disabled={dogrula.isPending} onClick={() => dogrula.mutate(true)}>
          Baştan doğrula
        </button>
      </div>
      <p className="mt-1.5 text-small text-ink-2">
        {sonuc == null
          ? 'Her kayıt bir öncekinin özetini (SHA-256) taşır; arada bir kayıt değişir ya da silinirse zincir kopar.'
          : sonuc.saglam
            ? `${sonuc.kapsam === 'tam' ? 'Baştan sona' : 'Son denetimden bu yana'} ${sayi(sonuc.dogrulanan)} kayıt doğrulandı` +
              (sonuc.sureMs != null ? ` (${sayi(sonuc.sureMs)} ms)` : '') +
              (sonuc.zaman ? ` · ${tarihSaatYilli(sonuc.zaman)}${sonuc.yapanAd ? `, ${sonuc.yapanAd}` : ''}` : '') +
              (sonuc.sonHash ? ` · son özet ${sonuc.sonHash.slice(0, 12)}…` : '') +
              (sonuc.zincirOncesi
                ? ` · zincir kurulmadan önce yazılmış ${sayi(sonuc.zincirOncesi)} kayıt özetsiz (doğrulanamaz)`
                : '')
            : `Kayıt no ${sonuc.bozukId}: ${sonuc.neden}. Bu kayıttan sonrasına güvenilemez; veritabanı dosyasına erişimi olanlara sorulmalı.`}
      </p>
      {dogrula.isError && (
        <p role="alert" className="mt-1 text-small text-crit">
          Doğrulanamadı: {hataMetni(dogrula.error)}
        </p>
      )}
      <p className="mt-1 text-small text-ink-3">
        "Yeni kayıtları doğrula" son sağlam denetimden sonrasına bakar; daha eskisi için "Baştan doğrula".
        Zincir, dosyaya erişen birinin bütün özetleri yeniden hesaplamasını engellemez: son özeti zaman
        zaman başka bir yere (ör. sunum notu) yazmak bunu da ortaya çıkarır.
      </p>
    </div>
  )
}
