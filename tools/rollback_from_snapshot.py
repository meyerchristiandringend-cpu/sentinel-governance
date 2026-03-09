#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

FAILURE_HOOK = os.getenv('FAILURE_HOOK')


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def dir_size_bytes(path: Path) -> int:
    total = 0
    for p in path.rglob('*'):
        if p.is_file():
            total += p.stat().st_size
    return total


def verify_snapshot_limit(snapshot_dir: Path, max_bytes: int):
    size = dir_size_bytes(snapshot_dir)
    if size > max_bytes:
        raise RuntimeError(f'Snapshot too large: {size} bytes > {max_bytes} bytes limit.')


def verify_checksums(snapshot_dir: Path, manifest: dict):
    checks = manifest.get('checksums', {})
    for rel, expected in checks.items():
        rel_path = Path(rel)
        if '..' in rel_path.parts:
            raise RuntimeError(f'Invalid checksum path with traversal: {rel}')
        candidate = snapshot_dir / rel_path
        if not candidate.exists() or not candidate.is_file():
            raise RuntimeError(f'Missing file in snapshot for checksum validation: {rel}')
        got = file_sha256(candidate)
        if got != expected:
            raise RuntimeError(f'Checksum mismatch for {rel}: {got} != {expected}')


def safe_relpath(path: Path, base: Path) -> Path:
    rel = path.relative_to(base)
    if '..' in rel.parts:
        raise RuntimeError(f'Unsafe relative path: {rel}')
    return rel


def collect_source_generated_dirs(snapshot_dir: Path) -> list[tuple[Path, Path]]:
    mappings = []

    snapshot_detections = snapshot_dir / 'detections'
    if snapshot_detections.exists():
        for src_gen in snapshot_detections.rglob('rules/generated'):
            if src_gen.is_dir():
                rel = safe_relpath(src_gen, snapshot_detections)
                mappings.append((rel, src_gen))

    direct_generated = snapshot_dir / 'generated'
    if direct_generated.exists() and direct_generated.is_dir() and not mappings:
        mappings.append((Path('default/rules/generated'), direct_generated))

    if not mappings:
        raise RuntimeError('No generated rule directories found in snapshot.')

    return mappings


def apply_file_permissions(root: Path, file_mode: int):
    if os.name == 'nt':
        return
    for p in root.rglob('*'):
        if p.is_file():
            p.chmod(file_mode)


def atomic_replace_generated(snapshot_dir: Path, repo_root: Path, file_mode: int = 0o640):
    detections_root = repo_root / 'detections'
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup_root = repo_root / 'detections_backup' / stamp
    staging_root = repo_root / '.rollback_staging' / stamp
    temp_old_root = repo_root / '.rollback_old' / stamp

    mappings = collect_source_generated_dirs(snapshot_dir)
    backup_root.mkdir(parents=True, exist_ok=True)
    staging_root.mkdir(parents=True, exist_ok=True)
    temp_old_root.mkdir(parents=True, exist_ok=True)

    replaced_paths = []
    swapped_targets = []
    injected = False

    try:
        for rel, src in mappings:
            if 'rules' not in rel.parts or 'generated' not in rel.parts:
                raise RuntimeError(f'Invalid generated path layout in snapshot: {rel}')

            target = detections_root / rel
            stage_target = staging_root / rel
            stage_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, stage_target, dirs_exist_ok=True)

            if target.exists():
                backup_target = backup_root / rel
                backup_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(target, backup_target, dirs_exist_ok=True)

        for rel, _ in mappings:
            target = detections_root / rel
            stage_target = staging_root / rel
            old_target = temp_old_root / rel
            old_target.parent.mkdir(parents=True, exist_ok=True)

            if target.exists():
                shutil.move(str(target), str(old_target))
            shutil.move(str(stage_target), str(target))
            apply_file_permissions(target, file_mode)

            swapped_targets.append((target, old_target))
            replaced_paths.append(str(target).replace('\\', '/'))

            if FAILURE_HOOK == 'mid-swap' and not injected:
                injected = True
                raise RuntimeError('Injected mid-swap failure')

        for _, old_target in swapped_targets:
            if old_target.exists():
                shutil.rmtree(old_target)

        shutil.rmtree(staging_root, ignore_errors=True)
        shutil.rmtree(temp_old_root, ignore_errors=True)
        return str(backup_root), replaced_paths

    except Exception as exc:
        for target, old_target in reversed(swapped_targets):
            try:
                if target.exists():
                    shutil.rmtree(target)
                if old_target.exists():
                    old_target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(old_target), str(target))
            except Exception:
                pass

        shutil.rmtree(staging_root, ignore_errors=True)
        shutil.rmtree(temp_old_root, ignore_errors=True)
        raise RuntimeError(f'Atomic replace failed and was rolled back: {exc}')


