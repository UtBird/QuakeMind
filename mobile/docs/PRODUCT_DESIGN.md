# QuakeMind Product Design

## Information architecture

The five primary destinations are Home, Map, Report, Alerts, and Profile. Secondary
flows (analysis, routing, risk, safety, incident detail and operations) are opened
from those destinations and never compete for bottom-navigation space.

## Role and capability model

The backend returns capability strings. UI visibility is derived from capabilities,
not role-name comparisons. Citizen defaults include reporting, safety status and
viewing public resources. Volunteer capabilities add field verification. Operations
capabilities add assignment, rejection and status management.

## Core flows

1. Guest → Home → Emergency report → Confirm → local tracking code → background sync.
2. Home → Safe route → vehicle/preferences → route comparison → live route warning.
3. Map → layer filter → incident → bottom sheet → detail/verification.
4. Home → Damage analysis → camera/gallery → progress → review AI confidence → report.
5. Home → Safety status → one-tap state → optional location/contact delivery.

## Navigation graph

```text
Splash → Onboarding → Auth/Guest → Main
Main ├─ Home ─┬─ Earthquake detail
     │        ├─ Safety
     │        ├─ Risk
     │        └─ Routing
     ├─ Map ──── Incident detail
     ├─ Report ── Confirmation/tracking
     ├─ Alerts ── Linked incident/map
     └─ Profile ─ Settings/offline maps/privacy
Secondary: NLP analysis, Damage analysis, Operations
Deep links: /incident/{id}, /alert/{id}, /report/{id}, /map?lat=&lng=
```

## Visual system

- Color: Deep Navy `#0B1F33`, Primary `#176BCE`, Accent `#2F8FFF`, Teal
  `#00A6A6`; critical red is reserved for danger.
- Typography: platform sans-serif (Roboto fallback); large numeric metrics use
  `headlineLarge`, page titles `headlineSmall`, body content `bodyLarge`.
- Spacing: 4 dp base grid; common values 8, 12, 16, 24, 32.
- Shapes: cards 20 dp, controls 12 dp, sheets 28 dp. Touch targets are at least 48 dp.
- Themes: high-contrast light and dark palettes are implemented from the same semantic
  token set. Meaning is always repeated with icon/text, never color alone.

## Component inventory

Top app bar, emergency action, earthquake summary, risk badge, connection chip,
offline banner, incident/road/alert/metric cards, map layer selector, status timeline,
upload progress, AI confidence, empty/error/loading states, permission explanation,
confirmation sheet, emergency contact, sync status and safe-route summary.

## Wireframes

```text
HOME                         MAP
┌ City · status · GPS ┐      ┌ Search · layer/filter ┐
│ M 4.2  latest quake │      │      map canvas       │
│ source · distance   │      │  clustered markers   │
├ Emergency report ───┤      ├ selected incident ───┤
│ 2×3 quick actions   │      │ status · trust · CTA │
│ nearby / alerts     │      └ bottom navigation ───┘
└ bottom navigation ──┘

REPORT                        DAMAGE
┌ Step + saved draft ┐        ┌ Camera / Gallery ┐
│ event category     │        │ image preview    │
│ description + AI  │        │ upload progress  │
│ location + people │        │ result overlay   │
│ media + urgency   │        │ confidence/note  │
└ Review → save/send┘        └ Convert to report┘
```

## State design

Loading uses non-blocking skeletons, empty states explain the next action, errors give a
human-readable reason plus retry, and offline state stays visible with queued item
counts. Existing input is never cleared by transient errors.

## Responsive behavior

Phones use a bottom bar and single column. At 840 dp and above, content is capped to a
readable width; lists/cards can use two columns and navigation may migrate to a rail.
