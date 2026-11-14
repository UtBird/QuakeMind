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
  type SimAlan,
  type SimSonuc,
} from '@/veri/simulasyon'
import { mesafe, sayi, sayiVeyaYok, sureMetni } from '@/lib/bicim'

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
    bitir.mutate(isId, { onSuccess: () => temizle(), onError: () => temizle() })
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
          disabled={!secim.alanId || !secim.katmanId || !secim.modelId || kos.isPending || koşuyor}
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

      <Bolum baslik="Rota varyantları">
        <Amac>
          Aynı ekip–afetzede çifti, üç planlama kuralıyla. Üçü de PLANLANAN yoldur;
          ekibin fiilen sürdüğü yol ayrı çizilir (aşağıya bakınız).
        </Amac>
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

      {sonuc.data?.izlenenYollar && (
        <Bolum baslik="Fiilen sürülen yol">
          <Amac>
            Manşet sayı buradan gelir: kapanmayı bilmeyen ekip yola çıkar, kapalı
            sokağa varınca öğrenir ve geri döner. Haritada o yolun tamamı çizilir —
            çıkmazlar dahil.
          </Amac>
          {Object.entries(sonuc.data.izlenenYollar).map(([ad, hatlar]) => (
            <div key={ad} className="flex items-baseline justify-between gap-2 py-0.5">
              <span className="text-small text-ink">{ad}</span>
              <Micro>{sayi(hatlar.length)} ekip</Micro>
            </div>
          ))}
        </Bolum>
      )}
    </>
  )
}

