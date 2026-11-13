import { Panel } from './Panel'
import { PanelSiniri } from './PanelSiniri'
import { GenelSol } from '@/modlar/genel'
import { SosSol } from '@/modlar/sos'
import { EkiplerSol } from '@/modlar/ekipler'
import { IhtiyacSol } from '@/modlar/ihtiyac'
import { BildirimSol } from '@/modlar/bildirim'
import { HasarSol } from '@/modlar/hasar'
import { KameraSol } from '@/modlar/kamera'
import { MetinSol } from '@/modlar/metin'
import { RiskSol } from '@/modlar/risk'
import { YolSol } from '@/modlar/yol'
import { SimulasyonSol } from '@/modlar/simulasyon'
import { modBul, type PanelModu } from '@/modlar/modlar'

/* Sol panel: seçili modun paneli (J-56). Başlıkta modun adı yazar; üst
   çubukta mod değişince burada neyin değiştiği görünür. Eskiden başlık her
   modda "Katmanlar"dı ve altına her modda aynı katman ve kaynak listesi
   ekleniyordu; katmanlar artık haritanın köşesindeki düğmede. */

const MOD_PANELI: Record<PanelModu, () => React.JSX.Element> = {
  genel: GenelSol,
  sos: SosSol,
  ekipler: EkiplerSol,
  ihtiyac: IhtiyacSol,
  bildirim: BildirimSol,
  hasar: HasarSol,
  kamera: KameraSol,
  metin: MetinSol,
  risk: RiskSol,
  yol: YolSol,
  simulasyon: SimulasyonSol,
}

export function SolPanel({ mod }: { mod: PanelModu }) {
  const ModPaneli = MOD_PANELI[mod]
  return (
    <Panel baslik={modBul(mod)?.ad ?? 'Mod'}>
      <PanelSiniri baslik={modBul(mod)?.ad ?? 'Mod'}>
        <ModPaneli />
      </PanelSiniri>
    </Panel>
  )
}
