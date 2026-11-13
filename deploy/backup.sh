#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
ROOT="${QUAKEMIND_DEPLOY_ROOT:-$HOME/opt/quakemind}"
exec 8>"$ROOT/backup.lock"
flock 8
active="$(cat "$ROOT/active-container")"
mkdir -p "$ROOT/backups"
name="quakemind-$(date -u +%Y%m%dT%H%M%SZ).sqlite3"
docker exec "$active" python -c "import os,sqlite3; s=sqlite3.connect(os.environ['QUAKEMIND_SQLITE']); d=sqlite3.connect('/tmp/quakemind-backup.sqlite3'); s.backup(d); d.close(); s.close()"
docker cp "$active:/tmp/quakemind-backup.sqlite3" "$ROOT/backups/$name"
docker exec "$active" rm /tmp/quakemind-backup.sqlite3
# Only our timestamped database snapshots; keep 14 days.
find "$ROOT/backups" -maxdepth 1 -name 'quakemind-*.sqlite3' -mtime +14 -delete
echo "Backup saved: $name"
