from pathlib import Path


def test_runtime_profile_store_is_excluded_from_docker_build_context() -> None:
    root = Path(__file__).parents[1]
    ignored_paths = set((root / ".dockerignore").read_text(encoding="utf-8").splitlines())

    assert {
        "datasets/profiles.parquet",
        "datasets/profiles.parquet.lock",
    }.issubset(ignored_paths)
