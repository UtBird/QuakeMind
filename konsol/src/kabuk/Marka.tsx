import { sn } from '@/lib/sinif'

/** `daraltilir`: dar ekranda (< 1280 px) yalnız simge kalır; üst çubuk sığsın.
    `'telefon'`: yalnız telefonda (< 640 px) simge kalır (afetzede ve saha ekranı, J-183). */
export function Marka({ daraltilir = false }: { daraltilir?: boolean | 'telefon' }) {
  return (
    <div className="flex shrink-0 items-center gap-2.5" title="QuakeMind">
      <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true" fill="none">
        <circle cx="10" cy="10" r="2" fill="var(--color-accent)" />
        <path
          d="M14.2 5.8a6 6 0 0 1 0 8.4"
          stroke="var(--color-accent)"
          strokeWidth="1.4"
          strokeLinecap="round"
          opacity=".85"
        />
        <path
          d="M5.8 14.2a6 6 0 0 1 0-8.4"
          stroke="var(--color-accent)"
          strokeWidth="1.4"
          strokeLinecap="round"
          opacity=".85"
        />
        <path
          d="M17 3a9.9 9.9 0 0 1 0 14"
          stroke="var(--color-accent)"
          strokeWidth="1.2"
          strokeLinecap="round"
          opacity=".38"
        />
        <path
          d="M3 17A9.9 9.9 0 0 1 3 3"
          stroke="var(--color-accent)"
          strokeWidth="1.2"
          strokeLinecap="round"
          opacity=".38"
        />
      </svg>
      <b
        className={sn(
          'font-cond text-subtitle font-semibold tracking-marka uppercase',
          daraltilir === 'telefon' ? 'hidden sm:inline' : daraltilir && 'hidden xl:inline',
        )}
      >
        QuakeMind
      </b>
    </div>
  )
}
