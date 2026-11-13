---
name: QuakeMind
description: Restrained native disaster readiness, with readable actions and explicit status.
colors:
  light-primary: "#176758"
  light-on-primary: "#FFFFFF"
  light-primary-container: "#E0EFE8"
  light-on-primary-container: "#154C40"
  light-secondary-container: "#E4ECE7"
  light-on-secondary-container: "#253C33"
  light-tertiary: "#305F82"
  light-tertiary-container: "#E2EDF7"
  light-background: "#F4F6F3"
  light-on-background: "#192D25"
  light-surface: "#FEFFFC"
  light-on-surface: "#192D25"
  light-surface-variant: "#E5EBE4"
  light-on-surface-variant: "#536159"
  light-surface-container-low: "#F6F8F3"
  light-surface-container: "#EDF1EA"
  light-surface-container-high: "#E6ECE3"
  light-outline: "#77877C"
  light-outline-variant: "#D4DDD2"
  light-error: "#AB302F"
  light-on-error: "#FFFFFF"
  light-error-container: "#FFEDEA"
  light-on-error-container: "#8D2425"
  dark-primary: "#A1D5BD"
  dark-on-primary: "#0D382C"
  dark-primary-container: "#204D3D"
  dark-on-primary-container: "#D0F0DF"
  dark-secondary-container: "#354D40"
  dark-on-secondary-container: "#D7EADC"
  dark-tertiary: "#A6CBE9"
  dark-tertiary-container: "#294C66"
  dark-background: "#101A16"
  dark-on-background: "#E0E9DF"
  dark-surface: "#17231D"
  dark-on-surface: "#E0E9DF"
  dark-surface-variant: "#2B3B31"
  dark-on-surface-variant: "#B5C5B7"
  dark-surface-container-low: "#142019"
  dark-surface-container: "#1C2921"
  dark-surface-container-high: "#26332B"
  dark-outline: "#879A8B"
  dark-outline-variant: "#3B4B40"
  dark-error: "#FFB4AC"
  dark-on-error: "#641C1B"
  dark-error-container: "#4A2320"
  dark-on-error-container: "#FFDAD4"
  light-success: "#237052"
  dark-success: "#9ED5B5"
  light-success-container: "#E8F4EA"
  dark-success-container: "#213C2D"
  light-warning: "#86520C"
  dark-warning: "#EBC17E"
  light-warning-container: "#FBF0DC"
  dark-warning-container: "#40331C"
typography:
  headline-large:
    fontFamily: "Android system sans-serif"
    fontSize: "32sp"
    lineHeight: "38sp"
    fontWeight: 500
    letterSpacing: "-0.8sp"
  headline-medium:
    fontFamily: "Android system sans-serif"
    fontSize: "28sp"
    lineHeight: "34sp"
    fontWeight: 500
    letterSpacing: "-0.6sp"
  headline-small:
    fontFamily: "Android system sans-serif"
    fontSize: "24sp"
    lineHeight: "30sp"
    fontWeight: 500
    letterSpacing: "-0.4sp"
  title-large:
    fontFamily: "Android system sans-serif"
    fontSize: "22sp"
    lineHeight: "28sp"
    fontWeight: 500
  title-medium:
    fontFamily: "Android system sans-serif"
    fontSize: "16sp"
    lineHeight: "23sp"
    fontWeight: 600
  body-large:
    fontFamily: "Android system sans-serif"
    fontSize: "16sp"
    lineHeight: "24sp"
  body-medium:
    fontFamily: "Android system sans-serif"
    fontSize: "14sp"
    lineHeight: "21sp"
  body-small:
    fontFamily: "Android system sans-serif"
    fontSize: "12sp"
    lineHeight: "18sp"
rounded:
  shape-6: "6dp"
  shape-8: "8dp"
  shape-12: "12dp"
  shape-16: "16dp"
  shape-20: "20dp"
