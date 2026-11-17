# Four headless browsers, one board app, one fixed script

Video: [VIDEO LINK, ADD BEFORE RELEASE]

This repository holds the scripts, exact versions, settings and results behind a YouTube Short. You do not need to watch the video to use it.

## The question

Lighter headless browsers say they are faster and smaller than Chrome. Can they do a real job in a real web app, driven the same way as Chrome? And how much memory do they use on a small page?

## What we tested

Two separate tests:

1. **Board test.** Each browser ran the same fixed 11-step script in [Kan](https://kan.bn), an open-source board app, driven by [agent-browser](https://github.com/vercel-labs/agent-browser) over the Chrome DevTools Protocol (CDP). Run on 15 November 2026.
2. **Memory test ("shop page").** Each browser opened a small local shop page 100 times while we sampled its memory. Run on 9 November 2026. It is a different job from the board test.

This was one run, with one pinned version of each browser. It is not a repeated measurement.

### Exact versions

| Part | Version | Pinned file (SHA256) | Source |
|---|---|---|---|
| Chrome | 157.0.8103.38, Chrome for Testing, linux64 | archive `8cdeb344e9b2cefe59f4aea8d1d93d5d93054c03cde217665c16fc1f62e72a66` (Google publishes MD5 and CRC32C, not SHA256; both matched, then this SHA256 was pinned) | [download](https://storage.googleapis.com/chrome-for-testing-public/157.0.8103.38/linux64/chrome-linux64.zip) |
| Obscura | v0.2.6, normal release (rendering on, not the stealth or no-render build) | archive `eed986e478c5ec5439f531f2d7fb6b0e36a356f1df7a6c44a8e8fd4f2486bd76` | [release](https://github.com/h4ckf0r0day/obscura/releases/tag/v0.2.6), source commit [8534b401](https://github.com/h4ckf0r0day/obscura/tree/8534b401898ed17b62f69bdc3d5eb186bffb0d60) |
| Moli | v1.1.22 | archive `7e10f9a5b62371da56203b21ac0172bbe3c3626de189fc3742b91b2e2b8cdd39` | [release](https://github.com/lexmount/moli/releases/tag/v1.1.22), source commit [2353bc83](https://github.com/lexmount/moli/tree/2353bc83123def8a2ff63791e11194a7f1f702e1) |
| Lightpanda | 1.0.3 | binary `53eb34da09159dcf8f04865dbfe3e63e9a652062684495aa7ced5ddd7c82e8b0` | [release](https://github.com/lightpanda-io/browser/releases/tag/1.0.3), source commit [b8e234a7](https://github.com/lightpanda-io/browser/tree/b8e234a77259283ff2653d5cc5900249d1d2cea9) |
| agent-browser (driver) | v0.41.2 | binary `c4351f3802ffa5254d8c69f20a52e2fcf56925c6016fcf4203db25a07d811379` | [release](https://github.com/vercel-labs/agent-browser/releases/tag/v0.41.2), source commit [d52a5e90](https://github.com/vercel-labs/agent-browser/tree/d52a5e90c372ec4710c69adc3837ac14bbd852aa) |
| Kan | commit `3a4dfcd6974b67a4636ee075d7d07149155898e2` (5 November 2026) | 785 tracked files, hashes in `harness/build-inputs/SOURCE_SHA256.json` | [kanbn/kan at the pin](https://github.com/kanbn/kan/tree/3a4dfcd6974b67a4636ee075d7d07149155898e2) |

Binary hashes inside the test image (after unpacking): Obscura `c1400eec0b1572ea9b583b1544feafb0b25cea4e155b353dbba9c144d94ae6e3`, obscura-worker `d1025e540736b494d5c3fefe5abc09f3a774c65d9be891d818b0eb374d34dd72`, Moli `48f14e3bc36a5f450836080cf802acb62a5814d9b5e2e3f4056b7c583fa1d2e0`, Chrome executable `41ea350a7f209da77c14d1df3924d71ac66988623e71d44459b49a3dceb1c14e`. Every run checked these before starting (`ENGINE_HASHES.json`, `ENGINE_BINARIES_RECEIPT.json` in `results/`).

Container images, by image ID:

| Image | ID | Note |
|---|---|---|
| Playwright base | `mcr.microsoft.com/playwright@sha256:9bd26ad900bb5e0f4dee75839e957a89ae89c2b7ab1e76050e559790e946b948` | base of the engine images |
| Node 24.15.0 (Debian 12) | `sha256:07da4b3bda51fd1973b20d19d7139b289e0e065e364990bb26a80bb1e46cf757` | official repo digest `sha256:f22d6a1f082c02f292e86929b5b0442ac2e5eaf438a5dea9b1566601c3e05940`; Kan build and web server |
| PostgreSQL 17.11 (Debian 13) | `sha256:7296f210ae81031ec955dbad9a67a84fe958572a2153b8d0826a647522904dc1` | official repo digest `sha256:67f41722b7a8cbdb868a44a4995c846eddfdc2973bccb291ce937dce88ad5675` |
| Board-test browser image | `sha256:d97a2c45d5d3a2e5ef3bedf8bee68fd53d018b62d152f0c67a51ac5e2046dc08` | built locally; see "How to reproduce" |
| Memory-test image (Chrome, Lightpanda, Moli) | `sha256:f90871d3287c819ab1d3c970d2e52cc8a330a59a2fd9cf46bb9b2b80d74d2b12` | built locally from `memory/rig/` |
| Memory-test image (Obscura) | `sha256:e207264482ee...` (full ID in `results/memory/obscura/CONTAINER_SUMMARY.json`) | built locally from `memory/rig/` plus `memory/rig-r5-obscura/` |

Locally built image IDs will differ on your machine.

## Board test results

The 11 steps, the same for every browser:

1. Password sign-in
2. Create a board called "Release planning"
3. Add a list "To do"
4. Add a list "Done"
5. Add card "Check mobile layout"
6. Add card "Record UI walkthrough"
7. Add card "Review browser results"
8. Drag "Check mobile layout" from To do to Done
9. Open the dragged card
10. Edit its title and description (the app saves automatically)
11. Close the card, resize to 360x720 and reload the board

| Browser | Steps passed | Stopped at | What happened |
|---|---|---|---|
| Chrome 157 | 11/11 | none | All steps passed. Three cards saved; "Check mobile layout" moved to Done. Title became "Check mobile layout — reviewed", description "Phone layout reviewed at 360px." Both saved. Board reloaded at 360 px. |
| Obscura 0.2.6 | 7/11 | step 8, drag card | Built the board, both lists and all three cards. The drag command answered `success: true` / `dragged: true`, but the card did not appear in Done within the 30-second page check. The database still had it in To do. The screenshots before and after the drag are byte-identical. |
| Moli 1.1.22 | 1/11 | step 2, create board | Signed in, reached the boards page, clicked New and filled the Name field. A visible, enabled "Create board" button never appeared within 30 seconds. The screenshot shows the boards page, not a board form. The database has zero boards. The cause is not established. |
| Lightpanda 1.0.3 | 2/11 | step 3, add first list | Signed in and created the board (confirmed in the database). On the board page the page text became empty and the screenshot blank. A visible, enabled "New list" button never appeared within 30 seconds. The database has zero lists. |

Exact stop messages. These come from our script's 30-second page check, not from the app:

Obscura:

```text
App observation deadline: document.querySelectorAll("[data-list-scroll-id]")[1]?.textContent.includes("Check mobile layout")
```

Moli:

```text
App observation deadline: (()=>{const e=[...document.querySelectorAll("button")].find(e=>e.textContent.trim()==="Create board" && e.getBoundingClientRect().width>0 && e.getBoundingClientRect().height>0 && !e.disabled);if(!e)return null;if(e.id)return "#"+CSS.escape(e.id);let p=e,s=[];while(p&&p.tagName!=="HTML"){let n=1,q=p;while(q=q.previousElementSibling)if(q.tagName===p.tagName)n++;s.unshift(p.tagName.toLowerCase()+":nth-of-type("+n+")");p=p.parentElement;}return s.join(" > ")})()
```

Lightpanda:

```text
App observation deadline: (()=>{const e=[...document.querySelectorAll("button")].find(e=>e.textContent.trim()==="New list" && e.getBoundingClientRect().width>0 && e.getBoundingClientRect().height>0 && !e.disabled);if(!e)return null;if(e.id)return "#"+CSS.escape(e.id);let p=e,s=[];while(p&&p.tagName!=="HTML"){let n=1,q=p;while(q=q.previousElementSibling)if(q.tagName===p.tagName)n++;s.unshift(p.tagName.toLowerCase()+":nth-of-type("+n+")");p=p.parentElement;}return s.join(" > ")})()
```

How the board test works:

- A fixed script, not an AI agent. Every change to the board went through agent-browser `fill`, `click`, `type` and `drag` commands. JavaScript only read the page. Read-only database queries only confirmed what was saved.
- Every browser started from the same saved state: one synthetic user and one empty workspace, zero boards, lists or cards.
- Chrome ran first and had to pass all 11 steps before the others ran, one at a time.
- Time limits: 30 s for each page check, 20 s for each saved-state check, 45 s for each agent-browser command.
- Desktop screenshots 1280x720, phone screenshots 360x720, both at device pixel ratio 1. The phone size is an emulated width, not a real phone.
- Before step 1 every browser got the same `set media dark` command. All four acknowledged it. Chrome, Obscura and Moli showed dark pages. Lightpanda returned a light, text-like page, then a blank one. Lightpanda's screenshots are not rendered website pixels like Chrome's; do not compare them as such.
- Moli runs its own server (`moli serve --host 127.0.0.1 --port 9222 --layout --resource`) and agent-browser connects to it with `--cdp`. agent-browser's output labels that connection "chrome". It is still Moli.
- Obscura gets `OBSCURA_ALLOW_PRIVATE_NETWORK=1` so it may open the app on `127.0.0.1`, inside a container with no network.

Results files: `results/board/RESULTS.json` (summary with the page and database state at each stop), `results/board/<browser>/STEPS.json` (every step), `results/board/CAPTURE_MANIFEST.json` and the 12 screenshots in `results/board/captures/` (three per browser, hashes in the manifest).

Earlier pass: a first four-browser pass put an extra theme-menu click inside step 1. Obscura failed that theme selector, Moli timed out on the user-menu button, and Lightpanda reached step 3. That click was not one of the 11 steps, so it was moved to the common `set media dark` setup and all four were run again. The tables above are from the second (core) pass. The first pass used a different `KAN_CAPTURE.py` (SHA256 `22d008155fc45c56916f583bc55e4f620b9734699674c26a8de38f7c94fd6b54`); its results are not in this repository.

## Memory test results

| Browser | Sampled peak memory (PSS) | In MiB | Memory samples | Samples with a missing process | 100-run loop | Median run |
|---|---:|---:|---:|---:|---:|---:|
| Chrome 157 | 559,499 KiB | 546.39 | 259 | 46 | 50.819 s | 501.878 ms |
| Obscura 0.2.6 | 58,640 KiB | 57.27 | 63 | 0 | 6.255 s | 61.935 ms |
| Moli 1.1.22 | 106,129 KiB | 103.64 | 131 | 0 | 13.567 s | 136.324 ms |
| Lightpanda 1.0.3 | 26,100 KiB | 25.49 | 17 | 0 | 1.488 s | 14.418 ms |

MiB = KiB / 1024. The video rounds these to about 550, 57, 104 and 25 MiB.

Method:

- The page is the Campfire demo shop page from the Lightpanda demo repository, served from inside the container on `127.0.0.1:1234`. See `memory/UPSTREAM.md`.
- One browser per container, one at a time. 100 runs, each in a fresh browser context: open the page, wait for price and reviews, read the product fields, check them, close. 800x600 at device pixel ratio 1. All 400 runs passed the same checks.
- `memory/rig/BENCHMARK.mjs` drives the browser over CDP, using the CDP address that agent-browser reports (`agent-browser get cdp-url`).
- `memory/rig/SPEED.py` (class `Memory`) samples memory about every 100 ms. Each sample adds up the proportional set size (PSS, from `/proc/<pid>/smaps_rollup`) of the browser's processes and all their child processes. agent-browser itself and the local test servers are not counted. The result is the highest sample.
- Sampling starts with a fresh browser session on `about:blank`, after the kit's start-up checks, and stops when `BENCHMARK.mjs` exits.
- Timing covers CDP calls, context setup, page load, reading and cleanup. It does not include browser start-up or the image build.

Limits:

- One run per browser. No spread or repeat runs were measured.
- It is a sampled peak, not a full count of every allocation. Short runs give few samples: Lightpanda has only 17.
- 46 of Chrome's samples could not read one or more of its processes at that moment (processes come and go). So the table does not give an exact memory ratio between browsers.
- This is the memory of the small shop-page job. It is not the memory of the board test.
- Network: Chrome, Lightpanda and Moli ran with Docker's normal bridge network and a small DNS server inside the container (test names resolve locally, the Lightpanda telemetry name is blocked, other names go to 1.1.1.1). The shop page itself is local. Obscura ran with Docker network `none`.

Results files: `results/memory/FOUR_ENGINE_COMPARISON.json`, and per browser `BENCHMARK_SUMMARY.json` (all 100 run times), `MEMORY.jsonl` (every sample), `BENCHMARK_MEMORY.jsonl` (the peak), `VERIFIED_SUMMARY.json`, `ENGINE_BINARIES_RECEIPT.json` and `CONTAINER_SUMMARY.json`.

## What we did not test

- Other versions of any browser, Kan or agent-browser.
- Repeat runs, or the spread between runs.
- Memory or speed during the board test.
- Any other app, or public websites.
- An AI model choosing the actions. The script is fixed.
- Obscura's stealth or no-render builds.
- Real phones. 360 px is an emulated width.
- Screen recording. Only step screenshots were saved.
- Any claim from a vendor's own benchmark (for example a "9x faster" or "16x lighter" figure). The memory test is a port of one vendor workload, not a reproduction of a published result.
- Why Obscura's drag did not land, why Moli's button did not appear, or why Lightpanda's board page went blank. We report what happened, not the cause.

## How to reproduce

Everything ran on one Linux x86_64 host with Docker, inside containers. Nothing was installed on the host. Steps marked **not checked** are things the original notes do not confirm. None of the scripts changed for publication (see `SANITISATION.md`) has been run after the change.

You need: a Linux x86_64 host, Docker, Python 3 and `openssl` on the host, and network access for the download steps. Host Python version: not checked.

### 1. Engine images (`engine-image/`)

`engine-image/RUN_HOST.sh` downloads the five release files listed in `engine-image/ARTIFACTS.json`, checks each SHA256 (and, for Chrome, Google's MD5 and CRC32C first), builds an image on the Playwright base and runs a short smoke check (`SMOKE.py`, which opens example.com, a Wikipedia page and github.com).

```sh
export HEAVY_JOB_SCRATCH_DIR=/path/to/a/new/empty/folder
bash engine-image/RUN_HOST.sh
```

- The Playwright base image must already be on the host by the digest in `engine-image/Dockerfile` (the build uses `--pull=false`). How the original host got it: **not checked**.
- The original setup built two images from this kit: one with agent-browser, Lightpanda, Obscura and Moli (`sha256:94b391782aa042272956ee8d4c6ccbdb75bd00d36648d97e08145be1b19b1739`), and one with agent-browser and Chrome (`sha256:7e44291716e341b3c0426e6d740a581e073fe0076d177a0a2b155f9fd9a3f3ca`). With the final `ARTIFACTS.json`, one run puts all five files into one image. Using that single image in place of both: **not checked**.

### 2. Memory test (`memory/`)

1. Put the two source archives in `memory/rig/staged/source/`:
   - `WPT.tar.gz`: [web-platform-tests](https://github.com/web-platform-tests/wpt) at commit `b62c4db0c515e8aa6f104f589c19bd2cb9b3424d`, SHA256 `814a76896b0339dd8cad43319082e5dbf29430c80f6be02b80433dacd234c9f4`. The kit's start-up checks use its test server.
   - `DEMO.tar.gz`: [lightpanda-io/demo](https://github.com/lightpanda-io/demo) at commit `a87412aebbeec8b6422337fca178fbb7e3ffc883`, SHA256 `700157c2941dbb7e120c9ded6c0aff7179ada83b4353b1260c04a6eb21dc702c`.
   - `PREPARE.py` refuses any other bytes. Where the original archives were downloaded from, and whether a fresh download gives the same bytes: **not checked**.
2. Put the eight pinned Python packages (see `memory/rig/requirements.lock`) in `memory/rig/staged/dependencies/`. `python3 memory/rig/STAGE_DEPS.py` downloads them from PyPI and checks PyPI's SHA256. It also rewrites `DEPENDENCIES.lock.json` and `requirements.lock` (new age and advisory fields); the package SHA256 values must stay the same.
3. Put your engine image IDs in the two `FROM` lines of `memory/rig/Dockerfile` and the two `docker image inspect` lines of `memory/rig/RUN_HOST.sh`. The tested IDs are left in place as the record.
4. Run one browser per new scratch folder. The kit's own notes say it was launched with `DOCKER_BUILDKIT=0` so the build accepts a local image ID in `FROM` (no per-run receipt of this setting exists: **not checked**):

```sh
export HEAVY_JOB_SCRATCH_DIR=/path/to/a/new/empty/folder
DOCKER_BUILDKIT=0 bash memory/rig/RUN_HOST.sh chrome benchmark
```

   Repeat with `lightpanda` and `moli`, each with a new scratch folder. For Obscura, copy `memory/rig/` to a new folder, copy the three files from `memory/rig-r5-obscura/` over it, and run that folder's `RUN_HOST.sh` with `obscura benchmark`.
5. Results appear in `$HEAVY_JOB_SCRATCH_DIR/results/`: `BENCHMARK_SUMMARY.json`, `MEMORY.jsonl`, `BENCHMARK_MEMORY.jsonl`.

Container limits for the memory runs (from `RUN_HOST.sh`): 2 CPUs, 4 GiB memory, 512 processes, 512 MiB shared memory, read-only root, user 1000, all capabilities dropped, no new privileges, empty tmpfs home (`/home/pwuser`) and `/tmp`, no published ports, `LIGHTPANDA_DISABLE_TELEMETRY=1`, `AGENT_BROWSER_NO_VERSION_CHECK=1`, telemetry host name mapped to `127.0.0.1`.

### 3. Board test (`harness/`)

The five tested scripts are `KAN_BUILD_R4.py`, `KAN_FIXTURE.py`, `KAN_RUN_ENGINE.py`, `KAN_CAPTURE.py` and `KAN_SESSION.py`. They import the agent-browser adapter (`RUN.py` and helpers) from `/opt/rig` inside the browser image. Those modules are in `harness/rig/`.

**a. Browser image.** The tested image (`sha256:d97a2c45...`) was built with the same Dockerfile and build script as `memory/rig/`, from a later revision (R9) of that kit. This repository includes only the R9 files the board test uses (`harness/rig/`). One way: copy `memory/rig/` to a new folder, copy `harness/rig/*` over it, and build it as in step 2. `RUN_HOST.sh` prints the scratch folder; the image ID is in `IMAGE_ID.txt` there. Whether this rebuilds an equivalent image: **not checked**. Then put your image ID in `BROWSER=` at the top of `harness/KAN_FIXTURE.py`.

**b. Settings.** Choose your own values:

```sh
export KAN_ROOT=/path/to/a/new/empty/folder
export KAN_HARNESS_DIR=/absolute/path/to/this/repo/harness
export KAN_TEST_PASSWORD='choose-a-password'
export KAN_DB_PASSWORD='choose-another'
export KAN_AUTH_SECRET='choose-a-long-random-string'
```

**c. Build inputs in `$KAN_ROOT`:**

- `KAN_SOURCE.tar`: the tracked files of [kanbn/kan](https://github.com/kanbn/kan/tree/3a4dfcd6974b67a4636ee075d7d07149155898e2) at commit `3a4dfcd6974b67a4636ee075d7d07149155898e2`, with no top-level folder. The build checks every file against `SOURCE_SHA256.json`. How the original tar was made: **not checked**.
- `SOURCE_SHA256.json`: copy from `harness/build-inputs/`.
- `PNPM.tgz`: pnpm 9.14.2 from `https://registry.npmjs.org/pnpm/-/pnpm-9.14.2.tgz`. The build checks SHA256 `06e65a4965baff6d6097f9c8f75c35f6d420974dbc03d775009056a69edfd271`.
- `font-input/`: copy `harness/build-inputs/PREPARE_FONT_INPUT.py` into `$KAN_ROOT` and run it there. It caches the real Plus Jakarta Sans files from Google Fonts so the build needs no network. Compare with `harness/build-inputs/FONT_RECEIPT.json`; whether Google serves the same bytes today: **not checked**.
- The Node and PostgreSQL images must be on the host by the image IDs at the top of `KAN_BUILD_R4.py` and `KAN_FIXTURE.py`. Whether pulling the official digests gives these exact image IDs: **not checked**.

**d. Build Kan:**

```sh
python3 harness/KAN_BUILD_R4.py R4
```

It runs two containers: `pnpm fetch` from the npm registry (bridge network), then an offline install and build (network `none`), both with 2 CPUs and 8 GiB, read-only root, user 1000, lifecycle scripts off, Next.js and Turbo telemetry off. The only change to Kan is one build setting added to `apps/web/next.config.js`: a webpack rule equal to Kan's own Turbopack SVG rule (exact text in `results/board/BUILD_SETTINGS_DIFF.txt`). Every other tracked file and the lockfile must still match their hashes. The script calls `chown`, so it needs a user allowed to do that and to use Docker; which user ran it originally: **not checked**.

**e. Baseline (one synthetic user, one empty workspace):**

1. `mkdir "$KAN_ROOT/kit"` and copy `harness/KAN_CAPTURE.py` and `harness/KAN_SESSION.py` into it. It is mounted read-only at `/opt/kan-capture` in the browser container. Which other files were in the original `kit` folder: **not checked**.
2. `python3 harness/KAN_FIXTURE.py up setup` starts PostgreSQL, applies Kan's database migrations and starts Kan.
3. Create the user (name `Capture User`, email `capture@example.test`, password `$KAN_TEST_PASSWORD`) and a workspace named `Capture workspace` through Kan's normal sign-up page in Chrome. The original sent agent-browser commands into the setup browser container one at a time, in this form:

   ```sh
   docker exec kan-fixture-setup-browser python3 /opt/kan-capture/KAN_SESSION.py chrome '<JSON list of agent-browser arguments>'
   ```

   `harness/setup/KAN_SEED_UI.py` holds a sign-up and workspace sequence found next to the harness. It starts with the sign-up page already open. The exact sequence and sign-up URL used: **not checked**.
4. `python3 harness/KAN_FIXTURE.py baseline setup` checks there is exactly one user, one workspace and nothing else, and saves `BASELINE.sql`. Compare with `results/board/BASELINE_STATE.json` (the user ID will differ).
5. `python3 harness/KAN_FIXTURE.py down setup`.

**f. Run the four browsers, Chrome first:**

```sh
python3 harness/KAN_RUN_ENGINE.py chrome
python3 harness/KAN_RUN_ENGINE.py obscura
python3 harness/KAN_RUN_ENGINE.py moli
python3 harness/KAN_RUN_ENGINE.py lightpanda
```

Each run starts fresh containers from `BASELINE.sql`, runs `KAN_CAPTURE.py` inside the browser container, answers its read-only database questions, saves logs and stops the containers. The other three refuse to run unless Chrome passed 11/11. Results appear in `$KAN_ROOT/fixture-<browser>/out/` (`RESULT.json`, `STEPS.json`, screenshots).

Container limits for the board test (from `KAN_FIXTURE.py`; recorded values in `results/board/CONTAINERS_SUMMARY.json`):

- No network: the browser container uses Docker network `none`; the Kan and database containers join that same network namespace. No bridge, no gateway, no published ports.
- Empty homes: tmpfs `/home/pwuser` and `/tmp` in the browser container; `HOME=/tmp/home` on tmpfs for Kan; no host files except the output folder, the read-only harness folder and the read-only Kan build.
- 2 CPUs and 4 GiB in total: browser 1.25 CPU / 2.5 GiB (1024 processes, 512 MiB shared memory), Kan 0.5 CPU / 1 GiB (256 processes), database 0.25 CPU / 512 MiB (128 processes).
- Read-only root, non-root users (1000, database 999), all capabilities dropped, no new privileges.
- Telemetry off: `LIGHTPANDA_DISABLE_TELEMETRY=1` and the Lightpanda telemetry host name mapped to `127.0.0.1`; `AGENT_BROWSER_NO_VERSION_CHECK=1`; `NEXT_TELEMETRY_DISABLED=1`; `TURBO_TELEMETRY_DISABLED=1`.
- No email, upload/S3, analytics or outside sign-in settings; password sign-in only (`NEXT_PUBLIC_ALLOW_CREDENTIALS=true`, `NEXT_PUBLIC_DISABLE_EMAIL=true`).

### Checking files

`TESTED_HASHES.json` lists every file copied from the test material, with the SHA256 of the file that ran and of the file in this repository. Changed files say "changed from tested hash ...". `SANITISATION.md` lists every change.

## Credits and licences

- [Kan](https://github.com/kanbn/kan): AGPL-3.0. Not included; tested at commit [3a4dfcd6](https://github.com/kanbn/kan/tree/3a4dfcd6974b67a4636ee075d7d07149155898e2).
- [agent-browser](https://github.com/vercel-labs/agent-browser) (Vercel Labs): Apache-2.0.
- [Lightpanda](https://github.com/lightpanda-io/browser): AGPL-3.0.
- [Obscura](https://github.com/h4ckf0r0day/obscura): Apache-2.0.
- [Moli](https://github.com/lexmount/moli): Apache-2.0.
- [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/) (Google). Its licence terms were not reviewed for this repository.
- [Lightpanda demo](https://github.com/lightpanda-io/demo) (Campfire workload and page): Apache-2.0; the page folder has its own MIT licence. See `memory/UPSTREAM.md`.
- [web-platform-tests](https://github.com/web-platform-tests/wpt): BSD 3-Clause.
- Python packages used by the memory kit's local test server: listed with versions and hashes in `memory/rig/DEPENDENCIES.lock.json`. pywebsocket3: BSD 3-Clause (see `LICENSES/`).
- Plus Jakarta Sans font, fetched from Google Fonts at build time. Not included.

Licences above were read from each repository's GitHub metadata or licence file on 9 to 15 November 2026. Binaries and source of all of these are linked, not included.

Our own files are under the MIT licence. `LICENSE` lists which files are ours and the two exceptions.
