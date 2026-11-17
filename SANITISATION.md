# Sanitisation record

This repository is built from private test notes. Before publication, private values were removed or replaced. Every change is listed below: the file, the line in this repository, what changed and why. In the Was column the removed private value itself is shown as a placeholder in angle brackets. Scripts that changed no longer match the hash of the file that ran; TESTED_HASHES.json lists both hashes for every copied file.

## Placeholders you must set

| Variable | Used by | Replaces |
|---|---|---|
| `KAN_ROOT` | harness/KAN_BUILD_R4.py, harness/KAN_FIXTURE.py, harness/KAN_RUN_ENGINE.py | a private host folder |
| `KAN_HARNESS_DIR` | harness/KAN_RUN_ENGINE.py | a private host folder that held the harness scripts |
| `KAN_TEST_PASSWORD` | harness/KAN_CAPTURE.py, harness/setup/KAN_SEED_UI.py, harness/KAN_FIXTURE.py (passed into the browser container) | the synthetic test user's password |
| `KAN_DB_PASSWORD` | harness/KAN_BUILD_R4.py, harness/KAN_FIXTURE.py | the synthetic local database password |
| `KAN_AUTH_SECRET` | harness/KAN_BUILD_R4.py, harness/KAN_FIXTURE.py | the synthetic Better Auth secret |

Pick any values you like. All of them were synthetic, local-only values in the original run; none was a real credential. Use the same `KAN_DB_PASSWORD` and `KAN_AUTH_SECRET` for the build and the runs (whether a mismatch matters was not checked).

## Line-by-line changes

