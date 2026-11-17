import { useId, useState } from 'react'
import type { Icon } from '@phosphor-icons/react'
import { Check, FirstAid, Lifebuoy, MapPin, Siren, SpeakerHigh, Warning } from '@phosphor-icons/react'
import { useCanliAkisDurumu } from '@/canli/canliAkis'
import { ApiHatasi } from '@/veri/istemci'
import { IHTIYAC_ADI, type SosCagrisi } from '@/veri/sorgular'
import { dogruluk, saat, sayi } from '@/lib/bicim'
import { sn } from '@/lib/sinif'
import { DURUMLAR, DURUM_ETIKETI } from './etiketler'
import { useDuduk } from './duduk'
import type { EtkinKonum, GpsDurumu } from './konum'
import { KisiSayaci } from './parcalar'
import { useCagriGonder } from './veri'
import { acikGorev } from '@/veri/gorev'
import { AfetzedeAdimlari, GelenEkipKarti, afetzedeDurumu } from './GelenEkip'

/* ---------------------------------------------------------------------------
   Acil yardım kartı (J-50, J-51). Deprem sonrası giren kişinin ilk sorusu
   "yardım nasıl çağırırım", ikincisi "yardım geliyor mu". Kart iki hâlde durur:

   · Form: kırmızı SOS düğmesi. Durum, not ve kişi sayısı isteğe bağlıdır;
     düğmeye hemen basılabilir. Durum seçilmezse çağrı en acil gider ve ekip
     bunun seçim olmadığını görür (durumSecildi=false).
   · Durum: çağrı gidince aynı kart "Bekliyor → Ekip atandı → Kapandı"
     adımlarını saatleriyle gösterir. Sayfa yenilense de açık çağrı görünür.

   Üçüncü tur (J-51, kullanıcı: "SOS butonu çok büyük, ölü alan var"): düğme
   sabit boyda (64 px), boş yeri doldurmaz; kart içeriği kadar uzar. İhtiyaç
   seçimi SOS'tan çıktı, kendi penceresi var ("İhtiyaç bildir"): SOS hayati
   tehlike içindir.

   Başarı yalnız sunucunun 201 yanıtından sonra yazılır; hata sebebiyle yazılır
   ve bilgiler silinmez (eski web hata olsa da "sinyaliniz alındı" diyordu).
--------------------------------------------------------------------------- */

const METIN_SINIRI = 500

const DURUM_IKONU: Record<SosCagrisi['oncelik'], Icon> = {
  kritik: Warning,
  yuksek: FirstAid,
  orta: Lifebuoy,
}

type Props = {
  konum: EtkinKonum | null
  gps: GpsDurumu
  /** Konum penceresini açar (cihaz konumu ya da mahalle seçimi). */
  konumAc: () => void
  /** Canlı akışla tazelenen çağrılar (afetzedede yalnız kendi çağrıları). */
  cagrilar: SosCagrisi[]
  /** Konsol rolüyle önizleme: sunucu bütün çağrıları verir, açık çağrı izlenmez. */
  onizleme: boolean
}

function hataMetni(e: unknown): string {
  if (e instanceof ApiHatasi) {
    if (e.durum === 401) return 'Oturumun kapanmış; yeniden giriş yapıp gönder.'
    if (e.durum === 422) return `Sunucu bilgileri kabul etmedi: ${e.message}.`
    if (e.durum >= 500) return 'Sunucu çağrıyı şu an kaydedemedi.'
    return e.message
  }
  if (e instanceof TypeError) return 'Sunucuya ulaşılamadı; internet bağlantın kopmuş olabilir.'
  return e instanceof Error ? e.message : 'Bilinmeyen bir hata oluştu.'
}

