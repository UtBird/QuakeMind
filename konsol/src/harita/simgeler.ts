import { SIMGE_YOLU, type SimgeAdi } from './simgeYollari'
import { tokenRenk } from './tokenRenk'

/* ---------------------------------------------------------------------------
   Harita simgeleri (J-172). Her nokta türü ayrı ŞEKİL + GLİF + RENK taşır;
   renk tek başına anlam taşımaz (ARAYUZ §6):
     * olay (SOS, ihbar)        -> daire
     * ekip                      -> yuvarlak köşeli kare, araç glifi
     * yer (toplanma, sağlık)    -> kare, hafif küçük
     * kapanma                   -> kırmızı daire, yasak glifi
   Simgeler SVG olarak bir kez üretilir (deck.gl IconLayer `getIcon`), renkler
   token dosyasından okunur. Panel ve lejant aynı resmi kullanır (`simgeAdresi`).
--------------------------------------------------------------------------- */

type Sekil = 'daire' | 'kare'

export type SimgeTanimi = {
  glif: SimgeAdi
  sekil: Sekil
  zemin: `--color-${string}`
  /** Glif rengi: açık zeminde koyu, koyu zeminde açık. */
  glifRengi: `--color-${string}`
  kenar?: `--color-${string}`
}

export type SimgeTuru =
  | 'sos-kritik'
  | 'sos-yuksek'
  | 'sos-orta'
  | 'ihbar-fotograf'
  | 'ihbar-metin'
  | 'ihbar-ihtiyac'
  | 'ekip-musait'
  | 'ekip-gorevde'
  | 'ekip-disi'
  | 'toplanma'
  | 'hastane'
  | 'saglik'
  | 'kapanma'

export const SIMGE: Record<SimgeTuru, SimgeTanimi> = {
  'sos-kritik': { glif: 'sos', sekil: 'daire', zemin: '--color-crit', glifRengi: '--color-ink' },
  'sos-yuksek': { glif: 'sos', sekil: 'daire', zemin: '--color-high', glifRengi: '--color-ground' },
  'sos-orta': { glif: 'sos', sekil: 'daire', zemin: '--color-mid', glifRengi: '--color-ground' },
  'ihbar-fotograf': { glif: 'fotograf', sekil: 'daire', zemin: '--color-ihbar-fotograf', glifRengi: '--color-ground' },
  'ihbar-metin': { glif: 'metin', sekil: 'daire', zemin: '--color-ihbar-metin', glifRengi: '--color-ground' },
  'ihbar-ihtiyac': { glif: 'ihtiyac', sekil: 'daire', zemin: '--color-ihbar-ihtiyac', glifRengi: '--color-ground' },
  'ekip-musait': { glif: 'ekip', sekil: 'kare', zemin: '--color-accent', glifRengi: '--color-accent-ink' },
  'ekip-gorevde': { glif: 'ekip', sekil: 'kare', zemin: '--color-ink', glifRengi: '--color-ground', kenar: '--color-accent' },
  'ekip-disi': { glif: 'ekip', sekil: 'kare', zemin: '--color-ink-3', glifRengi: '--color-ground' },
  toplanma: { glif: 'toplanma', sekil: 'kare', zemin: '--color-yer-toplanma', glifRengi: '--color-ground' },
  hastane: { glif: 'hastane', sekil: 'kare', zemin: '--color-yer-saglik', glifRengi: '--color-ground' },
  saglik: { glif: 'hastane', sekil: 'kare', zemin: '--color-yer-saglik', glifRengi: '--color-ground' },
  kapanma: { glif: 'kapanma', sekil: 'daire', zemin: '--color-crit', glifRengi: '--color-ink' },
}

const BOY = 64

function hex(ad: `--color-${string}`): string {
  const [r, g, b] = tokenRenk(ad)
  return `#${[r, g, b].map((x) => x.toString(16).padStart(2, '0')).join('')}`
}

function svg(t: SimgeTanimi, secili: boolean): string {
  const zemin = hex(t.zemin)
  const kenar = secili ? hex('--color-ink') : t.kenar ? hex(t.kenar) : hex('--color-ground')
  const kalin = secili ? 6 : t.kenar ? 5 : 4
  const govde =
    t.sekil === 'daire'
      ? `<circle cx="32" cy="32" r="${29 - kalin / 2}" fill="${zemin}" stroke="${kenar}" stroke-width="${kalin}"/>`
      : `<rect x="${3 + kalin / 2}" y="${3 + kalin / 2}" width="${58 - kalin}" height="${58 - kalin}" rx="12" fill="${zemin}" stroke="${kenar}" stroke-width="${kalin}"/>`
  // Glif 256x256 kutudan 30 piksele: ortada.
  const glif = SIMGE_YOLU[t.glif].map((d) => `<path d="${d}"/>`).join('')
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" width="${BOY}" height="${BOY}" viewBox="0 0 ${BOY} ${BOY}">` +
    govde +
    `<g transform="translate(17 17) scale(0.1172)" fill="${hex(t.glifRengi)}">${glif}</g></svg>`
  )
}

const onbellek = new Map<string, string>()

/** Simgenin veri adresi (harita, katman paneli ve lejant aynı resmi kullanır). */
export function simgeAdresi(tur: SimgeTuru, secili = false): string {
  const anahtar = `${tur}:${secili ? 1 : 0}`
  let adres = onbellek.get(anahtar)
  if (!adres) {
    adres = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg(SIMGE[tur], secili))}`
    onbellek.set(anahtar, adres)
  }
  return adres
}

/** deck.gl IconLayer `getIcon` için. */
export function ikon(tur: SimgeTuru, secili = false) {
  return { id: `${tur}${secili ? '-secili' : ''}`, url: simgeAdresi(tur, secili), width: BOY, height: BOY, mask: false }
}

/* Küme simgesi (J-191): türün şekli ve rengi, glifsiz; ortasına sayı yazılır.
   Şekil türü söyler (olay daire, yer ve ekip kare), renk tek başına değil. */
const kumeOnbellek = new Map<SimgeTuru, string>()

function kumeSvg(t: SimgeTanimi): string {
  const zemin = hex(t.zemin)
  const kenar = hex('--color-ground')
  const govde =
    t.sekil === 'daire'
      ? `<circle cx="32" cy="32" r="28" fill="${zemin}" stroke="${kenar}" stroke-width="4"/>`
      : `<rect x="4" y="4" width="56" height="56" rx="14" fill="${zemin}" stroke="${kenar}" stroke-width="4"/>`
  // İkinci, sönük halka: tek simgeden ayrılsın, "birden çok" okunsun.
  const halka =
    t.sekil === 'daire'
      ? `<circle cx="32" cy="32" r="22" fill="none" stroke="${kenar}" stroke-opacity=".35" stroke-width="2"/>`
      : `<rect x="10" y="10" width="44" height="44" rx="10" fill="none" stroke="${kenar}" stroke-opacity=".35" stroke-width="2"/>`
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${BOY}" height="${BOY}" viewBox="0 0 ${BOY} ${BOY}">${govde}${halka}</svg>`
}

/** deck.gl IconLayer `getIcon` için küme simgesi. */
export function kumeIkonu(tur: SimgeTuru) {
  let adres = kumeOnbellek.get(tur)
  if (!adres) {
    adres = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(kumeSvg(SIMGE[tur]))}`
    kumeOnbellek.set(tur, adres)
  }
  return { id: `kume-${tur}`, url: adres, width: BOY, height: BOY, mask: false }
}
