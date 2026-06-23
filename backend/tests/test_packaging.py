from pathlib import Path


def test_windows_nuitka_script_bundles_runtime_resources():
    script_path = Path(__file__).parents[2] / "build" / "windows-package.ps1"
    script_content = script_path.read_text(encoding="utf-8")

    assert "--mode=standalone" in script_content
    assert "--windows-console-mode=disable" in script_content
    assert "--windows-icon-from-ico" in script_content
    assert "frontend/dist" in script_content
    assert "alembic.ini" in script_content
    assert "alembic/env.py" in script_content
    assert "alembic/versions/" in script_content
    assert "--include-package=app" in script_content
    assert "--include-package=uvicorn" in script_content
    assert "--include-package=webview" not in script_content
    assert "--include-module=webview.platforms.winforms" in script_content
    assert "--include-module=clr" in script_content
    assert "--include-module=clr_loader" in script_content
    assert "--report=" in script_content
    assert "-replace '[\\\\/:*?\"<>|]', \"-\"" in script_content


def test_release_workflow_sanitizes_installer_version():
    workflow_path = Path(__file__).parents[2] / ".github" / "workflows" / "releases.yml"
    workflow_content = workflow_path.read_text(encoding="utf-8")

    assert "PACKAGE_VERSION=$version" in workflow_content
    assert "-replace '[\\\\/:*?\"<>|]', \"-\"" in workflow_content
    assert 'iscc build/installer.iss /DMyAppVersion="$env:PACKAGE_VERSION"' in workflow_content
