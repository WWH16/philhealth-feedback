"""
Database backup and restore utilities.

Supports both Local and Vercel (serverless AWS Lambda) environments without
requiring external database CLI binaries (mysqldump, pg_dump, psql, mysql) on PATH.

Backups are created as standard Django JSON fixtures via `dumpdata` (or SQL if provided).
Restores load JSON fixtures via `loaddata` inside an atomic transaction, or execute SQL
statements directly / via available DB tools.

Files live in settings.BACKUP_DIR or BASE_DIR/backups, falling back to tempfile.gettempdir()/backups
when the filesystem is read-only (e.g. on Vercel).
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.core.management import call_command
from django.db import connection, transaction
from django.utils import timezone

BACKUP_FILENAME_RE = re.compile(r'^philhealth_backup_\d{8}_\d{6}\.(json|sql)$')


def get_backup_dir() -> Path:
    """Returns the writable backup directory.
    On Local: uses settings.BACKUP_DIR or BASE_DIR/backups.
    On Vercel (serverless read-only filesystem): falls back to /tmp/backups.
    """
    configured = getattr(settings, 'BACKUP_DIR', None)
    candidate = Path(configured) if configured else settings.BASE_DIR / 'backups'
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        # Verify writability (critical on Vercel where BASE_DIR cannot be written to)
        test_file = candidate / '.write_perm_test'
        test_file.touch()
        test_file.unlink()
        return candidate
    except (OSError, PermissionError):
        pass

    backup_dir = Path(tempfile.gettempdir()) / 'backups'
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return backup_dir


def get_db_settings():
    return settings.DATABASES['default']


def _defaults_file(db_settings):
    """Writes a short-lived 0600 mysql options file for MySQL cli fallback."""
    fd = tempfile.NamedTemporaryFile(mode='w', suffix='.cnf', delete=False)
    fd.write('[client]\n')
    fd.write(f"user={db_settings.get('USER', '')}\n")
    fd.write(f"password={db_settings.get('PASSWORD', '')}\n")
    fd.write(f"host={db_settings.get('HOST') or 'localhost'}\n")
    fd.write(f"port={db_settings.get('PORT') or '3306'}\n")
    fd.close()
    try:
        Path(fd.name).chmod(0o600)
    except (OSError, NotImplementedError):
        pass
    return fd.name


def _human_size(num_bytes):
    size = float(num_bytes)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024:
            return f'{int(size)} {unit}' if unit == 'B' else f'{size:.1f} {unit}'
        size /= 1024
    return f'{size:.1f} TB'


def create_backup():
    """Creates a timestamped database backup.
    Uses pure-Python Django dumpdata serializer to avoid any external binary dependency
    (works on Windows, Linux, and Vercel serverless without pg_dump or mysqldump).
    """
    backup_dir = get_backup_dir()
    timestamp = timezone.localtime(timezone.now()).strftime('%Y%m%d_%H%M%S')
    filename = f'philhealth_backup_{timestamp}.json'
    dest_path = backup_dir / filename

    try:
        with open(dest_path, 'w', encoding='utf-8') as out:
            call_command(
                'dumpdata',
                exclude=['contenttypes', 'auth.permission', 'sessions'],
                natural_foreign=True,
                natural_primary=True,
                indent=2,
                stdout=out,
            )
    except Exception as exc:
        dest_path.unlink(missing_ok=True)
        raise RuntimeError(f'Backup creation failed: {exc}') from exc

    return {'filename': filename, 'size_bytes': dest_path.stat().st_size}


def list_backups():
    """Returns backup metadata, newest first (supports both .json and .sql dumps)."""
    backup_dir = get_backup_dir()
    rows = []
    for path in backup_dir.glob('philhealth_backup_*.*'):
        if not BACKUP_FILENAME_RE.match(path.name):
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        ts_match = re.search(r'philhealth_backup_(\d{8}_\d{6})', path.name)
        if ts_match:
            ts_str = ts_match.group(1)
            try:
                created = timezone.make_aware(datetime.datetime.strptime(ts_str, '%Y%m%d_%H%M%S'))
            except (ValueError, OverflowError):
                created = timezone.make_aware(datetime.datetime.fromtimestamp(stat.st_mtime))
        else:
            created = timezone.make_aware(datetime.datetime.fromtimestamp(stat.st_mtime))

        rows.append({
            'filename': path.name,
            'size_bytes': stat.st_size,
            'size_display': _human_size(stat.st_size),
            'created_at': created,
            'created_display': timezone.localtime(created).strftime('%b %d, %Y · %I:%M %p'),
            'extension': path.suffix.lstrip('.').upper(),
        })
    rows.sort(key=lambda r: r['created_at'], reverse=True)
    return rows


def resolve_backup_path(filename):
    if not BACKUP_FILENAME_RE.match(filename):
        raise SuspiciousFileOperation('Invalid backup filename.')
    path = get_backup_dir() / filename
    if not path.is_file():
        raise FileNotFoundError(filename)
    return path


def delete_backup(filename):
    resolve_backup_path(filename).unlink()


def _iter_file_chunks(file_obj, chunk_size=65536):
    if hasattr(file_obj, 'chunks'):
        yield from file_obj.chunks()
    else:
        while True:
            chunk = file_obj.read(chunk_size)
            if not chunk:
                break
            yield chunk


def restore_backup(uploaded_file):
    """Restores the database from an uploaded .json or .sql backup file.
    Takes a safety backup of the current database before applying changes.
    Supports both Django UploadedFile instances and standard file-like objects.
    """
    filename = getattr(uploaded_file, 'name', '') or 'backup'
    is_json = filename.lower().endswith('.json')
    is_sql = filename.lower().endswith('.sql')

    head = uploaded_file.read(4096)
    uploaded_file.seek(0)
    head_text = head.decode('utf-8', errors='ignore').strip()

    if not is_json and not is_sql:
        if head_text.startswith('[') or head_text.startswith('{'):
            is_json = True
        elif any(marker in head_text for marker in ('CREATE TABLE', 'INSERT INTO', 'PostgreSQL database dump', 'MySQL dump', '--')):
            is_sql = True
        else:
            raise ValueError('The uploaded file does not look like a valid .json or .sql backup.')

    safety = create_backup()

    if is_json:
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='wb') as tmp:
            for chunk in _iter_file_chunks(uploaded_file):
                tmp.write(chunk)
            tmp_path = Path(tmp.name)

        try:
            with open(tmp_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as err:
                    raise ValueError(f'Invalid JSON format: {err}')
                if not isinstance(data, list):
                    raise ValueError('Invalid backup format: expected a JSON array of fixtures.')

            models_in_fixture = {
                item.get('model') for item in data if isinstance(item, dict) and 'model' in item
            }

            from feedback.models import FeedbackEntry

            with transaction.atomic():
                if 'feedback.feedbackentry' in models_in_fixture:
                    FeedbackEntry.objects.all().delete()
                call_command('loaddata', str(tmp_path))
        except Exception as exc:
            raise RuntimeError(f'Failed to restore JSON backup: {exc}') from exc
        finally:
            tmp_path.unlink(missing_ok=True)

    else:
        with tempfile.NamedTemporaryFile(suffix='.sql', delete=False, mode='wb') as tmp:
            for chunk in _iter_file_chunks(uploaded_file):
                tmp.write(chunk)
            tmp_path = Path(tmp.name)

        try:
            db_settings = get_db_settings()
            engine = db_settings.get('ENGINE', '')
            is_postgres = 'postgresql' in engine or 'postgres' in engine
            is_mysql = 'mysql' in engine

            if is_postgres and shutil.which('psql'):
                env = os.environ.copy()
                if db_settings.get('PASSWORD'):
                    env['PGPASSWORD'] = str(db_settings['PASSWORD'])
                cmd = [
                    'psql',
                    '-h', db_settings.get('HOST', 'localhost'),
                    '-p', str(db_settings.get('PORT', 5432)),
                    '-U', db_settings.get('USER', 'postgres'),
                    '-d', db_settings.get('NAME', 'postgres'),
                ]
                with open(tmp_path, 'rb') as sql_in:
                    res = subprocess.run(cmd, stdin=sql_in, stderr=subprocess.PIPE, env=env)
                if res.returncode != 0:
                    raise RuntimeError(res.stderr.decode(errors='replace')[:500])

            elif is_mysql and shutil.which('mysql'):
                cnf_path = _defaults_file(db_settings)
                try:
                    with open(tmp_path, 'rb') as sql_in:
                        res = subprocess.run(
                            ['mysql', f'--defaults-extra-file={cnf_path}', db_settings['NAME']],
                            stdin=sql_in,
                            stderr=subprocess.PIPE,
                        )
                    if res.returncode != 0:
                        raise RuntimeError(res.stderr.decode(errors='replace')[:500])
                finally:
                    Path(cnf_path).unlink(missing_ok=True)

            else:
                with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as sql_file:
                    sql_text = sql_file.read()
                with connection.cursor() as cursor:
                    cursor.execute(sql_text)
        except Exception as exc:
            raise RuntimeError(f'Failed to restore SQL backup: {exc}') from exc
        finally:
            tmp_path.unlink(missing_ok=True)

    return safety