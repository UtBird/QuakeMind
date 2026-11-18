import { Check, MapPin, UsersThree } from '@phosphor-icons/react'
import { useZaman } from '@/durum/zamanDurumu'
import { once, saat, saatte, sureMetni } from '@/lib/bicim'
import { sn } from '@/lib/sinif'
import { GOREV_ADIMLARI, acikGorev, kurumTur, type Gorev } from '@/veri/gorev'
import { mesafeMetni } from './konum'

/* ---------------------------------------------------------------------------
   Afetzedenin çağrısına ya da ihbarına gelen ekip (J-54).

   Kullanıcı kararı: afetzede ekibin adını, kaç kişi olduğunu, hangi aşamada
   olduğunu ve saatini, ekip konumunu paylaştıysa nerede olduğunu görür.
   Kimin atadığı ve koordinasyonun iç notu buraya gelmez (sunucu göndermez).
   Uzaklık ve süre araç yolundan (J-55): tek yönlere uyar, bilinen kapanmalardan kaçınır. Süre
   yol türüne göre ortalama hız varsayımıyla tahmindir, trafik verisi yok; ekibin son bildirdiği
   konuma göredir. Yol ağı dışında kuş uçuşu yazılır ve bu söylenir.
--------------------------------------------------------------------------- */

const SIRA = (g: Gorev) => GOREV_ADIMLARI.indexOf(g.durum)

/** Ekibin konumu bundan eskiyse afetzedeye süre gösterilmez: ekip o arada
    yer değiştirmiş olabilir, "~6 dk" yanıltır. Konumun yaşı yazılır. */
const TAZE_KONUM_DK = 10

function tazeYol(g: Gorev, simdi: number) {
  const z = g.ekipKonumu?.zaman
  return g.yol && z != null && simdi - z < TAZE_KONUM_DK * 60_000 ? g.yol : null
}

/** Açık görevlerden en ilerideki (olay yerinde > yolda > atandı). */
export function enIleriGorev(gorevler: Gorev[] | null | undefined): Gorev | null {
  const acik = (gorevler ?? []).filter(acikGorev)
  return acik.sort((a, b) => SIRA(b) - SIRA(a))[0] ?? null
}

const ekipKisi = (g: Gorev) => `${g.ekip.ad} (${g.kisiSayisi} kişi)`

/** Başlık ve tek cümle: çağrı ve ihbar kartı aynı dili kullanır. */
export function afetzedeDurumu(
  gorevler: Gorev[] | null | undefined,
  kapali: boolean,
  /** Görev kaydından (J-54) önce atanmış çağrı: ekip var, ayrıntısı yok. */
  eskiAtama = false,
  simdi = Date.now(),
): { baslik: string; aciklama: string; ton: 'high' | 'ok' | 'nötr' } {
  const liste = gorevler ?? []
  const acik = liste.filter(acikGorev)
  const ileri = enIleriGorev(liste)
  if (kapali) {
    const biten = liste.find((g) => g.durum === 'tamamlandi')
    return {
      baslik: 'Kapandı',
      aciklama: biten
        ? `${biten.ekip.ad} işini bitirdi${biten.bitti ? ` · ${saat(biten.bitti)}` : ''}.`
        : 'Kayıt kapatıldı.',
      ton: 'nötr',
    }
  }
  if (!ileri && eskiAtama)
    return { baslik: 'Ekip görevlendirildi', aciklama: 'Çağrına bir ekip görevlendirildi.', ton: 'ok' }
  if (!ileri) {
    // liste en yeniden eskiye (sunucu: ORDER BY atandi DESC).
    const son = liste[0]
    return {
      baslik: 'Bekliyor',
      aciklama:
        son?.durum === 'iptal'
          ? 'Görevlendirilen ekip gelemedi; koordinasyon başka ekip gönderecek.'
          : son?.durum === 'tamamlandi'
            ? // Ekip "olay sürüyor" diyerek bitirdi (J-174): kayıt kapanmadı, sıraya döndü.
              `${son.ekip.ad} işini bitirdi ama olay sürüyor; koordinasyon başka ekip gönderecek.`
            : 'Kaydın alındı, henüz ekip görevlendirilmedi. Ekip görevlendirilince adı ve nerede olduğu burada görünür.',
      ton: 'high',
    }
  }
  const baska = acik.length > 1 ? ` Toplam ${acik.length} ekip, ${acik.reduce((t, g) => t + g.kisiSayisi, 0)} kişi geliyor.` : ''
  if (ileri.durum === 'olay-yerinde')
    return {
      baslik: 'Ekip geldi',
      aciklama: `${ekipKisi(ileri)}${ileri.vardi ? ` ${saatte(ileri.vardi)}` : ''} olay yerine vardı.${baska}`,
      ton: 'ok',
    }
  if (ileri.durum === 'yolda')
    return {
      baslik: 'Ekip yolda',
      aciklama: `${ekipKisi(ileri)}${ileri.yolaCikti ? ` ${saatte(ileri.yolaCikti)}` : ''} yola çıktı.${
        tazeYol(ileri, simdi) ? ` Tahmini varış ~${sureMetni(tazeYol(ileri, simdi)!.sureDk)}.` : ''
      }${baska}`,
      ton: 'ok',
    }
  return {
    baslik: 'Ekip görevlendirildi',
    aciklama: `${ekipKisi(ileri)} ${saatte(ileri.atandi)} görevlendirildi; yola çıkınca burada görünür.${baska}`,
    ton: 'ok',
  }
}

