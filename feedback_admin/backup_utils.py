"""
Manual MySQL backup/restore helpers.

Backups are full SQL dumps taken via `mysqldump` and restored via the
`mysql` client, run as subprocesses. Credentials are passed through a
short-lived, 0600-permission --defaults-extra-file so the DB password
never shows up in `ps aux` or shell history.

Files live in BASE_DIR/backups by default. Override with the
BACKUP_DIR setting (e.g. point it at a separate mounted volume on the
droplet) without touching this code.
"""
import datetime
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.utils import timezone

BACKUP_FILENAME_RE = re.compile(r'^philhealth_backup_\d{8}_\d{6}\.sql$')


def get_backup_dir():
    backup_dir = Path(getattr(settings, 'BACKUP_DIR', settings.BASE_DIR / 'backups'))
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        backup_dir = Path(tempfile.gettempdir()) / 'backups'
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
    return backup_dir


def get_db_settings():
    db_settings = settings.DATABASES['default']
    if db_settings['ENGINE'] != 'django.db.backends.mysql':
        raise NotImplementedError(
            'Backup/restore here only supports MySQL. If this project moves '
            'to another database engine, swap this module accordingly.'
        )
    return db_settings


def _require_binary(name):
    if shutil.which(name) is None:
        raise RuntimeError(
            f'"{name}" was not found on PATH. Make sure the MySQL client '
            f'tools are installed and on PATH (mysqldump.exe / mysql.exe '
            f'on Windows, e.g. C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin).'
        )


def _defaults_file(db_settings):
    """Writes a short-lived 0600 mysql options file so the password never
    appears in argv (visible via `ps aux`/Task Manager) or shell history."""
    fd = tempfile.NamedTemporaryFile(mode='w', suffix='.cnf', delete=False)
    fd.write('[client]\n')
    fd.write(f"user={db_settings['USER']}\n")
    fd.write(f"password={db_settings['PASSWORD']}\n")
    fd.write(f"host={db_settings.get('HOST') or 'localhost'}\n")
    fd.write(f"port={db_settings.get('PORT') or '3306'}\n")
    fd.close()
    try:
        Path(fd.name).chmod(0o600)
    except (OSError, NotImplementedError):
        pass  # chmod is a no-op on some Windows filesystems; not critical locally
    return fd.name


def _human_size(num_bytes):
    size = float(num_bytes)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024:
            return f'{int(size)} {unit}' if unit == 'B' else f'{size:.1f} {unit}'
        size /= 1024
    return f'{size:.1f} TB'


def create_backup():
    """Creates a timestamped .sql dump via mysqldump. --single-transaction
    keeps this non-blocking and consistent for InnoDB tables while the app
    keeps serving requests."""
    _require_binary('mysqldump')
    db_settings = get_db_settings()
    backup_dir = get_backup_dir()
    timestamp = timezone.localtime(timezone.now()).strftime('%Y%m%d_%H%M%S')
    filename = f'philhealth_backup_{timestamp}.sql'
    dest_path = backup_dir / filename

    cnf_path = _defaults_file(db_settings)
    try:
        with open(dest_path, 'wb') as out:
            result = subprocess.run(
                [
                    'mysqldump',
                    f'--defaults-extra-file={cnf_path}',
                    '--single-transaction',
                    '--routines',
                    '--triggers',
                    db_settings['NAME'],
                ],
                stdout=out,
                stderr=subprocess.PIPE,
            )
        if result.returncode != 0:
            dest_path.unlink(missing_ok=True)
            raise RuntimeError(result.stderr.decode(errors='replace')[:500])
    finally:
        Path(cnf_path).unlink(missing_ok=True)

    return {'filename': filename, 'size_bytes': dest_path.stat().st_size}


def list_backups():
    """Returns backup metadata, newest first."""
    backup_dir = get_backup_dir()
    rows = []
    for path in backup_dir.glob('philhealth_backup_*.sql'):
        if not BACKUP_FILENAME_RE.match(path.name):
            continue
        stat = path.stat()
        ts_str = path.stem.replace('philhealth_backup_', '')
        try:
            created = timezone.make_aware(datetime.datetime.strptime(ts_str, '%Y%m%d_%H%M%S'))
        except ValueError:
            created = timezone.make_aware(datetime.datetime.fromtimestamp(stat.st_mtime))
        rows.append({
            'filename': path.name,
            'size_bytes': stat.st_size,
            'size_display': _human_size(stat.st_size),
            'created_at': created,
            'created_display': timezone.localtime(created).strftime('%b %d, %Y · %I:%M %p'),
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


def restore_backup(uploaded_file):
    """Overwrites the live database with an uploaded .sql dump via the
    mysql client. Takes a safety backup of the current database first."""
    _require_binary('mysql')

    head = uploaded_file.read(4096)
    uploaded_file.seek(0)
    head_text = head.decode('utf-8', errors='ignore')
    if not any(marker in head_text for marker in ('CREATE TABLE', 'INSERT INTO', 'MySQL dump')):
        raise ValueError('The uploaded file does not look like a valid SQL dump.')

    safety = create_backup()

    db_settings = get_db_settings()
    cnf_path = _defaults_file(db_settings)

    with tempfile.NamedTemporaryFile(suffix='.sql', delete=False) as tmp:
        for chunk in uploaded_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        with open(tmp_path, 'rb') as sql_in:
            result = subprocess.run(
                ['mysql', f'--defaults-extra-file={cnf_path}', db_settings['NAME']],
                stdin=sql_in,
                stderr=subprocess.PIPE,
            )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.decode(errors='replace')[:500])
    finally:
        Path(cnf_path).unlink(missing_ok=True)
        Path(tmp_path).unlink(missing_ok=True)

    return safety