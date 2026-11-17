# Upstream source of the memory test

The "shop page" memory test is a port of the Campfire benchmark from the Lightpanda demo repository.

- Repository: https://github.com/lightpanda-io/demo
- Commit: `a87412aebbeec8b6422337fca178fbb7e3ffc883`
- Original client: [puppeteer/cdp.js](https://github.com/lightpanda-io/demo/blob/a87412aebbeec8b6422337fca178fbb7e3ffc883/puppeteer/cdp.js)
- Method notes: [BENCHMARKS.md](https://github.com/lightpanda-io/demo/blob/a87412aebbeec8b6422337fca178fbb7e3ffc883/BENCHMARKS.md), section "Campfire e-commerce Benchmark"
- Test page: [public/campfire-commerce/](https://github.com/lightpanda-io/demo/tree/a87412aebbeec8b6422337fca178fbb7e3ffc883/public/campfire-commerce). A fake product page that loads product details and reviews as JSON.
- Archive used: SHA256 `700157c2941dbb7e120c9ded6c0aff7179ada83b4353b1260c04a6eb21dc702c` (checked by `rig/PREPARE.py`). Where it was downloaded from is not checked.

## Licences

- The demo repository is under the Apache License 2.0. Its `cdp.js` carries the header "Copyright 2023-2024 Lightpanda (Selecy SAS), Licensed under the Apache License, Version 2.0". The licence text is in [../LICENSES/Apache-2.0.txt](../LICENSES/Apache-2.0.txt), read from the pinned archive.
- The Campfire page folder has its own MIT licence file in the upstream repository. This repository does not copy the page. `rig/PREPARE.py` unpacks it from the archive into the test image at build time.

## What `rig/BENCHMARK.mjs` changes

`rig/BENCHMARK.mjs` is a new file written for this test. It keeps the upstream workload:

- 100 runs, each in a new browser context and page;
- open `/campfire-commerce/` from a local server on `127.0.0.1:1234`;
- wait for the price and the reviews (100 ms limit each, as upstream);
- read the same fields: name, price, description, image, related products, reviews;
- check the same values: price 244.99, image `images/nomad_000.jpg`, 3 related products, 3 reviews;
- close the page and the context.

How it differs:

- Transport: Node's built-in WebSocket speaks CDP directly to the CDP address the browser exposes. Puppeteer is not installed.
- It uses raw CDP calls (`Target.createBrowserContext`, `Target.createTarget`, `Page.navigate`, `Runtime.evaluate`, ...) and waits for `Page.loadEventFired` itself before the two waits.
- It sets the viewport to 800x600 at device pixel ratio 1 explicitly.
- Each CDP call has a 15-second limit, and the load event a 15-second limit.
- It writes per-run results to `/out/BENCHMARK.jsonl` and a summary to `/out/BENCHMARK_SUMMARY.json`.

This is a workload port. It is not the vendor's machine, versions or Puppeteer timing, and it is not a reproduction of any published speed or memory claim.

`rig/BENCHMARK.mjs` is distributed under the Apache License 2.0 because it follows the upstream client closely. Everything else in `memory/` is under the MIT licence in [../LICENSE](../LICENSE), except the short pywebsocket3 code block quoted in `rig/TLS_COMPAT.py` (see LICENSE).

## Which kit ran which engine

- Chrome, Lightpanda, Moli: the files in `rig/` (kit revision R3), Docker bridge network.
- Obscura: `rig/` with the three files in `rig-r5-obscura/` copied over it (kit revision R5). R5 adds only a network check: Obscura runs with Docker network `none`, and gets `OBSCURA_ALLOW_PRIVATE_NETWORK=1` only after the container proves it has loopback only. `BENCHMARK.mjs` and the memory sampler `SPEED.py` are byte-identical in R3 and R5.
