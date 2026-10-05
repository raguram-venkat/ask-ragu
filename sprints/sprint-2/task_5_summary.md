# Task 5 — Local embeddings on ARM

Status: done (VM throughput to add once the A1 exists, D-008)
Est: 60m
Spec: SPEC.md §8 · ADR-0003

What: fastembed with BAAI/bge-small-en-v1.5 (384-d, ONNX) embedding chunks in batches off the event loop.

Approach: Load the model once at startup; batches run in a worker thread; record model + dim in index_state; benchmark chunks/sec on the VM.

Read first:

- fastembed README
- bge-small-en-v1.5 model card (query vs passage usage)

Watch out for:

- Confirm onnxruntime installs on aarch64 in your image before committing (fallback: sentence-transformers on CPU, heavier). No A1 yet (D-008): build and run the image with `--platform linux/arm64` under QEMU emulation on the laptop to catch arm64 install problems now. It's slow, so don't benchmark under emulation.
- Model downloads on first use: bake into the image or cache in a volume, or every restart re-downloads.
- CPU-bound work inside an async route blocks every request — thread pool only.
- bge expects a query instruction prefix on the query side; check whether fastembed's query embedding applies it.

Done when: the arm64 image passes an emulated smoke test; laptop throughput recorded; VM throughput added once the A1 exists.

---

Filled in while working

Files touched:

- `src/ask_ragu/index/embed.py` — `embed_passages`, `embed_query`, `passage_text`; model loaded once per process (`functools.cache`)
- `tests/test_embed.py` — real model: 384-d, normalized, related > unrelated
- `src/ask_ragu/settings.py`, `.env.example` — `EMBEDDING_*`
- `compose.yml` — `models` volume at `/app/models` (EMBEDDING_CACHE_DIR), so the model downloads once
- `.gitignore` — `models/`
- `adr/0016-int8-bge-small-batch-1.md`, `INDEX.md`

Decisions made here:

- int8 `Xenova/bge-small-en-v1.5` with batch size 1 → ADR-0016 (benchmark table there).
- Query prefix: fastembed does **not** add bge's query instruction (its `query_embed` just calls `embed`); it's `EMBEDDING_QUERY_PREFIX` in `.env` so Sprint 4 can ablate it.
- What gets embedded: `heading_path + "\n" + content` (heading_path starts with the title).
- Model cache in a named volume rather than baked into the image: simpler, and the model name lives in `.env`, which a build doesn't see.
- Embedding functions are sync; async callers wrap them in `asyncio.to_thread` (Tasks 6/7).
- No startup warm-up yet: nothing in the app embeds until Task 7.
- arm64 smoke test (2026-10-05, QEMU on the laptop): image built for `linux/arm64` in 2 min (226 MB), onnxruntime 1.30.0 installed from its aarch64 wheel; inside the container `platform.machine()` = `aarch64`, 384-d vectors, related 0.831 vs unrelated 0.475. How to rerun: register QEMU (command below), then `DOCKER_DEFAULT_PLATFORM=linux/arm64 docker compose -p ask-ragu-arm64 build app` and `... run --rm --no-deps app python -c "..."`; clean up with `docker compose -p ask-ragu-arm64 down -v --rmi local`. A separate project name keeps the real stack and its volumes untouched.
- Laptop throughput: 24.7 chunks/s at batch 1 (int8, 8 cores); full vault ~80 s. VM throughput: TODO when the A1 exists.

Gotchas:

- fastembed's "BAAI/bge-small-en-v1.5" is an fp16 build (66 MB, no int8 ops); "-Q" in its repo name doesn't mean int8.
- Batch 64 pads every chunk to the longest in the batch: ~1.3 GB peak and 5× slower than batch 1.
- arm64 testing without ARM hardware: QEMU user-mode emulation via `binfmt_misc`, not a VM. `docker run --privileged --rm tonistiigi/binfmt --install arm64` registers QEMU with the laptop's kernel; from then on, when an arm64 binary starts (e.g. inside a `--platform linux/arm64` container), the kernel hands it to QEMU, which translates each ARM instruction to x86 as it runs. Docker pulls the arm64 variant of the base image from the registry as usual, and the container is used like any other (`docker build/run/exec`), with no separate machine, IP or SSH. Correct but slow (no benchmarks under it); the registration is gone after a reboot. The native test is the A1 itself (`ssh ragu-vm`).
- Under QEMU, onnxruntime logs "Unknown CPU vendor": it can't identify the emulated CPU. Harmless.
- Vectors come back normalized, so cosine = dot product.
- fastembed's tokenizer truncates at 512 tokens, so it can't be used to check for over-long chunks; use `tokenizers.Tokenizer.from_file(...)` with `no_truncation()`.
- Real token counts (heading path + content, 1,964 chunks): median 155, p95 352, max 695; median 4.12 chars/token (Task 1's ~4 holds), but code-heavy chunks go down to 1.7. **8 chunks (0.4%) exceed 512 tokens** and are truncated for the vector only; full-text search still sees the whole chunk. → BACKLOG.
