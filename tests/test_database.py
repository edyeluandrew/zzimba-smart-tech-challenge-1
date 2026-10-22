from app.database import normalize_database_url


def test_sqlite_url_is_unchanged():
    assert normalize_database_url("sqlite:///./luweero.db") == "sqlite:///./luweero.db"


def test_neon_url_uses_pg8000_and_drops_libpq_params():
    raw = (
        "postgresql://user:pass@ep-x-pooler.eu-central-1.aws.neon.tech/neondb"
        "?sslmode=require&channel_binding=require"
    )
    normalized = normalize_database_url(raw)
    assert normalized == "postgresql+pg8000://user:pass@ep-x-pooler.eu-central-1.aws.neon.tech/neondb"


def test_legacy_postgres_scheme_is_rewritten():
    raw = "postgres://user:pass@ep-x.eu-central-1.aws.neon.tech/neondb"
    normalized = normalize_database_url(raw)
    assert normalized == "postgresql+pg8000://user:pass@ep-x.eu-central-1.aws.neon.tech/neondb"