| File | Line(s) | Was | Now | Why |
|---|---|---|---|---|
| harness/KAN_CAPTURE.py | 2 | `import json,pathlib,sys,time,traceback` | `import json,os,pathlib,sys,time,traceback` | needed to read the test password from the environment |
| harness/KAN_CAPTURE.py | 65 | `'<synthetic password>'` | `os.environ['KAN_TEST_PASSWORD']` | synthetic test-user password replaced with an environment variable |
| harness/KAN_FIXTURE.py | 1 | `"""<host name>-only offline fixture controller; no Kan source mutations."""` | `"""Offline fixture controller; no Kan source mutations."""` | private host name removed from docstring |
| harness/KAN_FIXTURE.py | 2 | `import json, pathlib, shutil, subprocess, sys, time` | `import json, os, pathlib, shutil, subprocess, sys, time` | needed for environment variables below |
| harness/KAN_FIXTURE.py | 3 | `ROOT=pathlib.Path('<private host folder>')` | `ROOT=pathlib.Path(os.environ['KAN_ROOT'])` | private host path replaced with an environment variable |
| harness/KAN_FIXTURE.py | 7 | `assert subprocess.check_output(['hostname']).decode().strip()=='<host name>'` | `# Host-name gate removed for publication (see SANITISATION.md).` | private host-name check removed |
| harness/KAN_FIXTURE.py | 13 | `URL='postgresql://capture:<synthetic password>@127.0.0.1:5432/kan_capture'` | `URL='postgresql://capture:'+os.environ['KAN_DB_PASSWORD']+'@127.0.0.1:5432/kan_capture'` | synthetic database password replaced with an environment variable |
| harness/KAN_FIXTURE.py | 14 | `'BETTER_AUTH_SECRET':'<synthetic secret>'` | `'BETTER_AUTH_SECRET':os.environ['KAN_AUTH_SECRET']` | synthetic auth secret replaced with an environment variable |
| harness/KAN_FIXTURE.py | 40 | `'--label','<product name>.fixture=1'` | `'--label','rig.fixture=1'` | internal product name removed from a container label |
| harness/KAN_FIXTURE.py | 41 | `'--env','AGENT_BROWSER_NO_VERSION_CHECK=1','--mount'` | `'--env','AGENT_BROWSER_NO_VERSION_CHECK=1','--env','KAN_TEST_PASSWORD','--mount'` | passes the test password from the host environment into the browser container (docker run -e NAME takes the host value) |
| harness/KAN_FIXTURE.py | 44 | `'--env','POSTGRES_PASSWORD=<synthetic password>'` | `'--env','POSTGRES_PASSWORD='+os.environ['KAN_DB_PASSWORD']` | synthetic database password replaced with an environment variable |
| harness/KAN_RUN_ENGINE.py | 2 | `import importlib.util,json,pathlib,subprocess,sys,threading,time` | `import importlib.util,json,os,pathlib,subprocess,sys,threading,time` | needed for environment variables below |
| harness/KAN_RUN_ENGINE.py | 3 | `ROOT=pathlib.Path('<private host folder>');EDIT=pathlib.Path('<private host folder>')` | `ROOT=pathlib.Path(os.environ['KAN_ROOT']);EDIT=pathlib.Path(os.environ['KAN_HARNESS_DIR'])` | private host paths replaced with environment variables |
| harness/KAN_BUILD_R4.py | 1 | `"""Bounded <host name>-only Kan build following admission task event <internal event ID>."""` | `"""Bounded offline Kan build in containers; see README.md."""` | private host name and internal event ID removed from docstring |
| harness/KAN_BUILD_R4.py | 3 | `ROOT=pathlib.Path('<private host folder>')` | `ROOT=pathlib.Path(os.environ['KAN_ROOT'])` | private host path replaced with an environment variable |
| harness/KAN_BUILD_R4.py | 7 | `assert subprocess.check_output(['hostname']).decode().strip()=='<host name>'` | `# Host-name gate removed for publication (see SANITISATION.md).` | private host-name check removed |
| harness/KAN_BUILD_R4.py | 11 | `,'admission_event':'<internal event ID>'` | (removed) | internal event ID removed from the build receipt |
| harness/KAN_BUILD_R4.py | 31 | `'BETTER_AUTH_SECRET':'<synthetic secret>','POSTGRES_URL':'postgresql://capture:<synthetic password>@127.0.0.1:5432/kan_capture'` | `'BETTER_AUTH_SECRET':os.environ['KAN_AUTH_SECRET'],'POSTGRES_URL':'postgresql://capture:'+os.environ['KAN_DB_PASSWORD']+'@127.0.0.1:5432/kan_capture'` | synthetic auth secret and database password replaced with environment variables |
| harness/KAN_BUILD_R4.py | 39 | `'--label','<product name>.fixture=1'` | `'--label','rig.fixture=1'` | internal product name removed from a container label |
| harness/setup/KAN_SEED_UI.py | 1 | `import pathlib,sys,time` | `import os,pathlib,sys,time` | needed to read the test password |
| harness/setup/KAN_SEED_UI.py | 7 | `'<synthetic password>'` | `os.environ['KAN_TEST_PASSWORD']` | synthetic test-user password replaced with an environment variable |
| harness/rig/RUN.py | 82, 96, 123 | `<product name>PaintReady` | `rigPaintReady` | internal product name removed from a JavaScript helper name (renamed consistently in every file that uses it) (3 occurrences) |
| harness/rig/RUN.py | 89, 113 | `<product name>SiteProbe` | `rigSiteProbe` | internal product name removed from a JavaScript helper name (renamed consistently) (2 occurrences) |
| harness/rig/RUN.py | 254 | `<product name>TextReady` | `rigTextReady` | internal product name removed from a JavaScript helper name (renamed consistently) |
| harness/rig/RUN.py | 145 | `__<product name>Wpt` | `__rigWpt` | internal product name removed from a page global name (renamed consistently) |
| harness/rig/READY.js | 2 | `<product name>PaintReady` | `rigPaintReady` | internal product name removed from a JavaScript helper name (renamed consistently in every file that uses it) |
| harness/rig/SITE_PROBE.js | 2 | `<product name>SiteProbe` | `rigSiteProbe` | internal product name removed from a JavaScript helper name (renamed consistently) |
| harness/rig/SITE_TEXT.js | 2 | `<product name>TextReady` | `rigTextReady` | internal product name removed from a JavaScript helper name (renamed consistently) |
| harness/rig/ENGINE_BINARIES.json | 11 | `on <host name>;` | `on the test host;` | private host name removed from a provenance note |
| memory/rig/BENCHMARK.mjs | 59 | `current pins/<host name>/built-in CDP client` | `current pins/test host/built-in CDP client` | private host name removed from the result label the script writes |
| memory/rig/RUN.py | 70 | `<product name>PaintReady` | `rigPaintReady` | internal product name removed from a JavaScript helper name (renamed consistently in every file that uses it) |
| memory/rig/RUN.py | 83 | `__<product name>Wpt` | `__rigWpt` | internal product name removed from a page global name (renamed consistently) |
| memory/rig/READY.js | 2 | `<product name>PaintReady` | `rigPaintReady` | internal product name removed from a JavaScript helper name (renamed consistently in every file that uses it) |
| memory/rig/COLLECTOR.js | 4 | `__<product name>Wpt` | `__rigWpt` | internal product name removed from a page global name (renamed consistently) |
| memory/rig/ENGINE_BINARIES.json | 11 | `on <host name>;` | `on the test host;` | private host name removed from a provenance note |
| memory/rig/PREFLIGHT.py | 1 | `in the locked <host name> container` | `in the locked test container` | private host name removed from docstring |
| memory/rig/PREFLIGHT.py | 15, 23, 39 | `/__<product name>/` | `/__rig/` | internal product name removed from a local test-fixture URL path (renamed consistently in PREPARE.py, PREFLIGHT.py and SERVICE_HEALTH.py) (3 occurrences) |
| memory/rig/PREPARE.py | 1 | `"""<host name>-only offline preparation` | `"""Offline preparation` | private host name removed from docstring |
| memory/rig/PREPARE.py | 27 | `    if os.uname().nodename!='<host name>':raise RuntimeError('<host name> only')` | `    # Host-name gate removed for publication (see SANITISATION.md).` | private host-name check removed |
| memory/rig/PREPARE.py | 43 | `wpt/'__<product name>'` | `wpt/'__rig'` | fixture directory renamed to match the /__rig/ URL path |
| memory/rig/SERVICE_HEALTH.py | 16 | `key='<base64 of a product-name string>'` | `key='cmlnLWZpeHR1cmUta2V5IQ=='` | WebSocket test key was base64 of an internal product name; replaced with base64 of 'rig-fixture-key!' (any 16-byte key works) |
| memory/rig/SERVICE_HEALTH.py | 24 | `payload=b'<product name>-fixture';mask=b'<product name>'` | `payload=b'rig-fixture';mask=b'mask'` | internal product name removed from the WebSocket echo payload and 4-byte mask |
| memory/rig/SERVICE_HEALTH.py | 37 | `/__<product name>/` | `/__rig/` | internal product name removed from a local test-fixture URL path (renamed consistently in PREPARE.py, PREFLIGHT.py and SERVICE_HEALTH.py) |
| memory/rig/Dockerfile | 10 | `LABEL <product name>.fixture="1" <product name>.task="<internal task ID>-headless-rig"` | `LABEL rig.fixture="1"` | internal product name and internal task ID removed from image labels |
| memory/rig/RUN_HOST.sh | 3 | `test "$(hostname)" = <host name>` | `# Host-name gate removed for publication (see SANITISATION.md).` | private host-name check removed |
| memory/rig/RUN_HOST.sh | 12 | `test -f "$kit_dir/REVIEW_CLEARANCE.json"` | `# Internal review-clearance file check removed for publication (see SANITISATION.md).` | internal review receipt (contains an internal event ID) is not published |
| memory/rig/RUN_HOST.sh | 13 | `python3 "$kit_dir/VERIFY_CLEARANCE.py"` | `# Internal review-clearance verification removed for publication (see SANITISATION.md).` | internal review gate is not published; use TESTED_HASHES.json instead |
| memory/rig/RUN_HOST.sh | 18 | `tag="repo-demos-headless-rig:<internal task ID>-${engine}-${phase}"` | `tag="headless-rig:${engine}-${phase}"` | internal task ID removed from the image tag |
| memory/rig/RUN_HOST.sh | 24 | `name="headless-rig-<internal task ID>-${engine}-${phase}-$(date +%s)"` | `name="headless-rig-${engine}-${phase}-$(date +%s)"` | internal task ID removed from the container name |
| memory/rig/RUN_HOST.sh | 26 | `--label <product name>.fixture=1` | `--label rig.fixture=1` | internal product name removed from a container label |
| memory/rig/STAGE_SOURCE.py | 6 | `EVIDENCE = HERE.parents[1] / '<private workspace folder>'` | `EVIDENCE = HERE / 'staged'` | private workspace path replaced with the kit-local staged/ folder that RUN_HOST.sh reads |
| memory/rig/STAGE_DEPS.py | 4 | `DEST = HERE.parents[1] / '<private workspace folder>/dependencies'` | `DEST = HERE / 'staged/dependencies'` | private workspace path replaced with the kit-local staged/ folder that RUN_HOST.sh reads |
| memory/rig-r5-obscura/RUN.py | 71 | `<product name>PaintReady` | `rigPaintReady` | internal product name removed from a JavaScript helper name (renamed consistently in every file that uses it) |
| memory/rig-r5-obscura/RUN.py | 84 | `__<product name>Wpt` | `__rigWpt` | internal product name removed from a page global name (renamed consistently) |
| memory/rig-r5-obscura/RUN_HOST.sh | 3 | `test "$(hostname)" = <host name>` | `# Host-name gate removed for publication (see SANITISATION.md).` | private host-name check removed |
| memory/rig-r5-obscura/RUN_HOST.sh | 12 | `test -f "$kit_dir/REVIEW_CLEARANCE.json"` | `# Internal review-clearance file check removed for publication (see SANITISATION.md).` | internal review receipt (contains an internal event ID) is not published |
| memory/rig-r5-obscura/RUN_HOST.sh | 13 | `python3 "$kit_dir/VERIFY_CLEARANCE.py"` | `# Internal review-clearance verification removed for publication (see SANITISATION.md).` | internal review gate is not published; use TESTED_HASHES.json instead |
| memory/rig-r5-obscura/RUN_HOST.sh | 19 | `tag="repo-demos-headless-rig:<internal task ID>-${engine}-${phase}"` | `tag="headless-rig:${engine}-${phase}"` | internal task ID removed from the image tag |
| memory/rig-r5-obscura/RUN_HOST.sh | 25 | `name="headless-rig-<internal task ID>-${engine}-${phase}-$(date +%s)"` | `name="headless-rig-${engine}-${phase}-$(date +%s)"` | internal task ID removed from the container name |
| memory/rig-r5-obscura/RUN_HOST.sh | 27 | `--label <product name>.fixture=1` | `--label rig.fixture=1` | internal product name removed from a container label |
| engine-image/Dockerfile | 2 | `LABEL <product name>.fixture="1" <product name>.task="<internal task ID>-headless-smoke"` | `LABEL rig.fixture="1"` | internal product name and internal task ID removed from image labels |
| engine-image/PREPARE.py | 1 | `"""On <host name>, within heavy-job:` | `"""On the test host, within a job scratch directory:` | private host name removed from docstring |
| engine-image/PREPARE.py | 25 | `'User-Agent':'<product name>-approved-headless-smoke'` | `'User-Agent':'headless-smoke'` | internal product name removed from the download User-Agent |
| engine-image/ARTIFACTS.json | 46 | `"owner_approval": "<internal event ID>"` | `"owner_approval": "internal-approval-id-removed"` | internal event ID replaced with a placeholder (PREPARE_CHROME.py copies this field into its receipt) |
| engine-image/PREPARE_CHROME.py | 1 | `"""<host name>-only first admission:` | `"""First admission:` | private host name removed from docstring |
| engine-image/RUN_HOST.sh | 3 | `test "$(hostname)" = <host name>` | `# Host-name gate removed for publication (see SANITISATION.md).` | private host-name check removed |
| engine-image/RUN_HOST.sh | 11, 12 | `repo-demos-headless:<internal task ID>-r3` | `headless-engines:r3` | internal task ID removed from the image tag (2 occurrences) |
| engine-image/RUN_HOST.sh | 15 | `--name headless-<internal task ID>-r3 --label <product name>.fixture=1` | `--name headless-engines-r3 --label rig.fixture=1` | internal task ID and product name removed from container name and label |
| results/memory/FOUR_ENGINE_COMPARISON.json | 3 | `workload port on <host name>;` | `workload port on the test host;` | private host name removed |
| results/memory/chrome/BENCHMARK_SUMMARY.json | 113 | `current pins/<host name>/built-in CDP client` | `current pins/test host/built-in CDP client` | private host name removed |
| results/memory/lightpanda/BENCHMARK_SUMMARY.json | 113 | `current pins/<host name>/built-in CDP client` | `current pins/test host/built-in CDP client` | private host name removed |
| results/memory/obscura/BENCHMARK_SUMMARY.json | 113 | `current pins/<host name>/built-in CDP client` | `current pins/test host/built-in CDP client` | private host name removed |
| results/memory/moli/BENCHMARK_SUMMARY.json | 113 | `current pins/<host name>/built-in CDP client` | `current pins/test host/built-in CDP client` | private host name removed |