export function SosKarti(p: Props) {
  const [gonderilen, setGonderilen] = useState<SosCagrisi | null>(null)
  const [yeniCagri, setYeniCagri] = useState(false)

  // İzlenen çağrı: az önce gönderilen (liste tazelenince güncel hâli) ya da
  // afetzedenin açık çağrısı.
  const izlenen = gonderilen
    ? (p.cagrilar.find((c) => c.id === gonderilen.id) ?? gonderilen)
    : p.onizleme
      ? null
      : (p.cagrilar.find((c) => c.durum !== 'kapandi') ?? null)

  const durumHali = !!izlenen && !yeniCagri

  return (
    <section
      aria-label="Acil yardım"
      className="flex shrink-0 flex-col rounded-panel border border-line border-t-4 border-t-ihbar-sos bg-panel"
    >
      <header className="flex shrink-0 items-center justify-between gap-2 border-b border-line px-3.5 py-2">
        <h2 className="flex items-center gap-2 text-subtitle text-ink">
          <Siren size={20} weight="fill" className="text-ihbar-sos" aria-hidden />
          {durumHali ? 'Çağrının durumu' : 'Acil yardım'}
        </h2>
        <KonumRozeti konum={p.konum} gps={p.gps} konumAc={p.konumAc} />
      </header>
      <div className="flex flex-col px-3.5 py-3">
        {durumHali && izlenen ? (
          <CagriDurumu c={izlenen} yeniCagri={() => setYeniCagri(true)} />
        ) : (
          <SosFormu
            {...p}
            gonderildi={(c) => {
              setGonderilen(c)
              setYeniCagri(false)
            }}
            vazgec={izlenen ? () => setYeniCagri(false) : undefined}
          />
        )}
      </div>
    </section>
  )
}

/* ---- form ---------------------------------------------------------------- */

function SosFormu({
  konum,
  konumAc,
  onizleme,
  gonderildi,
  vazgec,
}: Props & { gonderildi: (c: SosCagrisi) => void; vazgec?: () => void }) {
  const notKimligi = useId()
  const [oncelik, setOncelik] = useState<SosCagrisi['oncelik'] | null>(null)
  const [kisi, setKisi] = useState(1)
  const [metin, setMetin] = useState('')
  const gonder = useCagriGonder()

  function sos() {
    if (!konum) {
      konumAc()
      return
    }
    gonder.mutate(
      {
        lon: konum.lon,
        lat: konum.lat,
        oncelik: oncelik ?? 'kritik',
        durumSecildi: oncelik !== null,
        kisiSayisi: kisi,
        metin: metin.trim() || undefined,
        mahalle: konum.kaynak === 'mahalle' ? konum.yer.ad : undefined,
        konumKaynagi: konum.kaynak,
        konumDogrulukM: konum.kaynak === 'gps' ? Math.round(konum.dogrulukM) : undefined,
      },
      { onSuccess: gonderildi },
    )
  }

  const secim = DURUMLAR.find((d) => d.oncelik === oncelik)

  return (
    <div className="flex flex-col gap-3">
      {onizleme && (
        <p className="text-small text-ink-3">
          Önizleme: buradan gönderilen çağrı gerçek kayıt olarak koordinasyon ekranına düşer.
        </p>
      )}

      <div>
        <p className="text-small text-ink-2">Durumun · isteğe bağlı</p>
        <div role="group" aria-label="Durumun" className="mt-1.5 grid grid-cols-3 gap-1.5">
          {DURUMLAR.map((d) => {
            const Ikon = DURUM_IKONU[d.oncelik]
            const secili = oncelik === d.oncelik
            return (
              <button
                key={d.oncelik}
                type="button"
                aria-pressed={secili}
                title={d.aciklama}
                onClick={() => setOncelik((o) => (o === d.oncelik ? null : d.oncelik))}
                className={sn(
                  'relative flex h-12 flex-col items-center justify-center gap-0.5 rounded-control border px-1 text-small transition-colors duration-150 ease-out-qm',
                  secili
                    ? 'border-crit bg-crit/15 text-ink'
                    : 'border-line-2 text-ink-2 hover:bg-hover hover:text-ink',
                )}
              >
                <Ikon size={18} weight={secili ? 'fill' : 'regular'} className={secili ? 'text-crit' : ''} aria-hidden />
                {d.etiket}
                {secili && (
                  <Check size={12} weight="bold" className="absolute top-1 right-1 text-crit" aria-hidden />
                )}
              </button>
            )
          })}
        </div>
        <p className="mt-1 text-small text-ink-3">
          {secim ? secim.aciklama : 'Seçmezsen çağrın en acil olarak gider.'}
        </p>
      </div>

      <div>
        <div className="flex items-baseline justify-between gap-2">
          <label htmlFor={notKimligi} className="text-small text-ink-2">
            Durumunu yaz · isteğe bağlı
          </label>
          <span className="text-small text-ink-3">
            {metin.length}/{METIN_SINIRI}
          </span>
        </div>
        <textarea
          id={notKimligi}
          rows={2}
          maxLength={METIN_SINIRI}
          value={metin}
          onChange={(e) => setMetin(e.target.value)}
          placeholder="Bina, kat, giriş yönü, yaralının durumu…"
          className="mt-1 w-full resize-none rounded-control border border-line-2 bg-sunken px-2.5 py-2 text-body text-ink"
        />
      </div>

      <KisiSayaci deger={kisi} degis={setKisi} />

      <button
        type="button"
        aria-label={konum ? 'SOS: yardım çağır' : 'SOS: önce konumunu seç'}
        disabled={gonder.isPending}
        onClick={sos}
        className="flex h-16 items-center justify-center gap-3 rounded-panel bg-crit px-3 text-ground hover:bg-crit/90 disabled:opacity-50"
      >
        <Siren size={30} weight="fill" aria-hidden />
        <span className="text-title font-semibold tracking-marka">
          {gonder.isPending ? 'GÖNDERİLİYOR' : 'SOS'}
        </span>
        <span className="text-subtitle">
          {!konum ? 'Önce konumunu seç' : gonder.isError ? 'Tekrar gönder' : 'Yardım çağır'}
        </span>
      </button>

      {gonder.isError && (
        <div role="alert" className="rounded-control border border-crit px-2.5 py-2">
          <p className="text-body text-crit">Çağrın gönderilemedi.</p>
          <p className="mt-0.5 text-small text-ink-2">
            {hataMetni(gonder.error)} Bilgilerin duruyor. Şebeke varsa 112'yi de ara.
          </p>
        </div>
      )}

      {vazgec && (
        <p className="text-small text-ink-3">
          Açık çağrın var: yeniden gönderirsen yeni çağrı açılmaz, aynı çağrının konumu ve bilgileri
          güncellenir.
        </p>
      )}
      {vazgec && (
        <button
          type="button"
          onClick={vazgec}
          className="text-small text-ink-3 underline-offset-2 hover:text-ink-2 hover:underline"
        >
          Vazgeç, çağrımın durumuna dön
        </button>
      )}
    </div>
  )
}

