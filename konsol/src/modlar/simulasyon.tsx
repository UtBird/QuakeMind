import type { ReactNode } from 'react'
import { CaretDown } from '@phosphor-icons/react'
import { Amac, Bolum, HazirSecenekler, InceAyar, SuAn, Teknik, VeriYok } from '@/kabuk/Panel'
import { Anahtar, Kaydirici, Micro, Rozet } from '@/kabuk/parcalar'
import { useSimulasyon } from '@/durum/simulasyonDurumu'
import { sonIsSec, useIsler } from '@/durum/islerDurumu'
import { useKonsol } from '@/durum/konsolDurumu'
import {
  modelOzeti,
  modelSuresiSn,
  useSimAlanlar,
  useSimBitir,
  useSimKos,
  useSimModeller,
  useSimSonuc,
  VARYANT_ACIKLAMA,
  VARYANT_ADI,
  VARYANT_SIRASI,
  KOL_SIRASI,
  type SimAlan,
  type SimSonuc,
} from '@/veri/simulasyon'
import { mesafe, sayi } from '@/lib/bicim'
import { sn } from '@/lib/sinif'

/* ---------------------------------------------------------------------------
   Simülasyon (tatbikat) modu — SIMULASYON_SOZLESMESI.md §5.

   Panel kuralı (ARAYUZ §9): amaç → hazır seçenekler (alan, model) → ince ayar
   (eşik, yarıçap, tohum, ekip/afetzede) → şu an ne görüyorum → teknik not.

   Uçlar backend'de yazılıyor; hazır olmayan her şey "veri yok" diye görünür,
   uydurma sayı yazılmaz (kural 1).
--------------------------------------------------------------------------- */

const ORAN = (x: number) => `%${(x * 100).toFixed(1).replace('.', ',')}`