## Renamed files

| In this repository | Original name | Why |
|---|---|---|
| memory/rig/RUN_HOST.sh | run script whose name contained the private host name | host name removed |
| memory/rig-r5-obscura/RUN_HOST.sh | same, from the R5 kit | host name removed |
| engine-image/RUN_HOST.sh | same, from the engine-image kit (Chrome variant) | host name removed |
| results/memory/FOUR_ENGINE_COMPARISON.json | CAMPFIRE_FOUR_ENGINE_COMPARISON_R1.json | shorter name; content change listed above |

## Files left out on purpose

- Internal review notes, review bundles, review-clearance receipts and run lists from every kit (README.md, AUDIT_SUMMARY.md, R*_REPAIR.md, REVIEW_BUNDLE.md, REVIEW_CLEARANCE.json, RUN_LIST.json, VALIDATION.json, FILES.json). They contain names, internal IDs and host names. The clearance check that read them was removed from the run scripts (see the table above). Their file hashes are kept in TESTED_HASHES.json instead.
- Local self-test scripts of the rig (CHECK_*.py, VERIFY_CLEARANCE.py). They are not used by any test run.
- Host-side wrapper scripts that only called the harness with private paths (setup, Chrome-run and other-engines wrappers) and a transport script that reached the test host over SSH by internal IP address. README.md gives the equivalent commands.
- The rest of the R9 rig kit (site lists, WPT sample, site-gate and speed scripts). The board test imports only the modules in harness/rig/.
- adapter.mjs and action.mjs from the harness folder. They belong to the video-editing tool, not to agent-browser, and the board harness does not use them.
- Raw per-command logs (COMMANDS.jsonl) and container inspect receipts. They contain the synthetic password, host paths and container IDs. Sanitised summaries are in results/board/CONTAINERS_SUMMARY.json, results/board/BUILD_SUMMARY.json and results/memory/*/CONTAINER_SUMMARY.json.
- Server, web and database logs, the offline build log, and the theme-pass result folders.
- Kan source, the pnpm tarball, the cached font files and every engine binary or source archive. They are linked instead (licences and size).

## Kept on purpose

- `capture@example.test`, `Capture User`, `Capture workspace`: the synthetic test identity. `example.test` is a reserved test domain, not a real mailbox.
- `/home/pwuser`: the empty home folder inside the official Playwright container image (a tmpfs during runs), not a person's home folder.
- `127.0.0.1` and `1.1.1.1`: loopback, and the public DNS resolver the memory rig's container-local DNS forwards to.
- Environment variable names such as `POSTGRES_PASSWORD` and `BETTER_AUTH_SECRET` in the generated summaries. Values are not included.
- Docker image IDs and SHA256 values. They identify public images and files and contain no private data.