/** Madde 6: ilerleme YALNIZ canlı akıştan; burada zamanlayıcı yok. */
function IlerlemeBolumu() {
  const is = useIsler(sonIsSec)
  if (!is || is.isTipi !== 'simulasyon') return null
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
  satellite: 'Uydu görüntüsü',
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

/* ---- sağ panel ---------------------------------------------------------- */

export function SimulasyonSag() {
  const isId = useSimulasyon((d) => d.isId)
  const sonuc = useSimSonuc(isId)
  const katmanlar = useKonsol((d) => d.katmanlar)
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
  // Koşu kuyruktayken ya da hata verdiğinde yanıtta künye alanları YOKTUR;
  // tip artık bunu söylüyor (J-104). Eskiden burada `s.kaynak.gercek`
  // okunuyordu ve bayat bir iş kimliğiyle yenileyince panel çöküyordu.
  if (!s.alan || !s.kaynak || !s.model) {
    return (
      <Bolum baslik="Tatbikat">
        {s.durum === 'hata' ? (
          <VeriYok ne="Koşu" neden="koşu hata verdi; yeniden başlat" />
        ) : (
          <p className="text-small text-ink-3">Künye bekleniyor…</p>
        )}
      </Bolum>
    )
  }

  return (
    <>
      {/* Madde 3: her katmanın sağlayıcısı, tarihi, GSD'si; üretilen her şey etiketli. */}
      <Bolum baslik="Kaynak" ek={<Rozet ton={s.kaynak.gercek ? 'ok' : 'mid'}>{s.kaynak.gercek ? 'Gerçek' : 'Senaryo'}</Rozet>}>
        <p className="text-body text-ink">{s.alan.ad}</p>
        <p className="mt-1 text-small text-ink-2">
          {s.kaynak.saglayici} · çekim {s.kaynak.cekimTarihi}
          {s.kaynak.gsdM != null && ` · ${s.kaynak.gsdM} m/piksel`}
        </p>
        <p className="mt-2 text-small text-ink-3">
          Model: {s.model.mimari} · eşik {s.model.esik.toString().replace('.', ',')}
        </p>
        <Teknik>Parmak izi {s.parmakIzi.slice(0, 20)}… — aynı parmak izi aynı sonucu verir.</Teknik>
      </Bolum>

      {s.hasar && (
        <Bolum baslik="Hasar" ek={<Micro>{katmanlar.simHasar ? 'katman açık' : 'katman kapalı'}</Micro>}>
          <p className="text-body text-ink">{ORAN(s.hasar.hasarliPikselOrani)} piksel hasarlı</p>
          {s.hasar.noktaSayisi != null && (
            <p className="mt-1 text-small text-ink-2">{sayi(s.hasar.noktaSayisi)} hasar noktası</p>
          )}
          {s.hasar.oncesiKontrol?.kosuldu && (
            <p className="mt-2 text-small text-ink-3">
              Kontrol koşusu (deprem öncesi görüntü): {ORAN(s.hasar.oncesiKontrol.hasarliPikselOrani)} —
              yanlış alarm tabanı.
            </p>
          )}
        </Bolum>
      )}

      {s.kapanma && (
        <Bolum baslik="Kapanan yollar">
          <p className="text-body text-ink">
            {sayiVeyaYok(s.kapanma.kapaliKenarSayisi)} kapalı kenar
            {s.kapanma.cezaliKenarSayisi != null && ` · ${sayi(s.kapanma.cezaliKenarSayisi)} cezalı`}
          </p>
          <p className="mt-1 text-small text-ink-3">
            Kapanma yarıçapı {s.kapanma.yaricapM} m; hasar noktasına bu kadar yakın kenar kapalı sayıldı.
          </p>
        </Bolum>
      )}

      {/* Yer seviyesi kanallar (J-108). Uydu mahalleye yukarıdan baktı; bu
          ikisi yerden bakıyor. Neyin gerçek neyin üretilmiş olduğu her
          satırda yazar — kural 1. */}
      {s.kanallar?.kamera && (
        <Bolum
          baslik="Kamera tespiti"
          ek={<Micro>{katmanlar.simKamera ? 'katman açık' : 'katman kapalı'}</Micro>}
        >
          {s.kanallar.kamera.hata ? (
            <p className="text-small text-crit">{s.kanallar.kamera.hata}</p>
          ) : s.kanallar.kamera.kayitlar.length === 0 ? (
            <p className="text-small text-ink-3">{s.kanallar.kamera.not ?? 'Kayıt yok.'}</p>
          ) : (
            <>
              <p className="text-body text-ink">
                {sayi(s.kanallar.kamera.kayitlar.length)} fotoğraf ·{' '}
                {sayi(s.kanallar.kamera.kayitlar.reduce((n, k) => n + k.catlakSayisi, 0))} çatlak ·{' '}
                {sayi(s.kanallar.kamera.kayitlar.reduce((n, k) => n + k.binaSayisi, 0))} bina
              </p>
              <ul className="mt-2 flex flex-col gap-1.5">
                {s.kanallar.kamera.kayitlar.map((k) => (
                  <li key={k.id} className="flex flex-col">
                    <span className="text-small text-ink">{k.etiket}</span>
                    <Micro>
                      güven %{(k.guven * 100).toFixed(0)} · çıkarım {Math.round(k.cikarimMs)} ms ·{' '}
                      {k.foto.lisans} / {k.foto.yazar}
                    </Micro>
                  </li>
                ))}
              </ul>
              <Teknik>
                Fotoğraflar gerçek: 6 Şubat 2023 depremi, Wikimedia Commons (Public domain ve CC
                BY-SA 4.0), künyeleri SHA-256 ile kayıtlı. Model çıktısı da gerçek. Haritadaki
                konumları ÜRETİLDİ — tohumla, modelin hasarlı bulduğu alanlardan seçildi.
              </Teknik>
            </>
          )}
        </Bolum>
      )}

      {s.kanallar?.metin && (
        <Bolum
          baslik="Metin ihbarı"
          ek={<Micro>{katmanlar.simMetin ? 'katman açık' : 'katman kapalı'}</Micro>}
        >
          {s.kanallar.metin.hata ? (
            <p className="text-small text-crit">{s.kanallar.metin.hata}</p>
          ) : s.kanallar.metin.kayitlar.length === 0 ? (
            <p className="text-small text-ink-3">{s.kanallar.metin.not ?? 'Kayıt yok.'}</p>
          ) : (
            <>
              <p className="text-body text-ink">
                {sayi(s.kanallar.metin.kayitlar.length)} ihbar ·{' '}
                {sayi(s.kanallar.metin.kayitlar.filter((k) => k.elendi).length)} elendi
              </p>
              <ul className="mt-2 flex flex-col gap-2">
                {s.kanallar.metin.kayitlar.map((k) => (
                  <li key={k.id} className="flex flex-col">
                    <span className="text-small text-ink">{k.etiket}</span>
                    <Micro>
                      aciliyet {k.aciliyet}/5 · güven %{(k.guven * 100).toFixed(0)} ·{' '}
                      {Math.round(k.cikarimMs)} ms
                    </Micro>
                    <span className="mt-0.5 text-small text-ink-2">“{k.metin}”</span>
                  </li>
                ))}
              </ul>
              <Teknik>
                Metinler ÜRETİLMİŞTİR — elle yazıldı, gerçek çağrı değil. BERTurk sınıflandırması ve
                varlık ismi tanıma gerçek olarak koştu. Haritadaki konumları da üretildi: modelin
                coğrafi kodlayıcısı mahalle merkezine düşürüyor ve 500 m&apos;lik tatbikat kutusunun
                dışında kalıyor.
              </Teknik>
            </>
          )}
        </Bolum>
      )}

      {/* Madde 5: iki arama yan yana. Uç rotaları henüz vermiyorsa kart çıkmaz. */}
      {s.rotalar?.length ? <AramaKarti sonuc={s} /> : null}

      {/* Sunucunun verdiği aşama süreleri (sözleşmede yok, ucun ölçümü). */}
      {s.sureler && (
        <Bolum baslik="Koşu süreleri" ek={<Micro>sunucunun ölçümü</Micro>}>
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
              Toplam {(s.sureler.total / 1000).toFixed(1).replace('.', ',')} sn
            </p>
          )}
          {s.gunluk?.length ? <Teknik>{s.gunluk[s.gunluk.length - 1]}</Teknik> : null}
        </Bolum>
      )}

      {s.olcum && (
        <Bolum baslik="Ölçüm" ek={<Micro>{sayi(s.olcum.ciftSayisi)} çift</Micro>}>
          {s.olcum.ortalamaUzamaM != null && s.olcum.ortalamaUzamaYuzde != null ? (
            <p className="text-body text-ink">
              Ortalama uzama {mesafe(s.olcum.ortalamaUzamaM)} (%
              {s.olcum.ortalamaUzamaYuzde.toFixed(1).replace('.', ',')})
            </p>
          ) : (
            <p className="text-body text-ink-2">
              Uzama hesaplanamadı: uzama yalnız araçla ulaşılan çiftlerden alınır, bu koşuda öyle
              çift yok.
            </p>
          )}
          {s.olcum.enBuyukUzamaM != null && (
            <p className="mt-1 text-small text-ink-2">En çok uzama {mesafe(s.olcum.enBuyukUzamaM)}</p>
          )}
          {s.olcum.ortalamaYurumeM != null && (
            <p className="mt-1 text-small text-ink-2">
              Son adım yürüme, ortalama {mesafe(s.olcum.ortalamaYurumeM)}
              {s.olcum.yurumeGerekenCift != null && ` (${sayi(s.olcum.yurumeGerekenCift)} çiftte)`}
            </p>
          )}
          <p className="mt-1 text-small text-ink-3">
            Ekranda {sayi(s.gorevler?.length ?? 0)} görev çizili; ölçüm bütün çiftlerden.
            {s.olcum.ulasilamayanCift > 0 && ` ${sayi(s.olcum.ulasilamayanCift)} çifte ulaşılamadı.`}
            {s.olcum.hizKmh != null && ` Süreler ${s.olcum.hizKmh} km/sa varsayımıyla.`}
          </p>
        </Bolum>
      )}

      {s.referansAjanlar && (
        <Bolum baslik="Kıyas kolları">
          {Object.entries(s.referansAjanlar).map(([ad, deger]) => (
            <div key={ad} className="flex items-baseline justify-between gap-2 py-0.5">
              <span className="text-small text-ink-2">{ad}</span>
              <span className="text-small text-ink">
                {/* Kollar dakikanın altında ayrışıyor (ör. 2,4 · 2,2 · 1,6 dk): tam
                    sayıya yuvarlamak üçünü de "2 dk" yapıp farkı siliyordu (J-154). */}
                {deger.ortalamaSureDk == null
                  ? 'araçla ulaşılan görev yok'
                  : deger.ortalamaSureDk < 10
                    ? `${deger.ortalamaSureDk.toFixed(1).replace('.', ',')} dk`
                    : sureMetni(Math.round(deger.ortalamaSureDk))}
                {deger.ortalamaSureDk != null &&
                  deger.uDonusuSayisi != null &&
                  ` · ${sayi(deger.uDonusuSayisi)} U dönüşü`}
              </span>
            </div>
          ))}
        </Bolum>
      )}

      {s.gorevler?.length ? (
        <Bolum baslik="Görevler">
          {s.gorevler.map((g) => (
            <div key={g.id} className="border-b border-line py-2 last:border-b-0">
              <div className="flex items-baseline justify-between gap-2">
                <span className="text-body text-ink">{g.ekipAd}</span>
                <Micro>{sureMetni(Math.round(g.etaDk))}</Micro>
              </div>
              <p className="text-small text-ink-3">
                {g.afetzedeAd}
                {g.senaryo && ' · senaryo'}
                {g.sonAdimYurumeM != null && ` · son ${mesafe(g.sonAdimYurumeM)} yürüyerek`}
              </p>
            </div>
          ))}
        </Bolum>
      ) : null}
    </>
  )
}