export function SimulasyonSol() {
  const secim = useSimulasyon((d) => d.secim)
  const secimYaz = useSimulasyon((d) => d.secimYaz)
  const kosuBasladi = useSimulasyon((d) => d.kosuBasladi)
  const isId = useSimulasyon((d) => d.isId)
  const hazir = useSimulasyon((d) => d.hazir)
  const varyantlar = useSimulasyon((d) => d.varyantlar)
  const varyantDegistir = useSimulasyon((d) => d.varyantDegistir)
  const izlenenGoster = useSimulasyon((d) => d.izlenenGoster)
  const izlenenDegistir = useSimulasyon((d) => d.izlenenDegistir)

  const alanlar = useSimAlanlar()
  const modeller = useSimModeller()
  const kos = useSimKos()
  const bitir = useSimBitir()
  const temizle = useSimulasyon((d) => d.temizle)
  const is = useIsler(sonIsSec)
  const sonuc = useSimSonuc(isId)

  const alan = alanlar.data?.find((a) => a.id === secim.alanId) ?? null
  const model = modeller.data?.find((m) => m.id === secim.modelId) ?? null
  const katman = alan?.katmanlar.find((k) => k.id === secim.katmanId) ?? null
  const koşuyor = is?.isTipi === 'simulasyon' && (is.durum === 'kuyrukta' || is.durum === 'calisiyor')

  /** Tatbikatı bitirir: koşunun yazdığı hasar noktaları sunucuda silinir,
      şerit kalkar, tatbikat katmanları düşer, konsol normal akışa döner. */
  function tatbikatiBitir() {
    if (!isId) return
    // Hata olursa ekran temizlenmez (J-186): eskiden onError da temizliyordu,
    // sunucu noktaları silemeden tatbikat "bitti" görünüyordu.
    bitir.mutate(isId, { onSuccess: () => temizle() })
  }

  function baslat() {
    if (!secim.alanId || !secim.katmanId || !secim.modelId) return
    kos.mutate(
      { ...secim, alanId: secim.alanId, katmanId: secim.katmanId, modelId: secim.modelId },
      {
        onSuccess: (y) => {
          kosuBasladi(y.isId, y.parmakIzi, y.onbellekten)
          useIsler.getState().isBasladi(y.isId, 'simulasyon', 'Tatbikat kuyruğa alındı')
        },
      },
    )
  }

  return (
    <>
      <Bolum baslik="Tatbikat" ek={<Rozet ton="accent">Gerçek olay değil</Rozet>}>
        <Amac>
          Bu alanda deprem olsaydı ekipler nereden geçerdi? Gerçek görüntüde model koşar,
          kapanan yolları çıkarır, rotaları hesaplar.
        </Amac>

        {alanlar.isError && <VeriYok ne="Tatbikat alanları" neden="uç henüz yayında değil" />}
        {alanlar.data && (
          <HazirSecenekler
            etiket="Alan"
            secenekler={alanlar.data.map((a) => ({ id: a.id, etiket: a.ad }))}
            secili={secim.alanId}
            onSec={(id) => {
              const yeni = alanlar.data?.find((a) => a.id === id)
              secimYaz({ alanId: id, katmanId: yeni?.katmanlar[0]?.id ?? null })
            }}
          />
        )}

        {alan && (
          <HazirSecenekler
            etiket="Görüntü katmanı"
            secenekler={alan.katmanlar.map((k) => ({ id: k.id, etiket: k.ad }))}
            secili={secim.katmanId}
            onSec={(id) => secimYaz({ katmanId: id })}
          />
        )}

        {modeller.isError && <VeriYok ne="Modeller" neden="uç henüz yayında değil" />}
        {modeller.data && (
          <HazirSecenekler
            etiket="Model"
            secenekler={modeller.data.map((m) => ({ id: m.id, etiket: m.ad }))}
            secili={secim.modelId}
            onSec={(id) => secimYaz({ modelId: id })}
          />
        )}

        {model && (
          <p className="mt-2 text-small text-ink-3">
            {modelOzeti(model)}
            {/* Süre ölçülmediyse yazılmaz (kural 8). Uç bunu ölçüm notuyla veriyor. */}
            {modelSuresiSn(model) != null &&
              ` · 512×512 ileri geçiş ${modelSuresiSn(model)!.toFixed(2).replace('.', ',')} sn`}
            {model.hazir === false && ' · ağırlık hazır değil'}
          </p>
        )}

        <InceAyar baslik="İnce ayar">
          <Kaydirici
            etiket="Hasar eşiği"
            deger={secim.esik}
            enAz={0.1}
            enCok={0.9}
            adim={0.05}
            degerEtiketi={secim.esik.toFixed(2).replace('.', ',')}
            onDegis={(v) => secimYaz({ esik: v })}
          />
          {/* Kapanma yarıçapı (r_h) ve yumuşak maliyet BİLEREK panelde yok (J-70).
              EMSR648 yer gerçeğiyle kalibre edildi: yarıçabı büyütmek duyarlılığı
              artırırken kesinliği 0,10–0,18 bandından çıkarmıyor — operatöre
              sonucu düzeltmeyen bir düğme sunulmaz. Tatbikat ürünün kuralıyla
              (r_h = 0) koşar; ikisi de ölçüm için API'de durur. */}
          <Kaydirici
            etiket="Ekip sayısı"
            deger={secim.ekipSayisi}
            enAz={1}
            enCok={10}
            adim={1}
            degerEtiketi={`${secim.ekipSayisi} ekip`}
            onDegis={(v) => secimYaz({ ekipSayisi: v })}
          />
          <Kaydirici
            etiket="Afetzede sayısı"
            deger={secim.afetzedeSayisi}
            enAz={1}
            enCok={10}
            adim={1}
            degerEtiketi={`${secim.afetzedeSayisi} kişi`}
            onDegis={(v) => secimYaz({ afetzedeSayisi: v })}
          />
          <Kaydirici
            etiket="Tohum"
            deger={secim.tohum}
            enAz={1}
            enCok={100}
            adim={1}
            degerEtiketi={`tohum ${secim.tohum}`}
            onDegis={(v) => secimYaz({ tohum: v })}
          />
        </InceAyar>

        <button
          type="button"
          onClick={baslat}
          disabled={
            !secim.alanId || !secim.katmanId || !secim.modelId || model?.hazir === false || kos.isPending || koşuyor
          }
          className="mt-3 w-full rounded-control bg-accent px-3 py-2.5 text-body font-semibold text-accent-ink disabled:opacity-40"
        >
          {koşuyor ? 'Tatbikat koşuyor…' : isId ? 'Yeniden koştur' : 'Tatbikatı başlat'}
        </button>
        {/* Tatbikat AÇILIR ve KAPANIR: koşu varken bitirme düğmesi çıkar.
            Şeridin kendisinde kapatma yoktur (uyarı susturulamaz), bitirme
            burada durur — basınca koşunun hasar noktaları silinir, katmanlar
            düşer, konsol normal akışa döner. */}
        {isId && (
          <button
            type="button"
            onClick={tatbikatiBitir}
            disabled={bitir.isPending}
            className="mt-2 w-full rounded-control border border-line-2 px-3 py-2 text-body text-ink-2 hover:bg-hover hover:text-ink disabled:opacity-40"
          >
            {bitir.isPending ? 'Bitiriliyor…' : 'Tatbikatı bitir'}
          </button>
        )}
        {bitir.isError && (
          <p role="alert" className="mt-2 text-small text-crit">
            Tatbikat bitirilemedi; yeniden dene.
          </p>
        )}
        {model?.hazir === false && (
          <p className="mt-2 text-small text-ink-2">
            Bu modelin ağırlığı sunucuda kurulu değil; başka bir model seç ya da ağırlığı kur
            (deploy/README.md, "Analiz dosyaları").
          </p>
        )}
        {kos.isError && (
          <p role="alert" className="mt-2 text-small text-crit">
            {kos.error instanceof Error ? kos.error.message : 'Koşu başlatılamadı.'}
          </p>
        )}

        <SuAn>
          {isId
            ? `Koşu ${isId}: ${sonuc.data?.durum === 'bitti' ? 'bütün katmanlar hazır' : hazir.length ? `${hazir.join(' → ')} hazır` : 'katman bekleniyor'}.`
            : alan && katman
              ? `${alan.ad} · ${katman.ad} (${katman.cekimTarihi}, ${katman.saglayici}).`
              : 'Bir alan, bir görüntü katmanı ve bir model seç.'}
        </SuAn>
        <Teknik>
          Çıkarım istek yolunda koşmaz: kuyruğa girer (HTTP 202), ilerleme canlı akıştan
          gelir; yoklama yok.
        </Teknik>
      </Bolum>

      <IlerlemeBolumu />

      {/* Haritada hangi çizgiler (J-185). Varsayılan iki: QuakeMind'ın güzergâhı
          ve kapanmayı bilmeyen ekibin fiilen sürdüğü yol. Dört çizgi birlikte
          açıkken 5 görevde 20 çizgi üst üste biniyordu. */}
      <Bolum baslik="Haritada göster">
        <Amac>
          Varsayılan iki çizgi: QuakeMind'ın kapalı yolları bilerek bulduğu güzergâh ve kapanmayı
          bilmeyen ekibin fiilen sürdüğü yol. Sağdaki görev listesinden bir görev seçince yalnız o
          görünür.
        </Amac>
        <Anahtar
          acik={izlenenGoster}
          etiket="Bilmeyen ekibin sürdüğü yol"
          onDegis={izlenenDegistir}
          ek={<Micro>çıkmazlar dahil</Micro>}
        />
        {VARYANT_SIRASI.map((v) => (
          <Anahtar
            key={v}
            acik={varyantlar[v]}
            etiket={VARYANT_ADI[v]}
            onDegis={() => varyantDegistir(v)}
            ek={
              <span className="flex flex-col items-end gap-0.5">
                <Micro>{VARYANT_ACIKLAMA[v]}</Micro>
                <VaryantOzeti sonuc={sonuc.data} varyant={v} />
              </span>
            }
          />
        ))}
      </Bolum>
    </>
  )
}

