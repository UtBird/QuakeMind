import { useId, useState } from 'react'
import { ChatText, MapPin, PaperPlaneTilt, Sparkle } from '@phosphor-icons/react'
import { ApiHatasi } from '@/veri/istemci'
import { Rozet } from '@/kabuk/parcalar'
import { dogruluk } from '@/lib/bicim'
import { sn } from '@/lib/sinif'
import type { Ihbar } from '@/veri/ihbar'
import { IHTIYAC_ADI } from '@/veri/sorgular'
import { DUZEY_ADI, belirsizlikMetni, konumYeterli } from '@/veri/metin'
import { kusUcusuM, mesafeMetni, type EtkinKonum } from './konum'
import { Adim, BIRINCIL, Gonderildi, IKINCIL, KonumSatiri } from './parcalar'
import { konumAlanlari, useIhbarGonder, useMetinAnalizi, type MetinAnaliziYaniti } from './veri'

/* ---------------------------------------------------------------------------
   Yazılı ihbar (J-51, J-170). Afetzede ne olduğunu kendi cümlesiyle yazar;
   sunucu kategoriyi, aciliyeti ve metindeki adresi çıkarır (adres yerel
   dizinden; metin dışarı gitmez). İki adım: yaz → anladığımızı kontrol et ve
   gönder. Ekibin gideceği yer adresin inceliğine göre önseçilir: sokak,
   mahalle ya da köy bulunduysa metindeki adres; yalnız ilçe ya da il
   bulunduysa afetzedenin kendi konumu (ilçe merkezi olayın yeri değildir).
   Afetzede değiştirebilir.

   Model çalışmazsa ihbar kaybolmaz: "incelemeden gönder" metni modelsiz,
   kendi konumuyla iletir.
--------------------------------------------------------------------------- */

const METIN_SINIRI = 1000
const ACILIYET_TONU = (n: number) => (n >= 5 ? 'crit' : n >= 4 ? 'high' : n >= 3 ? 'mid' : 'ok')

function hataMetni(e: unknown): string {
  if (e instanceof ApiHatasi) return e.message
  if (e instanceof TypeError) return 'sunucuya ulaşılamadı; internet bağlantın kopmuş olabilir'
  return e instanceof Error ? e.message : 'bilinmeyen hata'
}