/** Madde 5: Dijkstra ve A* yan yana; aynı yolu bulduysa bunu yazar. */
function AramaKarti({ sonuc }: { sonuc: SimSonuc }) {
  const rotalar = sonuc.rotalar ?? []
  // Rota BAŞINA ortalama: toplam yazılsaydı tek arama o kadar sürmüş gibi
  // okunurdu. Karşılaştırılan şey iki algoritmanın aynı iş için süresi.
  const ortalama = (sec: (r: (typeof rotalar)[number]) => number) =>
    rotalar.length ? rotalar.reduce((t, r) => t + sec(r), 0) / rotalar.length : 0
  const dijkstra = ortalama((r) => r.arama.dijkstra.sureSn)
  const astar = ortalama((r) => r.arama.astar.sureSn)
  const ayni = rotalar.length > 0 && rotalar.every((r) => r.arama.ayniYol === true)
  const bilinmiyor = rotalar.some((r) => r.arama.ayniYol == null)
  const uzunlukAyni =
    rotalar.length > 0 && rotalar.every((r) => r.arama.dijkstra.uzunlukM === r.arama.astar.uzunlukM)
  const ms = (sn: number) => `${(sn * 1000).toFixed(0)} ms`

  return (
    <Bolum baslik="Arama" ek={<Micro>rota başına · {sayi(rotalar.length)} rota</Micro>}>
      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-control bg-raised px-2.5 py-2">
          <Micro>Dijkstra</Micro>
          <p className="text-body text-ink">{ms(dijkstra)}</p>
        </div>
        <div className="rounded-control bg-raised px-2.5 py-2">
          <Micro>A*</Micro>
          <p className="text-body text-ink">{ms(astar)}</p>
        </div>
      </div>
      <p className="mt-2 text-small text-ink-2">
        {ayni
          ? 'İkisi de aynı yolu buldu; A* daha az düğüm açtığı için hızlı.'
          : bilinmiyor
            ? uzunlukAyni
              ? 'Uç "aynı yol mu" demiyor; iki aramanın uzunlukları aynı çıktı.'
              : 'Uç "aynı yol mu" demiyor; uzunluklar da farklı.'
            : 'İki arama farklı yol buldu — sebebi incelenmeli.'}
      </p>
    </Bolum>
  )
}

export type { SimAlan }