/** Madde 6: ilerleme YALNIZ canlı akıştan; burada zamanlayıcı yok. */
function IlerlemeBolumu() {
  const is = useIsler(sonIsSec)
  const isId = useSimulasyon((d) => d.isId)
  // Tatbikat bitince eski iş kaydı "%0 · Tatbikat bitirildi" diye kalıyordu (J-186).
  if (!isId || !is || is.isTipi !== 'simulasyon') return null
  const bitti = is.durum === 'bitti'
  return (
    <Bolum baslik="Koşu">
      <div className="flex items-center justify-between gap-2">
        <span className="text-body text-ink">{DURUM_ADI[is.durum]}</span>
        <Micro>%{Math.round(is.ilerleme)}</Micro>
      </div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-badge bg-raised">
        <div
          className={sinif(bitti)}
          style={{ width: `${Math.min(100, Math.max(0, is.ilerleme))}%` }}
        />
      </div>
      {is.mesaj && <p className="mt-2 text-small text-ink-3">{is.mesaj}</p>}
      {is.hata && (
        <p role="alert" className="mt-2 text-small text-crit">
          {is.hata}
        </p>
      )}
    </Bolum>
  )
}

/** Ucun aşama adları (sözleşmede yok; ekranda Türkçe yazılır). */
const ASAMA_ADI: Record<string, string> = {
  satellite: 'Görüntü (drone ya da uydu)',
  roads: 'Yol ağı',
  inference: 'Model çıkarımı',
  logistics: 'Lojistik',
}

