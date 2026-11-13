# QuakeMind

<!-- impeccable:product-schema 1 -->

## Platform

android

## Product Purpose

QuakeMind is a Turkish disaster preparedness and response application. It brings
earthquake records, nearby resources, incident reporting, personal safety status,
SOS, preparation checklists and server-backed analysis into one native interface.

## Operating Context

People may use the app under stress, outdoors, with limited connectivity. An
incident is saved locally before background synchronization; a local tracking code
does not mean a responder has been dispatched. SOS is not a replacement for 112.

## Capabilities and Constraints

The existing Kotlin/Compose application, typed Navigation Compose destinations,
feature ViewModels, Room queue and backend contracts remain the implementation.
Server results, permissions, errors and pending state must remain explicit.
Operations access comes from session capabilities. Do not invent verification,
downloaded maps, automated messages or response guarantees.

## Brand Commitments

The user requested a complete, premium, restrained mobile refactor with fluidity
as the priority, using the local Eon project as a component architecture reference.
The follow-up delegates completion with the available design skills.

## Product Principles

- Prioritize urgent actions and readable, verifiable information.
- Preserve input, navigation state and offline behavior.
- Use a shared component system and lightweight native interactions.
- Give each color a consistent meaning and each action a clear label.

## Evidence on Hand

`mobile/docs/BACKEND_INTEGRATION.md`, feature routes and ViewModels describe the
implemented services. Existing product-design documentation contains historical
aspirations; code and current contracts take precedence over unsupported claims.