spacing:
  space-4: "4dp"
  space-8: "8dp"
  space-12: "12dp"
  space-16: "16dp"
  space-20: "20dp"
  space-24: "24dp"
  space-28: "28dp"
components:
  card:
    backgroundColor: "{colors.light-surface}"
    textColor: "{colors.light-on-surface}"
    rounded: "{rounded.shape-16}"
    padding: "{spacing.space-20}"
  button-urgent:
    backgroundColor: "{colors.light-error}"
    textColor: "{colors.light-on-error}"
    rounded: "{rounded.shape-8}"
  button-text:
    textColor: "{colors.light-primary}"
  input-description:
    backgroundColor: "{colors.light-surface}"
    textColor: "{colors.light-on-surface}"
    rounded: "{rounded.shape-8}"
    height: "100dp"
  badge-status:
    backgroundColor: "{colors.light-surface-container-high}"
    textColor: "{colors.light-on-surface}"
    rounded: "{rounded.shape-6}"
    padding: "3dp 8dp"
  navigation:
    backgroundColor: "{colors.light-surface}"
  filter-selected:
    backgroundColor: "{colors.light-secondary-container}"
    textColor: "{colors.light-on-secondary-container}"
    rounded: "{rounded.shape-8}"
---
# Design System: QuakeMind

## Overview

**Creative North Star: "Calm Readiness"**

A quiet, native information surface for decisions under pressure. Forest-green actions, warm pale neutrals and compact sans-serif typography give urgent content room to be read. Red carries incident reporting and emergency meaning; ordinary navigation stays calm.

The user chose premium restraint and fluidity, with Eon informing shared component architecture. The implementation remains Kotlin and Compose: native feedback, saved state and lightweight surfaces support that direction. This document records source behavior, not a claim of measured smoothness, outdoor readability, device acceptance or accessibility certification.

**Key Characteristics:**
- Semantic color in both light and dark themes.
- Readable headings and content-sized shared headers.
- Flat, softly rounded native surfaces.
- Explicit local, pending, error and permission states.

## Colors

The palette combines forest green with pale mineral surfaces; dark mode uses deep green-black neutrals and lighter semantic foregrounds. The frontmatter records a reused subset of the current Theme.kt palette, with explicit light/dark keys. Android theme roles remain the runtime authority.

### Primary

- **Forest green:** primary actions, logo and normal selected navigation; the primary container supports softer selection.
- **Success green:** successful/local status and lower magnitude badges. Success text must describe the actual confirmed state.

### Secondary

- **Muted sage:** native Material selected filter containers use secondary-container and on-secondary-container roles.

### Tertiary

- **Slate blue:** informational alerts and contextual information.
- **Warm amber:** offline, medium-risk and warning status.
- **Emergency red:** report actions, SOS navigation and error/critical states. These are semantic roles, not general decoration.

### Neutral

- **Mineral paper / forest night:** background, surface and container hierarchy in the two modes.
- **Ink / pale leaf:** primary text, with on-surface-variant for supporting detail.
- **Soft outlines:** thin card boundaries and dividers.

**The Meaning Before Accent Rule.** Reserve emergency and warning tones for their semantic context; keep normal actions in primary green.

## Typography

**Display and Body Font:** Android system sans-serif through Material 3 Typography; no custom font is installed by this system. Frontmatter retains native sp values; HTML previews use numerical CSS-pixel approximations at default scale.

### Hierarchy

- **Headlines:** large, medium and small roles provide medium-weight titles with slightly tightened tracking. ScreenHeader uses headline-small and heading semantics.
- **Titles:** title-large identifies the app; title-medium anchors sections and summaries with semibold emphasis.
- **Body:** large, medium and small roles provide progressively denser explanatory copy and metadata.
- **Labels:** Material label roles remain native defaults, with label-large made semibold. Bottom navigation uses label-small and changes selected weight.

Keep Turkish sentence case and legible source, time, distance and permission details. Home truncates its greeting to one line; shared screen titles and subtitles have no imposed one-line limit.

