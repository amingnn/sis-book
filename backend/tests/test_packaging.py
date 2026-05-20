from pathlib import Path


def test_pyinstaller_spec_bundles_alembic_files():
    spec_path = Path(__file__).parents[2] / "build" / "sis-book.spec"
    spec_content = spec_path.read_text(encoding="utf-8")

    assert "alembic.ini" in spec_content
    assert "'alembic')" in spec_content
