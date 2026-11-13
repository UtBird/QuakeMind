import { Panel } from './Panel'
import { PanelSiniri } from './PanelSiniri'
import { Micro } from './parcalar'
import { GenelSag } from '@/modlar/genel'
import { SosSag } from '@/modlar/sos'
import { EkiplerSag } from '@/modlar/ekipler'
import { IhtiyacSag } from '@/modlar/ihtiyac'
import { BildirimSag } from '@/modlar/bildirim'
import { HasarSag } from '@/modlar/hasar'
import { KameraSag } from '@/modlar/kamera'
import { MetinSag } from '@/modlar/metin'
import { RiskSag } from '@/modlar/risk'
import { YolSag } from '@/modlar/yol'
import { SimulasyonSag } from '@/modlar/simulasyon'
import type { PanelModu } from '@/modlar/modlar'
import { useAralik } from '@/durum/zamanDurumu'
import { tarih } from '@/lib/bicim'

const MOD_PANELI: Record<PanelModu, () => React.JSX.Element> = {
  genel: GenelSag,
  sos: SosSag,
  ekipler: EkiplerSag,
  ihtiyac: IhtiyacSag,
  bildirim: BildirimSag,
  hasar: HasarSag,
  kamera: KameraSag,
  metin: MetinSag,
  risk: RiskSag,
  yol: YolSag,
  simulasyon: SimulasyonSag,
}

export function SagPanel({ mod }: { mod: PanelModu }) {
  const ModPaneli = MOD_PANELI[mod]
  const [t0, t1] = useAralik()

  return (
    <Panel
      baslik="Antakya · durum"
      ek={
        <Micro>
          {tarih(t0)} – {tarih(t1)}
        </Micro>
      }
    >
      <PanelSiniri baslik={'Durum paneli'}>
        <ModPaneli />
      </PanelSiniri>
    </Panel>
  )
}
