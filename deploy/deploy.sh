#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
mode="${1:-}"
requested="${2:-}"
if [[ ! "$requested" =~ ^[0-9a-f]{40}$ ]] || \
    { [[ "$mode" != --prepare ]] && [[ "$mode" != --apply ]]; }; then
    echo 'Usage: deploy.sh --prepare FULL_MAIN_SHA | --apply FULL_MAIN_SHA --approve SAME_SHA' >&2
    exit 64
fi
if [[ "$mode" == --prepare && "$#" != 2 ]] || \
    { [[ "$mode" == --apply ]] && { [[ "$#" != 4 ]] || [[ "$3" != --approve ]] || [[ "$4" != "$requested" ]]; }; }; then
    echo 'Applying requires explicit approval for the exact tested commit; push is not approval.' >&2
    exit 64
fi
ROOT="${QUAKEMIND_DEPLOY_ROOT:-$HOME/opt/quakemind}"
mkdir -p "$ROOT" "$ROOT/gateway" "$ROOT/backups"
exec 9>"$ROOT/deploy.lock"
flock -n 9 || exit 0
cd "$ROOT/repo"
git fetch --depth=1 origin main
revision="$(git rev-parse origin/main)"
[[ "$revision" == "$requested" ]] || { echo 'main changed; prepare and approve its exact new SHA first' >&2; exit 1; }
active="$(cat "$ROOT/active-container" 2>/dev/null || true)"

# Main currently uses QuakeMindBackend; the mobile integration branch uses
# backend. Never deploy uncommitted working-directory contents.
if git cat-file -e "$revision:backend/fastapi_app.py" 2>/dev/null; then
    source_dir=backend
elif git cat-file -e "$revision:QuakeMindBackend/fastapi_app.py" 2>/dev/null; then
    source_dir=QuakeMindBackend
else
    echo 'main does not contain a supported backend entry point' >&2
    exit 1
fi
context="$(mktemp -d "$ROOT/build.XXXXXXXX")"
prepared="$ROOT/prepared/$revision"
image="quakemind-api:$revision"
candidate="quakemind-${revision:0:12}-$(date +%s)"
promoted=0
cleanup() {
    code=$?
    if [[ "$promoted" == 0 ]] && docker container inspect "$candidate" >/dev/null 2>&1; then
        docker logs --tail 100 "$candidate" >&2 || true
        docker rm -f "$candidate" >/dev/null || true
    fi
    # mktemp's absolute path must be beneath our deployment root.
    case "$context" in "$ROOT"/build.*) rm -rf -- "$context" ;; esac
    exit "$code"
}
trap cleanup EXIT
if [[ "$mode" == --prepare ]]; then
rm -f "$prepared/ready"
mkdir "$context/source" "$context/legacy-tools"
git archive "$revision" "$source_dir" | tar -x -C "$context/source" --strip-components=1
if git cat-file -e "$revision:quakemind/tool/risk_bridge.py" 2>/dev/null; then
    git archive "$revision" quakemind/tool | tar -x -C "$context/legacy-tools" --strip-components=2
