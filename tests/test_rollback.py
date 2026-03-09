from pathlib import Path
import hashlib
import sys

sys.path.insert(0, 'tools')
import rollback_from_snapshot as rb  # noqa: E402


def write_file(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def checksum_map(root: Path):
    checks = {}
    for p in sorted(root.rglob('*')):
        if p.is_file():
            rel = str(p.relative_to(root)).replace('\\', '/')
            checks[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return checks


def test_atomic_replace_generated_only(tmp_path: Path):
    repo = tmp_path
    detections = repo / 'detections'
    write_file(detections / 'windows/rules/generated/orig-win.yaml', 'orig-win')
    write_file(detections / 'windows/rules/static/static.yaml', 'keep-me')

    snapshot = repo / 'snapshot'
    write_file(snapshot / 'detections/windows/rules/generated/new-win.yaml', 'new-win')

    backup, replaced = rb.atomic_replace_generated(snapshot, repo)

    assert (detections / 'windows/rules/generated/new-win.yaml').exists()
    assert not (detections / 'windows/rules/generated/orig-win.yaml').exists()
    assert (detections / 'windows/rules/static/static.yaml').read_text(encoding='utf-8') == 'keep-me'
    assert Path(backup).exists()
    assert any('windows/rules/generated' in p for p in replaced)


def test_idempotent_second_run(tmp_path: Path):
    repo = tmp_path
    detections = repo / 'detections'
    write_file(detections / 'linux/rules/generated/orig-linux.yaml', 'orig-linux')

    snapshot = repo / 'snapshot'
    write_file(snapshot / 'detections/linux/rules/generated/rule-linux.yaml', 'snap-linux')

    rb.atomic_replace_generated(snapshot, repo)
    first = (detections / 'linux/rules/generated/rule-linux.yaml').read_text(encoding='utf-8')

    rb.atomic_replace_generated(snapshot, repo)
    second = (detections / 'linux/rules/generated/rule-linux.yaml').read_text(encoding='utf-8')

    assert first == 'snap-linux'
    assert second == 'snap-linux'


def test_verify_checksums_blocks_traversal(tmp_path: Path):
    snapshot = tmp_path / 'snapshot'
    write_file(snapshot / 'detections/windows/rules/generated/r.yaml', 'x')

    manifest = {'checksums': {'../evil.txt': 'abcd'}}

    try:
        rb.verify_checksums(snapshot, manifest)
        assert False, 'Expected traversal to fail'
    except RuntimeError as exc:
        assert 'traversal' in str(exc).lower()


def test_verify_checksums_success(tmp_path: Path):
    snapshot = tmp_path / 'snapshot'
    write_file(snapshot / 'detections/windows/rules/generated/r.yaml', 'abc')
    checks = checksum_map(snapshot)
    manifest = {'checksums': checks}

    rb.verify_checksums(snapshot, manifest)
