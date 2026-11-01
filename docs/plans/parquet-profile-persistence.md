# Parquet profile persistence

## Goal

Replace browser-local profile and configuration persistence with a server-side
profile cache in `datasets/profiles.parquet`.

## Agreed scope

- Store profile metadata, source settings, field mappings, and cached GeoJSON
  features in one Parquet file.
- Persist that file across Docker refreshes through a host bind mount.
- Replace ad-hoc source and mapping settings with saved-profile management.
- The final map profile dropdown item is **New +**.
- **New +** presents sequential source, field-mapping, and profile-name modals.
- Settings can delete the active profile and its Parquet records.

## Profile data model

Use a flat schema so one Parquet file can contain profile metadata and cached
features:

- `schema_version`, `record_type` (`profile` or `feature`), `profile_id`, and
  `profile_name`.
- Source configuration: source type, Google Sheet URL, CSV path, SQLite path,
  SQLite table, and header row.
- Field mapping: point ID, X/Y coordinate, description, and point colour.
- Cached-feature fields: sort order, longitude, latitude, point ID,
  description, and display colour.
- Creation/update timestamp on profile rows.

One metadata row exists for every profile, including empty GeoJSON. Feature rows
are reconstructed into the existing FeatureCollection response shape on load.
Profile mutations use an atomic temporary-file rewrite and replace because
Parquet is immutable.

## Backend

1. Add `atwood.services.profile_persistence`, resolving the store from
   `ATWOOD_PROFILE_STORE` or the current data root’s
   `datasets/profiles.parquet`.
2. Add profile APIs:
   - `GET /profiles/` for summaries.
   - `POST /profiles/` to validate source and mapping, build GeoJSON, and
     persist metadata plus cached features.
   - `GET /profiles/{profile_id}` to return saved metadata and cached GeoJSON.
   - `DELETE /profiles/{profile_id}` to remove all records for a profile.
3. Keep `/source/inspect/` and `/source/data/` behavior intact for the new
   profile-creation flow.
4. Add `pyarrow` with uv, then regenerate the lockfile and runtime
   `requirements.txt`.

## Frontend

1. Replace `keyboard-odyssey.map-config.v1` and
   `keyboard-odyssey.map-profiles.v1` use with the profile APIs. Browser-local
   profiles cannot be migrated automatically.
2. Make the map profile dropdown load profiles from `GET /profiles/` and
   append **New +** as its final option.
3. Build accessible, cancellable Bootstrap modals for:
   - Source selection and inspection.
   - Field mapping and preview.
   - Profile naming and saving.
4. Load selected profiles from cached GeoJSON instead of re-fetching their
   external or local source.
5. Add active-profile deletion to Settings with confirmation.
6. Preserve current MapLibre source/layer IDs, clustering, popups, endpoint
   validation, keyboard behavior, and error messages.

## Docker and documentation

- Ensure the non-root runtime user can write the mounted profile store.
- Use a host bind mount at `/app/datasets`; do not bake runtime profiles into
  the image.
- Document the mount command and host-directory write permission requirement
  in the README.
- Update architecture documentation and add an ADR for Parquet-backed profile
  storage and the browser-local migration boundary.

## Validation

- Test empty, corrupt, and round-trip Parquet storage; profile deletion; empty
  feature collections; duplicate-name behavior; and safe atomic writes.
- Test create/list/load/delete endpoints and verify cached loads do not invoke
  source loading.
- Test that the rendered page contains the New-profile modal flow.
- Run the full pytest suite, package build, and a Docker persistence smoke test
  that creates a profile, replaces the container, and reloads the profile.

## Refresh behavior

Cached Parquet GeoJSON loads by default. This release also provides a manual
**Refresh profile** action that re-fetches the saved original source and
atomically replaces that profile’s cached Parquet records.
