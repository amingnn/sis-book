import asyncio

import pytest
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.static import SPAStaticFiles


def _static_files(tmp_path) -> SPAStaticFiles:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<div id='root'>sis-book</div>", encoding="utf-8")
    assets = dist / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("window.__sisBook = true;", encoding="utf-8")
    return SPAStaticFiles(directory=str(dist), html=True)


def _get_response(files: SPAStaticFiles, path: str):
    scope = {"type": "http", "method": "GET", "path": f"/{path}", "headers": []}
    return asyncio.run(files.get_response(path, scope))


def test_static_files_fallback_to_index_for_spa_routes(tmp_path):
    response = _get_response(_static_files(tmp_path), "tasks")

    assert response.status_code == 200


def test_static_files_keep_api_and_asset_404(tmp_path):
    files = _static_files(tmp_path)

    with pytest.raises(StarletteHTTPException) as api_exc:
        _get_response(files, "api/missing")
    with pytest.raises(StarletteHTTPException) as asset_exc:
        _get_response(files, "assets/missing.js")

    assert api_exc.value.status_code == 404
    assert asset_exc.value.status_code == 404
