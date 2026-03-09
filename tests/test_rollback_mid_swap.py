import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, 'tools')
import rollback_from_snapshot as rb  # noqa: E402


class InjectedFailure(Exception):
    pass


def _write(path: Path, data: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding='utf-8')


def _checks(root: Path):
    out = {}
    for p in root.rglob('*'):
        if p.is_file():
            rel = str(p.relative_to(root)).replace('\\', '/')
            out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def test_mid_swap_failure(tmp_path: Path, monkeypatch):
    repo = tmp_path / 'repo'
    repo.mkdir()

    gen_dir = repo / 'detections/windows/rules/generated'
    _write(gen_dir / 'existing.yaml', 'original-content')

    snapshot = tmp_path / 'snapshot'
    snap_gen = snapshot / 'detections/windows/rules/generated'
    _write(snap_gen / 'existing.yaml', 'snapshot-content')

    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'id': 'smoke', 'checksums': _checks(snapshot)}), encoding='utf-8')

    monkeypatch.setattr(rb, 'FAILURE_HOOK', 'mid-swap')

    with pytest.raises(RuntimeError):
        rb.rollback_from_snapshot(
            snapshot_dir=str(snapshot),
            manifest_path=str(manifest),
            repo_root=str(repo),
        )

    original_file = repo / 'detections/windows/rules/generated/existing.yaml'
    assert original_file.exists()
    assert original_file.read_text(encoding='utf-8') == 'original-content'

    backups = list((repo / 'detections_backup').rglob('*'))
    assert backups

    audit = repo / 'governance/rollback_audit.json'
    assert audit.exists()
    data = json.loads(audit.read_text(encoding='utf-8'))
    assert data.get('status') == 'rollback_restore'
