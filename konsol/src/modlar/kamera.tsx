import { useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { ArrowsOut, Warning } from '@phosphor-icons/react'
import { Amac, Bolum, HazirSecenekler, SuAn, Teknik, VeriYok } from '@/kabuk/Panel'
import { Micro, Rozet } from '@/kabuk/parcalar'
import { IsaretliFoto, TespitListesi, hasarliSirali } from '@/kabuk/IsaretliFoto'
import { FotoInceleme } from '@/kabuk/FotoInceleme'
import { apiPost } from '@/veri/istemci'
import { useKameraCozumleme, type KameraSonucu, type KameraTespiti } from '@/durum/cozumlemeDurumu'
import type { Tespit } from '@/veri/ihbar'
import { sayi } from '@/lib/bicim'
import { GelenIhbarlar } from './ihbarParcalari'

/* Kamera modu: saha fotoğrafında çatlak ve yapı hasarı tespiti (YOLO).
   Görsel sunucuya gönderilir, model orada koşar; sonuç kutularıyla döner.

   J-165: kutular tarayıcıda, gönderilen fotoğrafın üstüne numaralı çizilir
   (sunucunun resme bastığı etiket Türkçe harfleri "??" yapıyordu). Fotoğrafa
   tıklayınca tam ekran incelenir. Çatlak modelinin sınıfı derece taşımaz:
   ekran çatlak için "kritik" ya da "boşaltın" demez. */

const MODELLER = [
  { id: 'hybrid', etiket: 'İkisi birden' },
  { id: 'catlak', etiket: 'Yalnız çatlak' },
  { id: 'bina', etiket: 'Yalnız yapı hasarı' },
] as const
type ModelId = (typeof MODELLER)[number]['id']

/** Afetzede ihbarlarıyla aynı derece puanı (sunucu `ihbar.SINIF`). */
const DERECE: Record<KameraTespiti['siddet'], number> = { agir: 1, orta: 0.6, belirsiz: 0.5, yok: 0 }

function tespiteCevir(t: KameraTespiti): Tespit {
  return {
    model: t.model.startsWith('catlak') ? 'catlak' : 'bina',
    sinif: t.sinif ?? null,
    ad: t.label,
    hasar: t.siddet !== 'yok',
    skor: DERECE[t.siddet] ?? 0.5,
    guven: (t.confidence ?? 0) / 100,
    kutu: [t.box[0], t.box[1], t.box[2], t.box[3]],
  }
}

/** Sonucun başlığı: ne bulundu, hangi tonla. Çatlak tek başına "kritik" değildir. */
function sonucBasligi(tespitler: KameraTespiti[]): { metin: string; ton: 'crit' | 'high' | 'mid' | 'nötr' } {
  const say = (s: KameraTespiti['siddet']) => tespitler.filter((t) => t.siddet === s).length
  const [agir, orta, catlak] = [say('agir'), say('orta'), say('belirsiz')]
  if (agir) return { metin: `${sayi(agir)} ağır yapı hasarı işareti`, ton: 'crit' }
  if (orta) return { metin: `${sayi(orta)} orta yapı hasarı işareti`, ton: 'high' }
  if (catlak) return { metin: `${sayi(catlak)} çatlak işareti`, ton: 'mid' }
  if (tespitler.length) return { metin: 'Yalnız hasarsız sınıfı', ton: 'nötr' }
  return { metin: 'Tespit yok', ton: 'nötr' }
}

export function KameraSol() {
  const [model, setModel] = useState<ModelId>('hybrid')
  const [dosyaAdi, setDosyaAdi] = useState<string | null>(null)
  const girdi = useRef<HTMLInputElement>(null)
  const sonucYaz = useKameraCozumleme((d) => d.yaz)

  const coz = useMutation({
    mutationFn: (g: { imageBase64: string; modelType: string; dosyaAdi: string }) =>
      apiPost<KameraSonucu>('/api/camera/analyze', { imageBase64: g.imageBase64, modelType: g.modelType }),
    onSuccess: (sonuc, g) => sonucYaz(sonuc, g.imageBase64, g.dosyaAdi),
  })

  function dosyaSec(dosya: File | undefined) {
    if (!dosya) return
    setDosyaAdi(dosya.name)
    const okuyucu = new FileReader()
    okuyucu.onload = () => {
      coz.mutate({ imageBase64: String(okuyucu.result), modelType: model, dosyaAdi: dosya.name })
    }
    okuyucu.readAsDataURL(dosya)
    // Aynı dosya yeniden seçilebilsin (başka modelle denemek için).
    if (girdi.current) girdi.current.value = ''
  }

  return (
    <Bolum baslik="Kamera tespiti" ek={<Micro>YOLO</Micro>}>
      <Amac>
        Sahadan gelen fotoğrafta ne var? Çatlağı ve yapı hasarı sınıfını işaretler; sonucu sağda
        büyütüp inceleyebilirsin.
      </Amac>

      <HazirSecenekler etiket="Model seçimi" secenekler={MODELLER} secili={model} onSec={setModel} />

      <input
        ref={girdi}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => dosyaSec(e.target.files?.[0])}
      />
      <button
        type="button"
        onClick={() => girdi.current?.click()}
        disabled={coz.isPending}
        className="mt-3 w-full rounded-control bg-accent px-3 py-2.5 text-body font-semibold text-accent-ink disabled:opacity-40"
      >
        {coz.isPending ? 'Model koşuyor…' : 'Fotoğraf seç'}
      </button>

      {dosyaAdi && <p className="mt-2 truncate text-small text-ink-3">Dosya: {dosyaAdi}</p>}
      {coz.isError && (
        <p role="alert" className="mt-2 text-small text-crit">
          {coz.error instanceof Error ? coz.error.message : 'Çözümlenemedi.'}
        </p>
      )}

      <SuAn>
        {coz.data
          ? `${MODELLER.find((m) => m.id === model)?.etiket} koşuldu: ${sayi(coz.data.detections?.length ?? 0)} tespit.`
          : 'Bir fotoğraf seç; tespitler sağ panelde görünür.'}
      </SuAn>

      <Teknik>
        Güven eşiği bilinçli olarak duyarlılık lehine ayarlıdır (%20): afet ortamında gözden kaçan
        hasarın maliyeti yanlış alarmdan yüksektir. Modellerin bilinen tek başarım sayısı eğitimdeki
        doğrulama mAP@50'dir (çatlak 0,731 · bina 0,592); iyimserdir, bağımsız bir sınamada
        ölçülmedi. Her analiz işlem kaydına yazılır; fotoğraf saklanmaz.
      </Teknik>
    </Bolum>
  )
}

