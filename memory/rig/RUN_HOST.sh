#!/bin/bash
set -euo pipefail
# Host-name gate removed for publication (see SANITISATION.md).
test -n "${HEAVY_JOB_SCRATCH_DIR:-}"
engine=${1:?engine required}
phase=${2:?phase required}
case "$engine" in chrome|lightpanda|obscura|moli) ;; *) exit 2 ;; esac
case "$phase" in preflight|wpt|sites|speed|benchmark) ;; *) exit 2 ;; esac
kit_dir=$(cd "$(dirname "$0")" && pwd)
scratch="$HEAVY_JOB_SCRATCH_DIR"
mkdir -p "$scratch"
# Internal review-clearance file check removed for publication (see SANITISATION.md).
# Internal review-clearance verification removed for publication (see SANITISATION.md).
context="$scratch/context"
python3 "$kit_dir/PREPARE.py" --source "$kit_dir/staged/source" --deps "$kit_dir/staged/dependencies" --output "$context"
docker image inspect sha256:7e44291716e341b3c0426e6d740a581e073fe0076d177a0a2b155f9fd9a3f3ca > "$scratch/BASE_IMAGE.json"
docker image inspect sha256:94b391782aa042272956ee8d4c6ccbdb75bd00d36648d97e08145be1b19b1739 > "$scratch/THREE_ENGINE_BASE_IMAGE.json"
tag="headless-rig:${engine}-${phase}"
docker build --pull=false --network=none --tag "$tag" "$context"
image_id=$(docker image inspect "$tag" --format '{{.Id}}')
printf '%s\n' "$image_id" > "$scratch/IMAGE_ID.txt"
mkdir "$scratch/results"
chmod 0777 "$scratch/results"
name="headless-rig-${engine}-${phase}-$(date +%s)"
trap 'docker stop --time 10 "$name" >/dev/null 2>&1 || true' EXIT INT TERM
docker run --name "$name" --label rig.fixture=1 --read-only --user 1000:1000 \
  --cap-drop=ALL --security-opt no-new-privileges --pids-limit=512 --cpus=2 --memory=4g --shm-size=512m \
  --tmpfs /tmp:rw,nosuid,nodev,size=1g,uid=1000,gid=1000 \
  --tmpfs /home/pwuser:rw,nosuid,nodev,size=256m,uid=1000,gid=1000 \
  --dns 127.0.0.1 --sysctl net.ipv4.ip_unprivileged_port_start=0 \
  --add-host telemetry.lightpanda.io:127.0.0.1 \
  --env LIGHTPANDA_DISABLE_TELEMETRY=1 --env AGENT_BROWSER_NO_VERSION_CHECK=1 \
  --mount "type=bind,source=$scratch/results,target=/out" \
  "$image_id" --engine "$engine" --phase "$phase"
docker inspect "$name" > "$scratch/CONTAINER_RECEIPT.json"
printf '%s\n' "$scratch"
