# Parquet-backed profile store

## Status
Accepted

## Decision
Store profile metadata, source settings, mappings, and cached GeoJSON features
as flat rows in `datasets/profiles.parquet`. Resolve an explicit
`ATWOOD_PROFILE_STORE` before the data-root default. Each mutation validates
the current Parquet file and atomically replaces it; a corrupt file is never
overwritten.

## Consequences
Profiles are shared by users of an application instance and browser-local
profiles are not migrated. Cached loads do not contact the original source;
users may explicitly refresh a profile. Docker deployments bind mount
`/app/datasets` to retain the store.