const DURUM_ADI: Record<string, string> = {
  kuyrukta: 'Kuyrukta',
  calisiyor: 'Model koşuyor',
  bitti: 'Bitti',
  hata: 'Hata',
}

/* Hasar analizindeki ilerleme çubuğuyla aynı sınıflar (modlar/hasar.tsx). */
const sinif = (bitti: boolean) =>
  `h-full rounded-badge transition-all duration-200 ease-out-qm ${bitti ? 'bg-ok' : 'bg-accent'}`

function VaryantOzeti({ sonuc, varyant }: { sonuc: SimSonuc | undefined; varyant: keyof typeof VARYANT_ADI }) {
  const rotalar = sonuc?.rotalar ?? []
  const uzunluklar = rotalar
    .map((r) => r.varyantlar[varyant]?.uzunlukM)
    .filter((x): x is number => typeof x === 'number')
  if (!uzunluklar.length) return null
  const ortalama = uzunluklar.reduce((t, x) => t + x, 0) / uzunluklar.length
  return <Micro>ort. {mesafe(ortalama)}</Micro>
}

/* ---- sağ panel (J-185) ----------------------------------------------------
   Eski panel dokuz bölümü alt alta diziyordu (kaynak, hasar, kapanma, kamera,
   metin, arama, süreler, ölçüm, kollar, görevler); manşet sonuç en altta,
   hiçbir satır tıklanmıyordu. Kullanıcı "aşağı doğru uzayan, okunaksız,
   etkileşimsiz" dedi (24 Kasım). Yeni sıra soruya göre:

     1. Sonuç    — tatbikatın tek cevabı: kapanmayı bilmek ne kazandırdı.
     2. Görevler — tıkla: haritada yalnız o ekip–afetzede çifti, harita yaklaşır.
     3. Bulgular — dört kutu; kutu o katmanı açıp kapatır.
     4. Ayrıntı  — kamera, metin, kaynak, ölçüm: kapalı başlar.
--------------------------------------------------------------------------- */

const dakika = (dk: number) =>
  dk < 1 ? `${Math.round(dk * 60)} sn` : `${dk.toFixed(1).replace('.', ',')} dk`

const KOL_KISA: Record<string, string> = {
  'Kapanmayı bilmeyen ekip': 'Bilmeyen ekip',
  'Telsizle paylaşan filo': 'Telsizle paylaşan filo',
  QuakeMind: 'QuakeMind',
}

export function SimulasyonSag() {
  const isId = useSimulasyon((d) => d.isId)
  const sonuc = useSimSonuc(isId)
  const s = sonuc.data

  if (!isId) {
    return (
      <Bolum baslik="Tatbikat">
        <VeriYok ne="Koşu" neden="henüz tatbikat başlatılmadı" />
      </Bolum>
    )
  }
  if (sonuc.isError) {
    return (
      <Bolum baslik="Tatbikat">
        <VeriYok ne="Koşu sonucu" neden="uç henüz yayında değil" />
      </Bolum>
    )
  }
  if (!s) {
    return (
      <Bolum baslik="Tatbikat">
        <p className="text-small text-ink-3">Sonuç bekleniyor…</p>
      </Bolum>
    )
  }
  // Koşu kuyruktayken ya da hata verdiğinde yanıtta künye alanları YOKTUR (J-104).
  if (!s.alan || !s.kaynak || !s.model) {
    return (
      <Bolum baslik="Tatbikat">
        {s.durum === 'hata' ? (
          <VeriYok ne="Koşu" neden={s.mesaj ? `koşu hata verdi: ${s.mesaj}` : 'koşu hata verdi; yeniden başlat'} />
        ) : (
          <p className="text-small text-ink-3">Künye bekleniyor…</p>
        )}
      </Bolum>
    )
  }

  return (
    <>
      <SonucBolumu s={s} />
      <GorevBolumu s={s} />
      <BulguBolumu s={s} />
      <Ayrintilar s={s} />
    </>
  )
}

