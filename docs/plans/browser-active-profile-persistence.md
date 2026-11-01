# Browser active-profile persistence

## Outcome

Restore the last successfully loaded or saved server profile after a browser
page refresh, using its cached GeoJSON without refetching the original source.

## Approach

1. Add an `atwood.active-profile.v1` local-storage contract and focused helpers
   to `src/atwood/templates/index.html`.
2. Record a profile ID only after `saveProfile()` or `loadProfile()` succeeds,
   and clear it after that active profile is successfully deleted.
3. After the initial profile list has populated, validate the persisted ID
   against that list and load it using the existing cached profile endpoint.
4. Quietly discard stale or invalid persisted IDs. Retain the ID for transient
   loading failures, so a later refresh can retry without losing the choice.
5. Add a page-contract assertion for the storage key and restoration flow in
   `tests/test_profile_api.py`.

## Constraints

- Keep restoration visually silent: do not expand Settings, move focus, open a
  modal, or change the MapLibre layout.
- Preserve existing IDs, Bootstrap and ARIA attributes, API endpoints, and
  MapLibre source/layer identifiers.
- Only the explicit Refresh profile action may refetch the saved source.

## Validation

Run the focused page/API test module with `uv run pytest tests/test_profile_api.py`.