/* ---- gönderilen çağrının durumu ------------------------------------------ */

function CagriDurumu({ c, yeniCagri }: { c: SosCagrisi; yeniCagri: () => void }) {
  const akis = useCanliAkisDurumu((d) => d.durum)
  const duduk = useDuduk()
  // Ekip: adı, kaç kişi, hangi aşamada, nerede (J-54, kullanıcı kararı).
  const d = afetzedeDurumu(c.gorevler, c.durum === 'kapandi', c.durum === 'atandi')
  const kenar = d.ton === 'ok' ? 'border-ok' : d.ton === 'nötr' ? 'border-line-2' : 'border-high'
  const gelenler = (c.gorevler ?? []).filter(acikGorev)
  const ozet = [
    c.durumSecildi === false ? 'Durum seçilmedi' : DURUM_ETIKETI[c.oncelik],
    c.kisiSayisi ? `${sayi(c.kisiSayisi)} kişi` : null,
    c.ihtiyaclar?.length ? c.ihtiyaclar.map((i) => IHTIYAC_ADI[i] ?? i).join(', ') : null,
  ].filter(Boolean)

  return (
    <div className="flex flex-col gap-3" aria-live="polite">
      <div className={sn('rounded-panel border-2 px-3.5 py-2.5', kenar)}>
        <p className="text-small text-ink-2">Çağrın alındı · {saat(c.zaman)}</p>
        {!!c.guncellemeSayisi && (
          <p className="mt-0.5 text-small text-ink-2">
            Çağrın zaten iletilmişti; yeniden gönderince yenisi açılmadı, konumun ve bilgilerin
            güncellendi ({sayi(c.guncellemeSayisi)} kez).
          </p>
        )}
        <p className="mt-0.5 text-title text-ink">{d.baslik}</p>
        <p className="mt-0.5 text-body text-ink-2">{d.aciklama}</p>
      </div>

      <AfetzedeAdimlari olayZamani={c.zaman} gorevler={c.gorevler} />

      {gelenler.map((g) => (
        <GelenEkipKarti key={g.id} gorev={g} />
      ))}

      <div className="text-small text-ink-2">
        <p>Gönderdiğin: {ozet.join(' · ')}</p>
        {c.metin && <p className="mt-0.5 line-clamp-2 text-ink-3">“{c.metin}”</p>}
        <p className="mt-0.5 text-ink-3">
          {c.konumKaynagi === 'mahalle'
            ? `Konum: ${c.mahalle ?? 'mahalle'} merkezi (yaklaşık)`
            : c.konumDogrulukM != null
              ? `Konum: cihaz, ${dogruluk(c.konumDogrulukM)}`
              : null}
        </p>
        <p className="mt-0.5 text-ink-3">
          {akis === 'bagli'
            ? 'Durum değişince burada kendiliğinden güncellenir.'
            : 'Canlı bağlantı koptu, yeniden deneniyor; bu arada durum değişikliği gelmeyebilir.'}
        </p>
      </div>

      <p className="rounded-control border border-line-2 px-2.5 py-2 text-small text-ink-2">
        <span className="text-ink">Ekip gelene kadar: </span>
        güvenli yerdeysen ayrılma. Enkaz altındaysan hareket etme, ağzını bir bezle kapat, bağırmak
        yerine düdük çal ya da boruya vur; şarjını idareli kullan.
      </p>

      <div className="grid grid-cols-2 gap-1.5">
        <button
          type="button"
          aria-pressed={duduk.caliyor}
          onClick={duduk.caliyor ? duduk.durdur : duduk.cal}
          className={sn(
            'flex h-11 items-center justify-center gap-2 rounded-control border px-2.5 text-body',
            duduk.caliyor ? 'border-crit bg-crit/15 text-ink' : 'border-line-2 text-ink hover:bg-hover',
          )}
        >
          <SpeakerHigh size={18} aria-hidden />
          {duduk.caliyor ? 'Düdüğü durdur' : 'Düdük sesi çal'}
        </button>
        <button
          type="button"
          onClick={yeniCagri}
          className="flex h-11 items-center justify-center rounded-control border border-line-2 px-2.5 text-body text-ink hover:bg-hover"
        >
          {c.durum === 'kapandi' ? 'Yeni çağrı' : 'Durumum değişti'}
        </button>
      </div>
    </div>
  )
}

/* ---- konum rozeti --------------------------------------------------------- */

function KonumRozeti({ konum, gps, konumAc }: Pick<Props, 'konum' | 'gps' | 'konumAc'>) {
  const metin =
    konum?.kaynak === 'gps'
      ? `Cihaz ${dogruluk(konum.dogrulukM)}`
      : konum?.kaynak === 'mahalle'
        ? `${konum.yer.ad} (yaklaşık)`
        : gps.durum === 'araniyor'
          ? 'Konum aranıyor…'
          : 'Konum yok'
  return (
    <button
      type="button"
      onClick={konumAc}
      title="Konumunu değiştir"
      className={sn(
        'flex h-9 min-w-0 items-center gap-1.5 rounded-control border px-2.5 text-body hover:bg-hover',
        konum ? 'border-line-2 text-ink-2' : 'border-crit text-ink',
      )}
    >
      <MapPin size={16} weight="fill" className={sn('shrink-0', konum ? 'text-ok' : 'text-crit')} aria-hidden />
      <span className="truncate">{metin}</span>
      <span className="shrink-0 text-accent">{konum ? 'değiştir' : 'seç'}</span>
    </button>
  )
}