/** 1. Tatbikatın cevabı ve üç kolun karşılaştırması. */
function SonucBolumu({ s }: { s: SimSonuc }) {
  const kollar = s.referansAjanlar ?? {}
  const bilmeyen = kollar['Kapanmayı bilmeyen ekip']
  const qm = kollar['QuakeMind']
  const satirlar = KOL_SIRASI.filter((ad) => kollar[ad]?.ortalamaSureDk != null).map((ad) => ({
    ad,
    ...kollar[ad],
  }))
  const enUzun = Math.max(...satirlar.map((k) => k.ortalamaSureDk ?? 0), 0.001)
  const kazanc =
    bilmeyen?.ortalamaSureDk != null && qm?.ortalamaSureDk != null
      ? bilmeyen.ortalamaSureDk - qm.ortalamaSureDk
      : null
  const yuzde = kazanc != null && bilmeyen?.ortalamaSureDk ? (kazanc / bilmeyen.ortalamaSureDk) * 100 : null

  return (
    <Bolum
      baslik="Sonuç"
      ek={<Rozet ton={s.kaynak!.gercek ? 'ok' : 'mid'}>{s.kaynak!.gercek ? 'Gerçek görüntü' : 'Senaryo'}</Rozet>}
    >
      {kazanc == null ? (
        <p className="text-small text-ink-2">Kıyas hesaplanamadı: araçla ulaşılan ortak görev yok.</p>
      ) : kazanc > 0.005 ? (
        <p className="text-subtitle leading-snug text-ink">
          Kapanmaları önceden bilen ekip ortalama{' '}
          <span className="font-semibold text-accent">{dakika(kazanc)}</span> daha erken ulaştı
          {yuzde != null && <span className="text-ink-2"> (%{Math.round(yuzde)})</span>}.
        </p>
      ) : (
        <p className="text-subtitle leading-snug text-ink">
          Bu alanda kapanmalar ekipleri yavaşlatmadı: yol ağı her görev için açık bir yol bıraktı.
        </p>
      )}
      {bilmeyen && (bilmeyen.toplamKesif ?? 0) > 0 && (
        <p className="mt-1.5 text-small text-ink-2">
          Bilmeyen ekip {sayi(bilmeyen.toplamKesif ?? 0)} kez kapalı sokağa girip döndü
          {(bilmeyen.uDonusuSayisi ?? 0) > 0 && `, ${sayi(bilmeyen.uDonusuSayisi ?? 0)} U dönüşü yaptı`}
          {qm && (qm.toplamKesif ?? 0) === 0 && '; QuakeMind ekibi hiç'}.
        </p>
      )}

      {satirlar.length > 0 && (
        <ul className="mt-3 flex flex-col gap-2" aria-label="Kolların ortalama varış süresi">
          {satirlar.map((k) => (
            <li key={k.ad}>
              <div className="flex items-baseline justify-between gap-2 text-small">
                <span className={k.ad === 'QuakeMind' ? 'text-ink' : 'text-ink-2'}>{KOL_KISA[k.ad] ?? k.ad}</span>
                <span className="font-mono text-ink">{dakika(k.ortalamaSureDk!)}</span>
              </div>
              <div className="mt-1 h-1.5 overflow-hidden rounded-badge bg-raised">
                <div
                  className={sn('h-full rounded-badge', k.ad === 'QuakeMind' ? 'bg-accent' : 'bg-ink-3')}
                  style={{ width: `${((k.ortalamaSureDk ?? 0) / enUzun) * 100}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-3 text-small text-ink-3">
        {bilmeyen?.ortakGorev != null && `${sayi(bilmeyen.ortakGorev)} ortak görevin ortalaması`}
        {s.olcum?.hizKmh != null && `, ${s.olcum.hizKmh} km/sa varsayımıyla`}. Tatbikatta kapanmalar
        modelin bulduklarıdır: bu, modelin doğruluğunu değil, kapanmayı önceden bilmenin kazandırdığı
        süreyi ölçer.
      </p>
    </Bolum>
  )
}

/** 2. Görevler: satıra tıkla, haritada yalnız o çift. */
function GorevBolumu({ s }: { s: SimSonuc }) {
  const secili = useSimulasyon((d) => d.seciliGorev)
  const gorevSec = useSimulasyon((d) => d.gorevSec)
  const gorevler = s.gorevler ?? []
  if (!gorevler.length) return null
  const kol = (ad: string, id: string) => s.gorevKollari?.[ad]?.find((k) => k.gorevId === id)

  return (
    <Bolum
      baslik="Görevler"
      ek={
        secili ? (
          <button type="button" onClick={() => gorevSec(null)} className="text-small text-accent hover:underline">
            Tümünü göster
          </button>
        ) : (
          <Micro>tıkla: haritada yalnız o</Micro>
        )
      }
    >
      <ul className="-mx-1 flex flex-col gap-1">
        {gorevler.map((g) => {
          const q = kol('QuakeMind', g.id)
          const b = kol('Kapanmayı bilmeyen ekip', g.id)
          const rota = s.rotalar?.find((r) => r.gorevId === g.id)
          const acik = secili === g.id
          return (
            <li key={g.id}>
              <button
                type="button"
                aria-pressed={acik}
                onClick={() => gorevSec(g.id)}
                className={sn(
                  'w-full rounded-control border px-2 py-1.5 text-left transition-colors duration-150 ease-out-qm',
                  acik ? 'border-accent bg-raised' : 'border-transparent hover:bg-hover',
                )}
              >
                <span className="flex items-baseline justify-between gap-2">
                  <span className="text-body text-ink">
                    {g.ekipAd.split(' · ')[0]} → {g.afetzedeAd}
                  </span>
                  <span className="font-mono text-small text-ink">
                    {q?.ulasti && q.sureDk != null ? dakika(q.sureDk) : '—'}
                  </span>
                </span>
                <span className="mt-0.5 flex items-baseline justify-between gap-2 text-small text-ink-3">
                  <span>
                    {b?.ulasti && b.sureDk != null
                      ? `bilmeyen ${dakika(b.sureDk)}${b.cikmaz ? ` · ${b.cikmaz} çıkmaz` : ''}`
                      : q?.ulasti === false
                        ? 'araçla ulaşılamadı'
                        : 'kıyas yok'}
                  </span>
                  {g.sonAdimYurumeM != null && <span>son {mesafe(g.sonAdimYurumeM)} yürüyerek</span>}
                </span>
              </button>
              {acik && (
                <div className="mx-2 mt-1 mb-1.5 space-y-0.5 text-small text-ink-2">
                  {q?.mesafeM != null && <p>QuakeMind güzergâhı {mesafe(q.mesafeM)}</p>}
                  {b?.mesafeM != null && (
                    <p>
                      Bilmeyen ekip {mesafe(b.mesafeM)} sürdü
                      {b.uDonusu ? `, ${b.uDonusu} U dönüşü` : ''}
                    </p>
                  )}
                  {rota?.varyantlar.depremOncesi?.uzunlukM != null && (
                    <p>Kapanma olmasaydı {mesafe(rota.varyantlar.depremOncesi.uzunlukM)}</p>
                  )}
                  <p className="text-ink-3">
                    Ekip: {g.gercekTesis ? 'gerçek tesis' : 'mahalle giriş ağzı (OSM)'} · afetzede konumu senaryo
                  </p>
                </div>
              )}
            </li>
          )
        })}
      </ul>
    </Bolum>
  )
}

type BulguKatmani = 'simHasar' | 'simKapanma' | 'simKamera' | 'simMetin'

/** 3. Bulgular: dört kutu; kutu haritadaki katmanı açıp kapatır. */
function BulguBolumu({ s }: { s: SimSonuc }) {
  const katmanlar = useKonsol((d) => d.katmanlar)
  const katmanDegistir = useKonsol((d) => d.katmanDegistir)
  const kamera = s.kanallar?.kamera?.kayitlar ?? []
  const metin = s.kanallar?.metin?.kayitlar ?? []
  const kutular: { id: BulguKatmani; deger: string; ad: string; yok: boolean }[] = [
    { id: 'simHasar', deger: s.hasar ? ORAN(s.hasar.hasarliPikselOrani) : '—', ad: 'piksel hasarlı', yok: !s.hasar },
    {
      id: 'simKapanma',
      deger: s.kapanma?.kapaliKenarSayisi != null ? sayi(s.kapanma.kapaliKenarSayisi) : '—',
      ad: 'kapalı sokak parçası',
      yok: !s.kapanma,
    },
    {
      id: 'simKamera',
      deger: sayi(kamera.length),
      ad: `fotoğraf · ${sayi(kamera.reduce((n, k) => n + (k.catlakSayisi ?? 0), 0))} çatlak`,
      yok: !kamera.length,
    },
    {
      id: 'simMetin',
      deger: sayi(metin.length),
      ad: `metin ihbarı · ${sayi(metin.filter((k) => k.elendi).length)} elendi`,
      yok: !metin.length,
    },
  ]
  return (
    <Bolum baslik="Bulgular" ek={<Micro>kutu: katmanı aç / kapat</Micro>}>
      <div className="grid grid-cols-2 gap-1.5">
        {kutular.map((k) => (
          <button
            key={k.id}
            type="button"
            aria-pressed={katmanlar[k.id]}
            disabled={k.yok}
            onClick={() => katmanDegistir(k.id)}
            className={sn(
              'rounded-control border px-2.5 py-2 text-left transition-colors duration-150 ease-out-qm disabled:opacity-50',
              katmanlar[k.id] ? 'border-line-2 bg-raised' : 'border-line bg-panel opacity-70',
              !k.yok && 'hover:border-accent',
            )}
          >
            <span className="block text-subtitle text-ink">{k.deger}</span>
            <span className="block text-small text-ink-2">{k.ad}</span>
            <span className="mt-0.5 block text-small text-ink-3">{katmanlar[k.id] ? 'haritada' : 'gizli'}</span>
          </button>
        ))}
      </div>
      {s.kapanma && (
        <p className="mt-2 text-small text-ink-3">
          {s.kapanma.yaricapM > 0
            ? `Kapalı yol: hasar noktasına ${s.kapanma.yaricapM} m'den yakın sokak parçası.`
            : 'Kapalı yol: modelin bulduğu hasar sokağın üstüne taşıyor (yalnız yol üstündeki hasar kapatır).'}
        </p>
      )}
    </Bolum>
  )
}

function Ayrinti({ baslik, ek, children }: { baslik: string; ek?: ReactNode; children: ReactNode }) {
  return (
    <details className="group border-b border-line last:border-b-0">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-2 px-3 py-2.5 text-small text-ink-2 hover:text-ink">
        <span>{baslik}</span>
        <span className="flex items-center gap-2">
          {ek}
          <CaretDown size={14} className="transition-transform group-open:rotate-180" aria-hidden />
        </span>
      </summary>
      <div className="px-3 pb-3">{children}</div>
    </details>
  )
}

/** 4. Ayrıntılar: kapalı başlar; yalnız merak eden açar. */
function Ayrintilar({ s }: { s: SimSonuc }) {
  const kamera = s.kanallar?.kamera
  const metin = s.kanallar?.metin
  return (
    <>
      {kamera && (
        <Ayrinti baslik="Kamera tespitleri" ek={<Micro>{sayi(kamera.kayitlar.length)}</Micro>}>
          {kamera.hata ? (
            <p className="text-small text-crit">{kamera.hata}</p>
          ) : kamera.kayitlar.length === 0 ? (
            <p className="text-small text-ink-3">{kamera.not ?? 'Kayıt yok.'}</p>
          ) : (
            <>
              <ul className="flex flex-col gap-1.5">
                {kamera.kayitlar.map((k) => (
                  <li key={k.id} className="flex flex-col">
                    <span className="text-small text-ink">{k.etiket}</span>
                    <span className="text-small text-ink-3">
                      güven %{(k.guven * 100).toFixed(0)} · {sayi(k.catlakSayisi ?? 0)} çatlak ·{' '}
                      {sayi(k.binaSayisi ?? 0)} bina ·{' '}
                      {k.foto.lisans}
                    </span>
                  </li>
                ))}
              </ul>
              <Teknik>
                Fotoğraflar gerçek (6 Şubat 2023, Wikimedia Commons) ve model çıktısı gerçek; haritadaki
                konumları tohumla, modelin hasarlı bulduğu alanlardan seçildi.
              </Teknik>
            </>
          )}
        </Ayrinti>
      )}

      {metin && (
        <Ayrinti baslik="Metin ihbarları" ek={<Micro>{sayi(metin.kayitlar.length)}</Micro>}>
          {metin.hata ? (
            <p className="text-small text-crit">{metin.hata}</p>
          ) : metin.kayitlar.length === 0 ? (
            <p className="text-small text-ink-3">{metin.not ?? 'Kayıt yok.'}</p>
          ) : (
            <>
              <ul className="flex flex-col gap-2">
                {metin.kayitlar.map((k) => (
                  <li key={k.id} className="flex flex-col">
                    <span className="text-small text-ink">
                      {k.etiket} <span className="text-ink-3">· aciliyet {k.aciliyet}/5</span>
                    </span>
                    <span className="mt-0.5 text-small text-ink-2">“{k.metin}”</span>
                  </li>
                ))}
              </ul>
              <Teknik>
                Metinler üretilmiştir (elle yazıldı); BERTurk sınıflandırması gerçek koştu. Konumları da
                üretildi.
              </Teknik>
            </>
          )}
        </Ayrinti>
      )}

      <Ayrinti baslik="Görüntü ve model">
        <p className="text-small text-ink">{s.alan!.ad}</p>
        <p className="mt-1 text-small text-ink-2">
          {s.kaynak!.saglayici} · çekim {s.kaynak!.cekimTarihi}
          {s.kaynak!.gsdM != null && ` · ${s.kaynak!.gsdM} m/piksel`}
        </p>
        <p className="mt-1 text-small text-ink-2">
          Model {s.model!.mimari} · eşik {s.model!.esik.toString().replace('.', ',')}
        </p>
        {s.hasar?.oncesiKontrol?.kosuldu && (
          <p className="mt-1 text-small text-ink-2">
            Deprem öncesi görüntüde {ORAN(s.hasar.oncesiKontrol.hasarliPikselOrani)} (yanlış alarm tabanı)
          </p>
        )}
        <Teknik>Parmak izi {s.parmakIzi.slice(0, 20)}… — aynı parmak izi aynı sonucu verir.</Teknik>
      </Ayrinti>

      {(s.olcum || s.sureler) && (
        <Ayrinti baslik="Ölçüm ve süreler" ek={s.olcum ? <Micro>{sayi(s.olcum.ciftSayisi)} çift</Micro> : undefined}>
          {s.olcum && (
            <div className="space-y-1 text-small text-ink-2">
              <p>
                Bütün {sayi(s.olcum.ciftSayisi)} ekip–afetzede çifti ölçüldü; listede ilk tur (
                {sayi(s.gorevler?.length ?? 0)} görev).
              </p>
              {s.olcum.ortalamaUzamaM != null && s.olcum.ortalamaUzamaYuzde != null && (
                <p>
                  Kapanmalar yolu ortalama {mesafe(s.olcum.ortalamaUzamaM)} (%
                  {s.olcum.ortalamaUzamaYuzde.toFixed(1).replace('.', ',')}) uzattı
                  {s.olcum.enBuyukUzamaM != null && `, en çok ${mesafe(s.olcum.enBuyukUzamaM)}`}.
                </p>
              )}
              {s.olcum.yurumeGerekenCift ? (
                <p>
                  {sayi(s.olcum.yurumeGerekenCift)} çiftte son adım yürüyerek
                  {s.olcum.ortalamaYurumeM != null && `, ortalama ${mesafe(s.olcum.ortalamaYurumeM)}`}.
                </p>
              ) : null}
              {s.olcum.ulasilamayanCift > 0 && <p>{sayi(s.olcum.ulasilamayanCift)} çifte ulaşılamadı.</p>}
            </div>
          )}
          {s.sureler && (
            <div className="mt-2">
              {Object.entries(s.sureler)
                .filter(([ad]) => ad !== 'total')
                .map(([ad, ms]) => (
                  <div key={ad} className="flex items-baseline justify-between gap-2 py-0.5">
                    <span className="text-small text-ink-2">{ASAMA_ADI[ad] ?? ad}</span>
                    <span className="font-mono text-small text-ink">{(ms / 1000).toFixed(1).replace('.', ',')} sn</span>
                  </div>
                ))}
              {s.sureler.total != null && (
                <p className="mt-1 text-small text-ink-3">
                  Koşu toplam {(s.sureler.total / 1000).toFixed(1).replace('.', ',')} sn (sunucunun ölçümü)
                </p>
              )}
            </div>
          )}
          {s.rotalar?.length ? <AramaOzeti sonuc={s} /> : null}
        </Ayrinti>
      )}
    </>
  )
}

/** Dijkstra ve A* (madde 5): aynı yolu bulduysa bunu yazar. */
function AramaOzeti({ sonuc }: { sonuc: SimSonuc }) {
  const rotalar = sonuc.rotalar ?? []
  const ortalama = (sec: (r: (typeof rotalar)[number]) => number) =>
    rotalar.length ? rotalar.reduce((t, r) => t + sec(r), 0) / rotalar.length : 0
  const ms = (sn: number) => `${(sn * 1000).toFixed(0)} ms`
  const ayni = rotalar.length > 0 && rotalar.every((r) => r.arama.ayniYol === true)
  return (
    <p className="mt-2 text-small text-ink-3">
      Rota araması (rota başına): Dijkstra {ms(ortalama((r) => r.arama.dijkstra.sureSn))}, A*{' '}
      {ms(ortalama((r) => r.arama.astar.sureSn))}
      {ayni ? '; ikisi de aynı yolu buldu.' : '.'}
    </p>
  )
}

export type { SimAlan }