## Layout

Android dp controls geometry and sp controls text; these units are intentionally retained in the machine-readable tokens. The shell centers non-map content with a maximum width of 840dp; the map remains full width. No browser breakpoint system is implemented.

Home uses a LazyColumn with stable keys/content types, 20dp horizontal content padding, 20dp section spacing and 28dp bottom padding. Its header uses 20dp horizontal and 12dp vertical padding. Shared ScreenHeader uses 16dp padding with an optional native back button and a weighted text column. Cards provide 20dp internal padding. Compact rows generally use 8–16dp gaps.

The bottom bar uses native navigation insets and items with a minimum height of 64dp. The app reserves bottom content space except for the full-screen map and applies keyboard padding. These source choices need large-text and device verification; they do not establish a universal minimum target size for every legacy control.

## Elevation & Depth

Depth is primarily tonal. QuakeCard uses a 1dp outline-variant border and no explicit shadow elevation. Bottom navigation explicitly sets tonal elevation to zero. Native Material controls retain their own state feedback; this is not a claim that every feature is shadow-free.

**The Flat Surface Rule.** Shared cards and bottom navigation use tonal separation and borders rather than decorative shadow.

## Shapes

Use softly rounded rectangles: compact badges use shape-6; magnitude badges, description fields and report buttons use shape-8; Material medium uses shape-12; shared cards and Home actions use shape-16; extra-large Material shapes use shape-20. Circle shapes are reserved for dots and circular status marks. Theme.kt also retains smaller legacy radius helpers; do not expand the shared scale without a need.

## Components

### Buttons

Report submission uses an emergency-filled button, shape-8, a minimum height of 52dp and an explicit disabled/submitting state. Text buttons carry secondary actions. ErrorState uses a bordered retry button. Press feedback and keyboard/accessibility behavior come from native Material components, not a custom hover animation.

### Chips

Home uses native FilterChip with selected state, horizontally scrollable filters and saved selection. StatusBadge is a compact bordered label; ConnectionStatusChip pairs a colored dot with explicit online/offline text. A dot alone does not convey status.

### Cards / Containers

QuakeCard is a full-width surface with shape-16, a thin outline and 20dp padding. Optional click handling clips to its shape. Home action tiles are separate flat surfaces with 16dp padding; do not assume every tile has QuakeCard's border.

### Inputs / Fields

Report description uses an outlined field with shape-8, a fixed 100dp height and an emergency-colored focus border. Its container uses the semantic surface role in both modes. Other Material inputs must be inspected before assuming identical overrides. Submission errors remain visible alongside the action.

### Navigation

Five native bottom destinations: Ana Sayfa, Harita, SOS, Uyarılar and Çanta. Normal selection uses primary-container indicators and primary text; SOS uses error roles even when unselected. Active icons and label weight reinforce selection. The shell saves/restores top-level navigation state and avoids re-navigating to the selected tab. Detail destinations omit the bar.

### Magnitude and offline status

Magnitude badges use success below 3.5, warning from 3.5 and emergency from 4.5; the number is always visible. They are static even if the retained showPulse argument is passed. OfflineModeBanner includes pending local report count when present. LoadingSkeleton currently renders a compact native progress indicator rather than a shimmer.

## Do's and Don'ts

### Do:
- Do use MaterialTheme semantic roles and shared QuakeCard and ScreenHeader components.
- Do retain Turkish action labels, source details and explicit local-versus-server status.
- Do keep headings content-sized and preserve native text scaling and interaction feedback.
- Do verify dark theme, large text and physical-device performance before declaring acceptance.

### Don't:
- Don't imply a local tracking code confirms server receipt or responder dispatch.
- Don't use emergency red as the default color of ordinary navigation.
- Don't introduce decorative looping motion or speculative performance guarantees.
- Don't treat the HTML previews as Android screenshots or native behavior tests.