fi
cp "$ROOT/Dockerfile" "$ROOT/requirements.txt" "$context/"
cat > "$context/.dockerignore" <<'EOF'
source/benchmark
source/**/__pycache__
source/**/.venv
source/**/venv
source/veri/*.sqlite*
source/veri/*.db
EOF
docker build --build-arg "BACKEND_DIR=$source_dir" --label "org.opencontainers.image.revision=$revision" -t "$image" "$context"
# Existing endpoint tests run before touching the live container or data.
test_args=(tests /deployment_checks)
legacy_test="$(git rev-parse "$revision:$source_dir/tests/test_road_damage_api.py" 2>/dev/null || true)"
if [[ "$legacy_test" == 2015d83580fd769b211a58c9d6f97397f430c2a3 ]]; then
    # This exact upstream revision predates auth + SQLite on the heatmap.
    # All four cases run in checks/test_road_api.py with the current contract.
    # A changed upstream test file always runs normally.
    test_args+=(--ignore=tests/test_road_damage_api.py)
fi
docker run --rm --memory=3g --cpus=2 --env PYTHONPATH=/deployment_checks \
    --mount "type=bind,source=$ROOT/checks,target=/deployment_checks,readonly" \
    --entrypoint python "$image" -m pytest "${test_args[@]}" -o cache_dir=/tmp/pytest-cache -q
mkdir -p "$prepared"
docker image inspect --format '{{.Id}}' "$image" > "$prepared/image-id"
sha256sum "$ROOT/deploy.sh" "$ROOT/backup.sh" "$ROOT/Dockerfile" "$ROOT/requirements.txt" "$ROOT/prepare_basemap.py" "$ROOT"/checks/*.py > "$prepared/config.sha256"
printf '%s\n' "$revision" > "$prepared/ready"
echo "PREPARED_NOT_DEPLOYED: $revision"
echo 'Review the test results and request explicit user approval before --apply.'
exit 0
fi
[[ "$(cat "$prepared/ready" 2>/dev/null || true)" == "$revision" ]] || { echo 'No passing prepared release for this SHA' >&2; exit 1; }
sha256sum --check --status "$prepared/config.sha256" || { echo 'Deployment inputs changed; prepare again and renew approval' >&2; exit 1; }
image_id="$(cat "$prepared/image-id")"
[[ "$(docker image inspect --format '{{.Id}}' "$image")" == "$image_id" ]] || { echo 'Prepared image changed; refusing activation' >&2; exit 1; }
image="$image_id"
docker network inspect quakemind >/dev/null 2>&1 || docker network create quakemind
docker volume inspect quakemind-data >/dev/null 2>&1 || docker volume create quakemind-data
docker volume inspect quakemind-road-models >/dev/null 2>&1 || docker volume create quakemind-road-models
docker volume inspect quakemind-nlp-models >/dev/null 2>&1 || docker volume create quakemind-nlp-models
docker volume inspect quakemind-ner-models >/dev/null 2>&1 || docker volume create quakemind-ner-models
docker run --rm --user 0 --mount source=quakemind-ner-models,target=/models \
    --entrypoint chown "$image" 10001:10001 /models

backend_path="/app/$source_dir"
docker run --rm -i -e HF_HUB_DISABLE_PROGRESS_BARS=1 \
    --mount "source=quakemind-data,target=$backend_path/veri" \
    --entrypoint python "$image" - "$backend_path/veri" < "$ROOT/prepare_basemap.py"

# Download and verify the satellite checkpoint before the API's bounded
# startup window. A new installation can take longer than that window.
docker run --rm --memory=1g --cpus=1 \
    -e "HF_HOME=$backend_path/veri/huggingface" \
    --mount "source=quakemind-data,target=$backend_path/veri" \
    --mount "source=quakemind-road-models,target=$backend_path/apps/road_damage/models" \
    --entrypoint python "$image" -c \
    'from apps.road_damage.utils import model_kunyesi as m; k=m.kunye_oku(); p=m.agirligi_hazirla(k); assert m.sha256(p)==k["agirlik"]["sha256"], "Satellite model checksum mismatch"'

# The upstream NER loader writes apps/models/ner, separately from the
# classifier's apps/disaster_nlp/models. Persist and prepare both locations.
docker run --rm --memory=3g --cpus=2 \
    -e "HF_HOME=$backend_path/veri/huggingface" \
    --mount "source=quakemind-data,target=$backend_path/veri" \
    --mount "source=quakemind-nlp-models,target=$backend_path/apps/disaster_nlp/models" \
    --mount "source=quakemind-ner-models,target=$backend_path/apps/models" \
    --entrypoint python "$image" -c \
    'import sys; sys.path.insert(0,"apps/disaster_nlp"); from src.pipeline import DisasterPipeline; DisasterPipeline(); print("NLP models prepared")'

if [[ -n "$active" ]]; then
    "$ROOT/backup.sh"
fi
docker run -d --name "$candidate" --restart unless-stopped --init \
    --network quakemind --memory=4g --memory-swap=5g --cpus=2 \
    --cap-drop ALL --security-opt no-new-privileges:true \
    --env-file "$ROOT/backend.env" \
    -e "QUAKEMIND_SQLITE=$backend_path/veri/quakemind.sqlite3" \
    -e "HF_HOME=$backend_path/veri/huggingface" \
    --mount "source=quakemind-data,target=$backend_path/veri" \
    --mount "source=quakemind-road-models,target=$backend_path/apps/road_damage/models" \
    --mount "source=quakemind-nlp-models,target=$backend_path/apps/disaster_nlp/models" \
    --mount "source=quakemind-ner-models,target=$backend_path/apps/models" \
    --log-opt max-size=10m --log-opt max-file=3 "$image"
healthy=0
for ((attempt=0; attempt<80; attempt++)); do
    state="$(docker inspect --format '{{.State.Health.Status}}' "$candidate")"
    if [[ "$state" == healthy ]]; then healthy=1; break; fi
    if [[ "$(docker inspect --format '{{.State.Running}}' "$candidate")" != true ]]; then break; fi
    sleep 5
done
[[ "$healthy" == 1 ]] || { echo 'Candidate did not become healthy; existing backend retained' >&2; exit 1; }
docker exec "$candidate" python -c \
    'import json,urllib.request; s=json.load(urllib.request.urlopen("http://127.0.0.1:8000/api/status",timeout=5)); assert s["modules"]["risk"] and s["modules"]["camera"], s'
docker exec -i "$candidate" python - <<'PY'
import os
import secrets
import sqlite3
import uuid

import httpx
import kimlik
from depo import aktif_depo

email = f"risk-check-{uuid.uuid4().hex}@example.invalid"
user = aktif_depo().kullanici_olustur(
    email, "Deployment verification", kimlik.sifre_ozetle(secrets.token_urlsafe(24)), "afetzede",
)
try:
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=60) as client:
        headers = {"Authorization": f"Bearer {kimlik.erisim_jetonu_uret(user)}"}
        catalog = client.get("/api/altlik", headers=headers)
        catalog.raise_for_status()
        assert catalog.json()["bolgeler"], "Basemap catalog is empty"
        prediction = client.post(
            "/api/risk/predict", headers=headers,
            json={"city": "Amasya", "manualLatitude": 40.653, "manualLongitude": 35.833},
        )
        prediction.raise_for_status()
finally:
    with sqlite3.connect(os.environ["QUAKEMIND_SQLITE"]) as connection:
        connection.execute("DELETE FROM kullanicilar WHERE id=? AND eposta=?", (user["id"], email))
PY
cat > "$ROOT/gateway/default.conf.next" <<EOF
server {
    listen 8080;
    server_name quakemind-api.dehaozcan.online;
    client_max_body_size 25m;
    add_header X-QuakeMind-Revision "$revision" always;
    add_header X-QuakeMind-Instance "$candidate" always;
    if (\$http_x_forwarded_proto = http) {
        return 308 https://quakemind-api.dehaozcan.online\$request_uri;
    }
    include /etc/nginx/conf.d/console/*.inc;
    location / {
        proxy_pass http://$candidate:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_read_timeout 300s;
    }
}
EOF
if [[ -f "$ROOT/gateway/default.conf" ]]; then cp "$ROOT/gateway/default.conf" "$ROOT/gateway/default.conf.previous"; fi
mv "$ROOT/gateway/default.conf.next" "$ROOT/gateway/default.conf"
gateway_ok=0
if docker container inspect quakemind-gateway >/dev/null 2>&1; then
    if docker exec quakemind-gateway nginx -t && docker exec quakemind-gateway nginx -s reload; then gateway_ok=1; fi
else
    if docker run -d --name quakemind-gateway --restart unless-stopped --network quakemind \
        -p 127.0.0.1:8086:8080 --mount "type=bind,source=$ROOT/gateway,target=/etc/nginx/conf.d,readonly" \
        --log-opt max-size=10m --log-opt max-file=3 nginx:stable-alpine; then gateway_ok=1; fi
fi
if [[ "$gateway_ok" == 1 ]]; then
    for ((attempt=0; attempt<15; attempt++)); do
        if curl --fail --silent --max-time 5 -D "$ROOT/gateway-response.headers" http://127.0.0.1:8086/ > "$ROOT/gateway-response.json" \
            && grep -qi "X-QuakeMind-Revision: $revision" "$ROOT/gateway-response.headers" \
            && grep -qi "X-QuakeMind-Instance: $candidate" "$ROOT/gateway-response.headers"; then
            promoted=1; break
        fi
        sleep 2
    done
fi
if [[ "$promoted" != 1 ]]; then
    if [[ -f "$ROOT/gateway/default.conf.previous" ]]; then
        cp "$ROOT/gateway/default.conf.previous" "$ROOT/gateway/default.conf"
        docker exec quakemind-gateway nginx -s reload
    fi
    echo 'Gateway verification failed; previous route restored' >&2
    exit 1
fi
printf '%s\n' "$candidate" > "$ROOT/active-container.next"
mv "$ROOT/active-container.next" "$ROOT/active-container"
printf '%s\n' "$revision" > "$ROOT/deployed-commit.next"
mv "$ROOT/deployed-commit.next" "$ROOT/deployed-commit"
if [[ -n "$active" && "$active" != "$candidate" ]]; then docker stop --timeout 30 "$active"; fi
echo "Deployed main $revision as $candidate"
