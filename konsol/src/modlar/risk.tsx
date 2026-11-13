import { useQuery } from '@tanstack/react-query'
import { Amac, Bolum, HazirSecenekler, SuAn, Teknik, VeriYok } from '@/kabuk/Panel'
import { Micro, Rozet } from '@/kabuk/parcalar'
import { apiGet, apiPost } from '@/veri/istemci'
import { useHarita } from '@/harita/HaritaKabugu'
import { BOLGELER, type BolgeId } from '@/veri/analiz'
import { useCozumleme } from '@/durum/cozumlemeDurumu'
import { sayi } from '@/lib/bicim'

/* Risk modu: bir şehir için kısa vadeli model riski, uzun vadeli tehlike ve
   fay etkisi. Model sunucuda dosyadan yüklenir; istek yolunda eğitim yoktur. */

type RiskYaniti = {
  city: string
  coordinates: { lat: number; lon: number }
  riskScore: number
  riskLevel: string
  lastUpdate?: string
  factors: Record<string, number>
  metrics: {
    shortRisk: number
    longHazard: number
    faultScore: number
    faultDistanceKm: number
    heatSampleCount?: number
    totalFaultFeatures?: number
  }
  /** Sunucu bunları hazır metin olarak veriyor: "Dogu Anadolu Fayi (5.5 km)",
      "M1.8 - 114 km - 2026-08-13". */
  nearbyFaults?: string[]
  recentEvents?: string[]
}

/** Sunucu seviye metnini emoji ile veriyor; arayüzde emoji kullanılmaz
    (ARAYUZ §2), renk zaten rozetten geliyor. */
function seviyeMetni(ham: string): string {
  return ham.replace(/[^\p{L}\p{N}\s]/gu, '').trim()
}

function seviyeTonu(skor: number): 'crit' | 'high' | 'mid' | 'ok' {
  if (skor >= 75) return 'crit'
  if (skor >= 50) return 'high'
  if (skor >= 25) return 'mid'
  return 'ok'
}

/** 81 il merkezi: sunucu yerel OSM kopyasından bir kez üretir
    (araclar_il_merkezleri_uret.py). Konum dış servisten aranmaz. */
type IlMerkezi = { il: string; merkez: string; lat: number; lon: number; osm: string }
type IlListesi = {
  iller: IlMerkezi[]
  kaynak: { atif: string; lisans: string; dosyaTarihi: string; yontem: string } | null
}

const IL_ONEKI = 'il:'

function useIller() {
  return useQuery({
    queryKey: ['risk-iller'],
    staleTime: Infinity,
    queryFn: () => apiGet<IlListesi>('/api/risk/iller'),
  })
}

/** Seçim ya bir harita bölgesinin kimliği ya da `il:<ad>`. */
function hedefi(secim: string | null, iller: IlMerkezi[] | undefined) {
  if (!secim) return null
  if (secim.startsWith(IL_ONEKI)) {
    const il = iller?.find((x) => x.il === secim.slice(IL_ONEKI.length))
    return il ? { ad: il.il, lat: il.lat, lon: il.lon } : null
  }
  return BOLGELER.find((x) => x.id === (secim as BolgeId)) ?? null
}

function useRisk(secim: string | null) {
  const iller = useIller()
  const h = hedefi(secim, iller.data?.iller)
  return useQuery({
    queryKey: ['risk', secim],
    enabled: !!h,
    queryFn: () =>
      apiPost<RiskYaniti>('/api/risk/predict', {
        city: h!.ad,
        manualLatitude: h!.lat,
        manualLongitude: h!.lon,
      }),
  })
}

export function RiskSol() {
  const secim = useCozumleme((d) => d.riskBolge)
  const sec = useCozumleme((d) => d.riskBolgeSec)
  const risk = useRisk(secim)
  const iller = useIller()
  const { ucus } = useHarita()

  return (
    <Bolum baslik="Deprem riski" ek={<Micro>CatBoost</Micro>}>
      <Amac>
        Hangi bölgede önümüzdeki dönemde risk daha yüksek? Sismik geçmiş, fay uzaklığı ve son
        hareketlilik birlikte değerlendirilir.
      </Amac>

      <HazirSecenekler
        etiket="Bölgeler"
        secenekler={BOLGELER.map((b) => ({ id: b.id, etiket: b.ad }))}
        secili={secim as BolgeId | null}
        onSec={(id) => {
          sec(id)
          const b = BOLGELER.find((x) => x.id === id)
          if (b) ucus(b.lon, b.lat, 9)
        }}
      />

      <label className="mt-3 block text-micro ls-micro text-ink-3 uppercase" htmlFor="risk-il">
        81 il
      </label>
      {iller.isError || (iller.data && !iller.data.iller.length) ? (
        <div className="mt-1.5">
          <VeriYok
            ne="İl listesi"
            neden="il merkezleri üretilmedi (araclar_il_merkezleri_uret.py)"
          />
        </div>
      ) : (
        <select
          id="risk-il"
          value={secim?.startsWith(IL_ONEKI) ? secim : ''}
          disabled={!iller.data}
          onChange={(e) => {
            if (!e.target.value) return
            sec(e.target.value)
            const il = iller.data?.iller.find((x) => IL_ONEKI + x.il === e.target.value)
            if (il) ucus(il.lon, il.lat, 11)
          }}
          className="mt-1.5 w-full rounded-control border border-line-2 bg-sunken px-2.5 py-2 text-body text-ink"
        >
          <option value="">{iller.data ? 'İl seç…' : 'İl listesi yükleniyor…'}</option>
          {(iller.data?.iller ?? []).map((il) => (
            <option key={il.il} value={IL_ONEKI + il.il}>
              {il.il}
            </option>
          ))}
        </select>
      )}

      <SuAn>
        {risk.isFetching
          ? 'Model koşuyor…'
          : risk.data
            ? `${risk.data.city}: risk skoru ${risk.data.riskScore}, en yakın fay ${risk.data.metrics.faultDistanceKm.toFixed(
                1,
              )} km.`
            : 'Bir bölge ya da il seç; sonuç sağ panelde bileşenleriyle görünür.'}
      </SuAn>

      {risk.isError && (
        <div className="mt-2">
          <VeriYok
            ne="Risk sonucu"
            neden="model dosyası yoksa sunucu eğitim komutunu istiyor (araclar_risk_egit.py)"
          />
        </div>
      )}

      <Teknik>
        Model istek yolunda eğitilmez: eğitim ayrı bir komuttur, sonuç dosyaya yazılır, API
        yalnız yükler. Ölçüm: ilk istek 1,7 sn (soğuk), sonrakiler ortanca 168 ms.
      </Teknik>
      {iller.data?.kaynak && (
        <Teknik>
          İl merkezleri: {iller.data.kaynak.atif} ({iller.data.kaynak.lisans}), yerel kopya{' '}
          {iller.data.kaynak.dosyaTarihi}; il sınırı içindeki şehir noktası. Hesap il merkezi için
          yapılır, ilin tamamı için değil.
        </Teknik>
      )}
    </Bolum>
  )
}

