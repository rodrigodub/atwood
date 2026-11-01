# Profile camera browser persistence

## Outcome

Each saved profile restores its own MapLibre camera after a page refresh and
when the user switches profiles.

## Approach

1. Add browser-only camera records to `atwood.profile-camera.v1`, keyed by
   profile ID and containing a validated center, zoom, bearing, and pitch.
2. Save a profile's settled camera on map movement only while that saved
   profile is active. Snapshot the outgoing profile before beginning a switch.
3. Render cached profile GeoJSON first, then restore its saved camera. When a
   profile has no saved camera, retain the current `fitBounds` behavior and
   save that resulting camera as its initial view.
4. Guard programmatic map changes so `fitBounds` and camera restoration do not
   overwrite persisted state as user interactions.
5. Remove deleted and stale profile camera records. Ignore malformed or
   unavailable browser storage without affecting map use.
6. Add page-contract tests for the storage key, restoration order, movement
   persistence, and deletion cleanup.

## Constraints

- Preserve the active-profile storage key, existing API calls, MapLibre
  identifiers, form controls, and cached-profile behavior.
- Do not persist a camera for unsaved/default settings.
- Do not change layout, focus, Settings collapse state, or profile-control
  accessibility while restoring a camera.

## Validation

Run `uv run pytest tests/test_profile_api.py`.