def write_audit(repo_root: Path, manifest: dict, backup_path: str, replaced_paths: list[str], duration_seconds: float, error: str | None, status: str):
    audit = {
        'snapshot_id': manifest.get('id', 'unknown'),
        'manifest_release': manifest.get('manifest_release', manifest.get('release', '')),
        'git_commit': manifest.get('git_commit', ''),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'operator': os.getenv('GITHUB_ACTOR', 'local'),
        'backup_path': backup_path,
        'replaced_paths': replaced_paths,
        'duration_seconds': round(duration_seconds, 3),
        'status': status,
        'error': error,
    }
    out = repo_root / 'governance' / 'rollback_audit.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')


def acquire_lock(lock_path: Path):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode('utf-8'))
    os.close(fd)


def release_lock(lock_path: Path):
    if lock_path.exists():
        lock_path.unlink()


def rollback_from_snapshot(snapshot_dir: str, manifest_path: str, repo_root: str | None = None, max_snapshot_bytes: int = 2 * 1024 * 1024 * 1024, file_mode: int = 0o640):
    root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    start = time.monotonic()
    lock_path = root / '.rollback_lock'
    backup_path = ''
    replaced_paths: list[str] = []
    status = 'failed_pre_swap'

    manifest = load_json(Path(manifest_path).resolve())

    try:
        acquire_lock(lock_path)
        sdir = Path(snapshot_dir).resolve()
        if not sdir.exists():
            raise RuntimeError(f'Snapshot directory not found: {sdir}')

        verify_snapshot_limit(sdir, max_snapshot_bytes)
        verify_checksums(sdir, manifest)

        backup_path, replaced_paths = atomic_replace_generated(sdir, root, file_mode=file_mode)
        status = 'success'
        duration = time.monotonic() - start
        write_audit(root, manifest, backup_path, replaced_paths, duration, None, status)
        return {'status': status, 'backup_path': backup_path, 'replaced_paths': replaced_paths}

    except Exception as exc:
        err = str(exc)
        if 'rolled back' in err.lower():
            status = 'rollback_restore'
        duration = time.monotonic() - start
        write_audit(root, manifest, backup_path, replaced_paths, duration, err, status)
        raise

    finally:
        release_lock(lock_path)


def main():
    parser = argparse.ArgumentParser(description='Rollback generated detection rules from a signed snapshot')
    parser.add_argument('--snapshot-dir', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--max-snapshot-bytes', type=int, default=2 * 1024 * 1024 * 1024)
    parser.add_argument('--file-mode', default='640', help='POSIX mode for restored files (ignored on Windows)')
    args = parser.parse_args()

    mode = int(args.file_mode, 8)
    rollback_from_snapshot(
        snapshot_dir=args.snapshot_dir,
        manifest_path=args.manifest,
        repo_root=str(Path.cwd()),
        max_snapshot_bytes=args.max_snapshot_bytes,
        file_mode=mode,
    )
    print('Rollback completed successfully.')


if __name__ == '__main__':
    main()
