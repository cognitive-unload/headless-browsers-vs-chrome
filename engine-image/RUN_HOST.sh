#!/bin/bash
set -euo pipefail
# Host-name gate removed for publication (see SANITISATION.md).
test -n "${HEAVY_JOB_SCRATCH_DIR:-}"
kit_dir=$(cd "$(dirname "$0")" && pwd)
python3 "$kit_dir/PREPARE_CHROME.py"
python3 "$kit_dir/PREPARE.py"
job_scratch=$(cat "$kit_dir/LAST_SCRATCH.txt")
mkdir -p "$job_scratch/results"
chmod 0777 "$job_scratch/results"
docker build --pull=false --network=none --tag headless-engines:r3 "$job_scratch/context"
docker image inspect headless-engines:r3 --format '{{.Id}}' > "$job_scratch/IMAGE_ID.txt"
image_id=$(cat "$job_scratch/IMAGE_ID.txt")
# No Docker socket, real home, keys, host network, inbound ports or personal data.
docker run --name headless-engines-r3 --label rig.fixture=1 \
  --read-only --user 1000:1000 --cap-drop=ALL --security-opt no-new-privileges \
  --pids-limit=512 --cpus=2 --memory=4g --shm-size=512m \
  --tmpfs /tmp:rw,nosuid,nodev,size=512m,uid=1000,gid=1000 \
  --tmpfs /home/pwuser:rw,nosuid,nodev,size=256m,uid=1000,gid=1000 \
  --add-host telemetry.lightpanda.io:127.0.0.1 \
  --env LIGHTPANDA_DISABLE_TELEMETRY=1 --env AGENT_BROWSER_NO_VERSION_CHECK=1 \
  --mount "type=bind,source=$job_scratch/results,target=/out" \
  "$image_id"
printf '%s\n' "$job_scratch"