export function MetinIhbari({ konum, konumAc }: { konum: EtkinKonum | null; konumAc: () => void }) {
  const kimlik = useId()
  const [metin, setMetin] = useState('')
  // Afetzedenin seçimi; seçmediyse adresin inceliğine göre önseçim (aşağıda).
  const [hedef, setHedef] = useState<'metin' | 'kendi' | null>(null)
  const [gonderilen, setGonderilen] = useState<Ihbar | null>(null)
  const analiz = useMetinAnalizi()
  const gonder = useIhbarGonder()

  const sonuc = analiz.data
  const metindeKonum = sonuc?.konum ?? null
  // Metinde adres yoksa ekip afetzedenin kendi konumuna gider. Varsa: adres
  // yeterince inceyse (sokak/mahalle/köy) ya da afetzedenin konumu yoksa metin.
  const onerilen: 'metin' | 'kendi' = konumYeterli(sonuc?.konumDuzeyi) || !konum ? 'metin' : 'kendi'
  const secilenHedef = metindeKonum ? (hedef ?? onerilen) : 'kendi'
  const gonderilebilir = secilenHedef === 'metin' || (secilenHedef === 'kendi' && !!konum)
  const uzaklik = metindeKonum && konum ? kusUcusuM(konum, metindeKonum) : null

  function ihbarEt(incelemesiz = false) {
    const g = incelemesiz || !sonuc ? undefined : sonuc.analizId
    if (secilenHedef === 'metin' && g && !incelemesiz) {
      gonder.mutate({ tur: 'metin', analizId: g, metin: metin.trim(), konumKaynagi: 'metin' }, { onSuccess: setGonderilen })
    } else if (konum) {
      gonder.mutate({ tur: 'metin', analizId: g, metin: metin.trim(), ...konumAlanlari(konum) }, { onSuccess: setGonderilen })
    }
  }

  if (gonderilen) {
    return (
      <div className="grid gap-3">
        <Gonderildi baslik="Yazılı ihbarın koordinasyona ulaştı" kimlik={gonderilen.id} zaman={gonderilen.zaman} />
        <button
          type="button"
          onClick={() => {
            analiz.reset()
            gonder.reset()
            setGonderilen(null)
            setMetin('')
          }}
          className={IKINCIL}
        >
          <ChatText size={18} aria-hidden /> Başka ihbar yaz
        </button>
      </div>
    )
  }

  return (
    <div className="grid gap-4">
      <p className="text-body text-ink-2">
        Ne gördüğünü kendi cümlenle yaz: ne oldu, nerede, kaç kişi. Model metinden kategoriyi,
        aciliyeti ve adresi çıkarır; sonucu görüp gönderirsin.
      </p>

      <Adim no={1} baslik="Ne oldu, nerede?">
        <div className="flex items-baseline justify-between gap-2">
          <label htmlFor={kimlik} className="text-small text-ink-2">
            İhbar metni
          </label>
          <span className="text-small text-ink-3">
            {metin.length}/{METIN_SINIRI}
          </span>
        </div>
        <textarea
          id={kimlik}
          rows={4}
          maxLength={METIN_SINIRI}
          value={metin}
          onChange={(e) => {
            setMetin(e.target.value)
            // Metin değişince eski inceleme geçersiz: sunucu da farklı metni reddeder.
            if (analiz.data || analiz.isError) analiz.reset()
          }}
          placeholder="Örnek: Armutlu Mahallesi 5. Sokak'ta bina çöktü, iki kişi enkaz altında."
          className="mt-1 w-full resize-none rounded-control border border-line-2 bg-sunken px-2.5 py-2 text-body text-ink"
        />
        {!sonuc && (
          <>
            <button
              type="button"
              disabled={metin.trim().length < 5 || analiz.isPending}
              onClick={() => analiz.mutate(metin.trim())}
              className={sn(BIRINCIL, 'mt-2')}
            >
              <Sparkle size={18} aria-hidden />
              {analiz.isPending ? 'İnceleniyor…' : 'İncelet'}
            </button>
            <p className="mt-1.5 text-small text-ink-3">
              Sonucu görüp öyle gönderirsin. Adres telefonda değil sunucuda, kendi adres listemizden bulunur.
            </p>
          </>
        )}
        {analiz.isError && (
          <div role="alert" className="mt-2 rounded-control border border-crit px-2.5 py-2">
            <p className="text-small text-crit">Model inceleyemedi: {hataMetni(analiz.error)}.</p>
            <p className="mt-0.5 text-small text-ink-2">
              İhbarın kaybolmasın: incelemeden, kendi konumunla gönderebilirsin.
            </p>
            <button
              type="button"
              disabled={gonder.isPending}
              onClick={() => (konum ? ihbarEt(true) : konumAc())}
              className={sn(IKINCIL, 'mt-2')}
            >
              <PaperPlaneTilt size={18} aria-hidden /> {konum ? 'İncelemeden gönder' : 'Önce konumunu seç'}
            </button>
          </div>
        )}
      </Adim>

      {sonuc && (
        <Adim no={2} baslik="Kontrol et ve gönder">
          <Anladigimiz sonuc={sonuc} />
          <p className="mt-3 mb-1.5 text-body text-ink">Ekip nereye gitsin?</p>
          {metindeKonum ? (
            <div role="radiogroup" aria-label="Ekibin gideceği yer" className="grid gap-1.5">
              <HedefSecenegi
                secili={secilenHedef === 'metin'}
                sec={() => setHedef('metin')}
                baslik={`Metindeki adres: ${sonuc.konumMetin ?? 'model buldu'}`}
                alt={[
                  sonuc.konumDuzeyi
                    ? `${DUZEY_ADI[sonuc.konumDuzeyi]} düzeyinde, ${belirsizlikMetni(sonuc.belirsizlikM) ?? 'yaklaşık'}`
                    : 'Yaklaşık',
                  uzaklik != null ? `senden ${mesafeMetni(uzaklik)} uzakta` : null,
                  konumYeterli(sonuc.konumDuzeyi) ? null : 'yalnız bölgeyi söyler, olayın yeri değildir',
                ]
                  .filter(Boolean)
                  .join('; ') + '.'}
              />
              <HedefSecenegi
                secili={secilenHedef === 'kendi'}
                sec={() => setHedef('kendi')}
                baslik={
                  konum
                    ? konum.kaynak === 'gps'
                      ? `Benim konumum (cihaz, ${dogruluk(konum.dogrulukM)})`
                      : `Benim konumum (${konum.yer.ad} merkezi)`
                    : 'Benim konumum (henüz seçilmedi)'
                }
                alt="Olay bulunduğun yerdeyse bunu seç."
              />
              {secilenHedef === 'kendi' && !konum && (
                <KonumSatiri konum={konum} konumAc={konumAc} />
              )}
            </div>
          ) : (
            <KonumSatiri konum={konum} konumAc={konumAc} not="Metinde adres bulunamadı; ekip bu konuma bakar." />
          )}
          <button
            type="button"
            disabled={gonder.isPending}
            onClick={() => (gonderilebilir ? ihbarEt() : konumAc())}
            className={sn(BIRINCIL, 'mt-2.5')}
          >
            <PaperPlaneTilt size={18} aria-hidden />
            {gonder.isPending
              ? 'Gönderiliyor…'
              : gonderilebilir
                ? 'İhbarı gönder'
                : 'Önce konumunu seç'}
          </button>
          {gonder.isError && (
            <p role="alert" className="mt-2 text-small text-crit">
              Gönderilemedi: {hataMetni(gonder.error)}. Metnin duruyor; yeniden deneyebilirsin.
            </p>
          )}
        </Adim>
      )}
    </div>
  )
}

