import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { sorguIstemcisi } from '@/veri/istemci'
import { OturumSaglayici, useOturum } from '@/kimlik/oturum'
import { Bekleme, RolKapisi } from '@/kimlik/RolKapisi'
import { GirisEkrani } from '@/kimlik/GirisEkrani'
import { SifreDegistirmeEkrani } from '@/kimlik/SifreDegistirmeEkrani'
import { CanliSaglayici } from '@/canli/CanliSaglayici'
import { KONSOL_ROLLERI, acilisYolu } from '@/kimlik/roller'
import { VARSAYILAN_MOD } from '@/modlar/modlar'

// Rota bazlı kod bölme: afetzede ekranı harita motorunu indirmez (MIMARI §7).
const KonsolKabugu = lazy(() =>
  import('@/kabuk/KonsolKabugu').then((m) => ({ default: m.KonsolKabugu })),
)
const AfetzedeEkrani = lazy(() =>
  import('@/afetzede/AfetzedeEkrani').then((m) => ({ default: m.AfetzedeEkrani })),
)
// Saha ekibinin telefondaki görev ekranı (J-54); harita motorunu indirmez.
const EkipEkrani = lazy(() => import('@/ekip/EkipEkrani').then((m) => ({ default: m.EkipEkrani })))

export function App() {
  return (
    <QueryClientProvider client={sorguIstemcisi}>
      <OturumSaglayici>
        <CanliSaglayici>
          <BrowserRouter>
            <Suspense fallback={<Bekleme />}>
              <Routes>
                <Route path="/giris" element={<GirisEkrani />} />
                <Route path="/sifre-degistir" element={<SifreDegistirmeEkrani />} />
                <Route
                  path="/konsol/:mod"
                  element={
                    <RolKapisi izinli={KONSOL_ROLLERI}>
                      <KonsolKabugu />
                    </RolKapisi>
                  }
                />
                <Route
                  path="/konsol"
                  element={<Navigate to={`/konsol/${VARSAYILAN_MOD}`} replace />}
                />
                <Route
                  path="/afetzede"
                  element={
                    <RolKapisi izinli={['afetzede', 'koordinator', 'yonetici']}>
                      <AfetzedeEkrani />
                    </RolKapisi>
                  }
                />
                <Route
                  path="/ekip"
                  element={
                    <RolKapisi izinli={['saha', 'koordinator', 'yonetici']}>
                      <EkipEkrani />
                    </RolKapisi>
                  }
                />
                <Route path="*" element={<Acilis />} />
              </Routes>
            </Suspense>
          </BrowserRouter>
        </CanliSaglayici>
      </OturumSaglayici>
    </QueryClientProvider>
  )
}

/** Rol ne ise oraya: konsol ya da afetzede ekranı. */
function Acilis() {
  const { oturum, yukleniyor } = useOturum()
  if (yukleniyor) return <Bekleme />
  return <Navigate to={oturum ? acilisYolu(oturum) : '/giris'} replace />
}