/** Dört adım: alındı, ekip atandı, yolda, geldi. Atlanan adımın saati uydurulmaz. */
export function AfetzedeAdimlari({ olayZamani, gorevler }: { olayZamani: number; gorevler: Gorev[] | undefined }) {
  const g = enIleriGorev(gorevler)
  const sira = g ? SIRA(g) : -1
  const adimlar = [
    { ad: 'Alındı', zaman: olayZamani, tamam: true },
    { ad: 'Ekip atandı', zaman: g?.atandi ?? null, tamam: sira >= 0 },
    { ad: 'Yolda', zaman: g?.yolaCikti ?? null, tamam: sira >= 1 },
    { ad: 'Geldi', zaman: g?.vardi ?? null, tamam: sira >= 2 },
  ]
  return (
    <ol className="grid grid-cols-4 gap-1.5" aria-label="Çağrının aşamaları">
      {adimlar.map((a) => (
        <li
          key={a.ad}
          className={sn('rounded-control border px-2 py-1.5', a.tamam ? 'border-ok text-ink' : 'border-line-2 text-ink-3')}
        >
          <span className="flex items-center gap-1 text-small">
            {a.tamam && <Check size={12} weight="bold" className="text-ok" aria-hidden />}
            {a.ad}
          </span>
          <span className="block font-mono text-small text-ink-3">{a.zaman ? saat(a.zaman) : '—'}</span>
        </li>
      ))}
    </ol>
  )
}

/** Gelen ekibin kartı: ad, kurum, kaç kişi, nerede. */
export function GelenEkipKarti({ gorev: g }: { gorev: Gorev }) {
  const simdi = useZaman((z) => z.simdi)
  const k = g.ekipKonumu
  const yol = tazeYol(g, simdi)
  return (
    <div className="flex gap-2.5 rounded-control border border-line-2 bg-sunken px-3 py-2.5">
      <span aria-hidden className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-accent-soft text-accent">
        <UsersThree size={20} weight="bold" />
      </span>
      <div className="min-w-0 flex-1 text-small">
        <p className="text-body text-ink">
          <span className="font-semibold">{g.ekip.ad}</span>
          <span className="text-ink-2"> · {g.kisiSayisi} kişi</span>
        </p>
        {kurumTur(g.ekip) && <p className="text-ink-2">{kurumTur(g.ekip)}</p>}
        <p className="mt-1 flex gap-1.5 text-ink">
          <MapPin size={14} weight="bold" className="mt-0.5 shrink-0 text-accent" aria-hidden />
          <span>
            {g.durum === 'olay-yerinde'
              ? 'Ekip olay yerinde.'
              : k
                ? yol
                  ? `Ekip şu an ${k.yerAdi ? `${k.yerAdi} yakınında` : 'yolda'}; sana yoldan ~${sureMetni(yol.sureDk)} (${mesafeMetni(yol.mesafeM)}, tahmini).`
                  : g.yol
                    ? `Ekibin son bildirdiği yer ${k.yerAdi ? `${k.yerAdi} yakını` : 'yolda'}; konum eski olduğu için süre verilemiyor.`
                    : `Ekip şu an ${k.yerAdi ? `${k.yerAdi} yakınında` : 'yolda'}${
                        g.kalanM != null ? `, sana kuş uçuşu ${mesafeMetni(g.kalanM)}` : ''
                      }.`
                : g.cikis?.yerAdi
                  ? `${g.cikis.yerAdi} yakınından geliyor.`
                  : 'Ekibin konumu henüz paylaşılmadı.'}
            {k?.zaman && g.durum !== 'olay-yerinde' ? (
              <span className="text-ink-3"> Konumu {once(k.zaman, simdi)} bildirildi.</span>
            ) : null}
          </span>
        </p>
      </div>
    </div>
  )
}
