# Task 5 — Local embeddings on ARM

Status: todo
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

- 

Decisions made here:

- 

Gotchas:

- 