/** Modelin anladığı, tek kartta: afetzede yanlışı bir bakışta görsün. */
function Anladigimiz({ sonuc }: { sonuc: MetinAnaliziYaniti }) {
  if (sonuc.ilgisiz) {
    return (
      <p className="rounded-control border border-line-2 px-2.5 py-2 text-body text-ink">
        Model bu metni afet ihbarı olarak anlamadı. Yanıldığını düşünüyorsan yine de gönderebilirsin.
      </p>
    )
  }
  const kisiler = (sonuc.kisiler ?? []).map((k) => `${k.sayi} ${k.ne}`)
  const ihtiyaclar = [...new Set((sonuc.ihtiyaclar ?? []).map((i) => IHTIYAC_ADI[i.ihtiyac] ?? i.ihtiyac))]
  const isaretler = [...new Set((sonuc.sinyaller ?? []).map((x) => x.ad))]
  const d = sonuc.konumDuzeyi
  return (
    <div className="rounded-control border border-line-2 px-2.5 py-2">
      <div className="flex items-start justify-between gap-2">
        <p className="text-body font-semibold text-ink">{sonuc.kategori ?? 'Kategori belirsiz'}</p>
        {sonuc.aciliyet != null && <Rozet ton={ACILIYET_TONU(sonuc.aciliyet)}>{`aciliyet ${sonuc.aciliyet}/5`}</Rozet>}
      </div>
      <dl className="kilav-kv mt-1.5 gap-x-3 gap-y-1 text-small">
        <dt className="text-ink-3">Adres</dt>
        <dd className="text-ink">
          {sonuc.konumMetin ?? 'metinde bulunamadı'}
          {d && <span className="text-ink-3">{` (${DUZEY_ADI[d].toLocaleLowerCase('tr')})`}</span>}
        </dd>
        {kisiler.length > 0 && (
          <>
            <dt className="text-ink-3">Kişi</dt>
            <dd className="text-ink">{kisiler.join(', ')}</dd>
          </>
        )}
        {isaretler.length > 0 && (
          <>
            <dt className="text-ink-3">Durum</dt>
            <dd className="text-ink">{isaretler.join(', ')}</dd>
          </>
        )}
        {ihtiyaclar.length > 0 && (
          <>
            <dt className="text-ink-3">İhtiyaç</dt>
            <dd className="text-ink">{ihtiyaclar.join(', ')}</dd>
          </>
        )}
      </dl>
      {(sonuc.adresNotlari ?? []).slice(0, 2).map((n) => (
        <p key={n} className="mt-1.5 text-small text-ink-3">
          {n}
        </p>
      ))}
      <p className="mt-1.5 text-small text-ink-3">
        Modelin tahminidir; yanlışsa metni düzeltip yeniden inceletebilirsin.
      </p>
    </div>
  )
}

function HedefSecenegi({
  secili,
  sec,
  baslik,
  alt,
}: {
  secili: boolean
  sec: () => void
  baslik: string
  alt: string
}) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={secili}
      onClick={sec}
      className={sn(
        'flex items-start gap-2.5 rounded-control border px-2.5 py-2 text-left',
        secili ? 'border-accent bg-accent-soft' : 'border-line-2 hover:bg-hover',
      )}
    >
      <MapPin size={18} weight={secili ? 'fill' : 'regular'} className="mt-0.5 shrink-0 text-accent" aria-hidden />
      <span>
        <span className="block text-body text-ink">{baslik}</span>
        <span className="block text-small text-ink-3">{alt}</span>
      </span>
    </button>
  )
}