export function RiskSag() {
  // Seçim mağazada; sol panelle aynı sorgu anahtarı paylaşıldığı için
  // ikinci bir istek atılmaz.
  const secim = useCozumleme((d) => d.riskBolge)
  const risk = useRisk(secim)
  const veri = risk.data

  if (!veri) {
    return (
      <Bolum baslik="Risk">
        <Amac>Seçilen bölgenin ya da ilin risk skoru ve bileşenleri burada görünür.</Amac>
        <div className="mt-2">
          <VeriYok ne="Risk" neden="henüz bölge ya da il seçilmedi" />
        </div>
      </Bolum>
    )
  }

  return <RiskSonucu veri={veri} />
}

export function RiskSonucu({ veri }: { veri: RiskYaniti }) {
  return (
    <>
      <Bolum baslik="Risk skoru" ek={<Micro>{veri.city}</Micro>}>
        <p className="font-cond text-metric text-ink">
          {veri.riskScore.toFixed(1).replace('.', ',')}
        </p>
        <p className="mt-1.5">
          <Rozet ton={seviyeTonu(veri.riskScore)}>{seviyeMetni(veri.riskLevel)}</Rozet>
        </p>

        <dl className="kilav-kv mt-3 gap-x-2.5 gap-y-1.5 text-small">
          <dt className="text-ink-3">Kısa vadeli</dt>
          <dd className="text-ink">{(veri.metrics.shortRisk * 100).toFixed(1).replace('.', ',')}</dd>
          <dt className="text-ink-3">Uzun vadeli</dt>
          <dd className="text-ink">
            {(veri.metrics.longHazard * 100).toFixed(1).replace('.', ',')}
          </dd>
          <dt className="text-ink-3">Fay etkisi</dt>
          <dd className="text-ink">
            {(veri.metrics.faultScore * 100).toFixed(1).replace('.', ',')}
          </dd>
          <dt className="text-ink-3">En yakın fay</dt>
          <dd className="text-ink">
            {veri.metrics.faultDistanceKm.toFixed(1).replace('.', ',')} km
          </dd>
        </dl>

        <Teknik>
          Skor üç bileşenin ağırlıklı toplamıdır (0,4 kısa + 0,3 uzun + 0,3 fay); ağırlıklar uzman
          tanımlıdır, ölçülmüş değildir. Kısa vadeli model zayıftır: yedi model karşılaştırmasında
          (13.643 kayıt, 5 katlı zamana göre doğrulama, 19 Ekim 2026) CatBoost ROC-AUC 0,61 ± 0,04,
          en iyisi lojistik regresyon 0,64 ± 0,06. Fay mesafesi GEM Global Active Faults (CC BY-SA
          4.0) çizgilerine en kısa uzaklıktır.
        </Teknik>
      </Bolum>

      {!!veri.nearbyFaults?.length && (
        <Bolum baslik="Yakın faylar">
          <ul>
            {veri.nearbyFaults.slice(0, 4).map((f) => (
              <li key={f} className="border-b border-line py-1.5 text-small text-ink-2 last:border-b-0">
                {f}
              </li>
            ))}
          </ul>
        </Bolum>
      )}

      {!!veri.recentEvents?.length && (
        <Bolum baslik="Son depremler" ek={<Micro>{sayi(veri.recentEvents.length)} kayıt</Micro>}>
          <ul>
            {veri.recentEvents.slice(0, 6).map((o, i) => (
              <li
                key={`${o}-${i}`}
                className="border-b border-line py-1.5 font-mono text-small text-ink-2 last:border-b-0"
              >
                {o}
              </li>
            ))}
          </ul>
        </Bolum>
      )}
    </>
  )
}