/** Afetzedelerin gönderdiği hasar fotoğrafları kamera modunun başında durur
    (J-51): ekip yeni fotoğrafı burada görür, sonra kendi fotoğrafını da
    inceletebilir. */
export function KameraSag() {
  // Kendi analizin varsa en üstte: az önce gönderdiğin fotoğrafı aramak zorunda kalma.
  const sonucVar = useKameraCozumleme((d) => d.sonuc != null)
  const gelen = (
    <GelenIhbarlar
      tur="fotograf"
      baslik="Afetzedelerden gelen fotoğraflar"
      amac="Afetzedenin seçtiği modelle incelenip ihbar edilen hasar fotoğrafları. Seçince fotoğraf, işaretler ve konum açılır."
    />
  )
  return sonucVar ? (
    <>
      <KendiTespitlerim />
      {gelen}
    </>
  ) : (
    <>
      {gelen}
      <KendiTespitlerim />
    </>
  )
}

function KendiTespitlerim() {
  const sonuc = useKameraCozumleme((d) => d.sonuc)
  const gorsel = useKameraCozumleme((d) => d.gorsel)
  const dosyaAdi = useKameraCozumleme((d) => d.dosyaAdi)
  const [inceleme, setInceleme] = useState<{ acik: boolean; sira: number | null }>({ acik: false, sira: null })
  const [vurgu, setVurgu] = useState<number | null>(null)

  if (!sonuc) {
    return (
      <Bolum baslik="Kendi fotoğrafın">
        <Amac>Soldan seçtiğin fotoğraftaki tespitler burada görünür; fotoğrafa tıklayınca büyür.</Amac>
        <div className="mt-2">
          <VeriYok ne="Tespit" neden="henüz fotoğraf gönderilmedi" />
        </div>
      </Bolum>
    )
  }

  const ham = sonuc.detections ?? []
  const tespitler = ham.map(tespiteCevir)
  const isaretli = hasarliSirali(tespitler)
  const baslik = sonucBasligi(ham)
  const foto = gorsel && sonuc.imageWidth && sonuc.imageHeight
    ? { veri: gorsel, en: sonuc.imageWidth, boy: sonuc.imageHeight }
    : null
  const enYuksek = ham.length ? Math.max(...ham.map((t) => t.confidence)) : null
  const ac = (sira: number | null) => setInceleme({ acik: true, sira })

  const ozet = (
    <div>
      <div className="flex flex-wrap items-center gap-2">
        <Rozet ton={baslik.ton}>{baslik.metin}</Rozet>
      </div>
      <p className="mt-2 flex gap-2 text-small text-ink-2">
        {(baslik.ton === 'crit' || baslik.ton === 'high') && (
          <Warning size={16} className="mt-0.5 shrink-0 text-high" aria-hidden />
        )}
        <span>{sonuc.advice}</span>
      </p>
    </div>
  )
  const kunye = (
    <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-small">
      <dt className="text-ink-3">Model</dt>
      <dd className="text-ink">{sonuc.activeModels?.map((m) => m.split(' ')[0]).join(', ') || '—'}</dd>
      <dt className="text-ink-3">En yüksek güven</dt>
      <dd className="font-mono text-ink">{enYuksek == null ? '—' : `%${Math.round(enYuksek)}`}</dd>
      <dt className="text-ink-3">Süre</dt>
      <dd className="font-mono text-ink">{sonuc.sureMs == null ? '—' : `${sayi(sonuc.sureMs)} ms`}</dd>
      <dt className="text-ink-3">Fotoğraf</dt>
      <dd className="font-mono text-ink">{foto ? `${foto.en}×${foto.boy}` : '—'}</dd>
    </dl>
  )

  return (
    <Bolum baslik="Kendi fotoğrafın" ek={<Micro>{sayi(isaretli.length)} işaret</Micro>}>
      {ozet}

      {foto ? (
        <button
          type="button"
          onClick={() => ac(null)}
          className="group relative mt-2.5 block w-full rounded-control focus-visible:outline-2 focus-visible:outline-accent"
          aria-label="Fotoğrafı tam ekranda incele"
        >
          <IsaretliFoto
            veri={foto.veri}
            en={foto.en}
            boy={foto.boy}
            tespitler={tespitler}
            className="h-56"
            numarali
            secili={vurgu}
          />
          <span className="absolute right-2 bottom-2 flex items-center gap-1.5 rounded-control border border-line-2 bg-panel px-2 py-1 text-small text-ink group-hover:bg-hover">
            <ArrowsOut size={14} aria-hidden />
            Büyüt
          </span>
        </button>
      ) : (
        sonuc.annotatedImage && (
          <img src={sonuc.annotatedImage} alt="Model tespitleriyle işaretlenmiş fotoğraf" className="mt-2.5 w-full rounded-control border border-line" />
        )
      )}

      {isaretli.length === 0 ? (
        <p className="mt-2 text-small text-ink-2">
          Model bu fotoğrafta hasar işaretlemedi. Bu, hasar yok demek değil: eşiğin altında kalan hasar
          işaretlenmez.
        </p>
      ) : (
        <div className="mt-2">
          <TespitListesi tespitler={tespitler} numarali secili={vurgu} onSec={ac} onVurgula={setVurgu} />
        </div>
      )}

      <div className="mt-3 border-t border-line pt-2.5">{kunye}</div>
      <Teknik>
        Sonuç gönderilen fotoğrafın kendisinden çıkar; konum gönderilmediği için haritaya düşmez. Bu
        analiz işlem kaydına yazıldı: kim, ne zaman, ne bulundu (fotoğraf saklanmaz).
      </Teknik>

      {foto && (
        <FotoInceleme
          acik={inceleme.acik}
          kapat={() => setInceleme({ acik: false, sira: null })}
          baslik={`Kamera tespiti · ${dosyaAdi ?? 'fotoğraf'}`}
          veri={foto.veri}
          en={foto.en}
          boy={foto.boy}
          tespitler={tespitler}
          baslangic={inceleme.sira}
          ozet={ozet}
          kunye={kunye}
        />
      )}
    </Bolum>
  )
}
