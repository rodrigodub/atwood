# Global browser map camera

## Outcome

Keep one browser-persisted MapLibre camera across all profiles. Switching,
saving, refreshing, or deleting a profile changes its data without changing
the current map view.

## Approach

1. Replace the profile-keyed `atwood.profile-camera.v1` store with one
   validated `atwood.map-camera.v1` camera record.
2. Remove the obsolete profile-camera key without migrating it, because no
   individual profile should determine the global view.
3. Persist the global camera after settled user map movements only.
4. Render profile GeoJSON without fitting its bounds when a valid global camera
   exists; restore that global camera after deferred map rendering on startup.
5. When no global camera exists, retain the first profile's `fitBounds` view
   and persist it once as the initial global camera.
6. Preserve the global camera through profile saves, switches, refreshes,
   deletion, and profile-list changes.
7. Update page-contract coverage for global storage and the removal of
   profile-scoped camera handling.

## Constraints

- Keep `atwood.active-profile.v1`, cached profile loading, endpoints, element
  IDs, and MapLibre layer/source identifiers unchanged.
- Ignore malformed or unavailable browser storage safely.
- Do not write camera state for programmatic restore, initial fit, or
  resize/minimum-zoom adjustments.

## Validation

Run `uv run pytest tests/test_profile_api.py`.
