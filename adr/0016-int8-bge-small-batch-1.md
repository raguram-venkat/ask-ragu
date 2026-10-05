# ADR-0016: int8 bge-small-en-v1.5, embedded one chunk at a time

Status: accepted
Date: 2026-10-05
Sprint: sprint-2 (task_5)

## Context

ADR-0003 picked fastembed + bge-small-en-v1.5. fastembed's built-in build of that model turned out to be fp16 (66 MB), not int8, and the default batch of 64 pads every chunk to the longest one in the batch. On the laptop that meant 3–5 chunks/s and a 1.2–1.5 GB peak, which is too much RAM for a 12 GB box that will also run Postgres and a local LLM.

## Decision

Load `Xenova/bge-small-en-v1.5` `onnx/model_quantized.onnx` (int8, 34 MB) through fastembed's `add_custom_model`, with `EMBEDDING_BATCH_SIZE=1`. All of it is `.env` config (`EMBEDDING_MODEL`, `EMBEDDING_MODEL_FILE`, `EMBEDDING_POOLING`, `EMBEDDING_BATCH_SIZE`).

Measured on 256 real chunks (laptop, x86, 8 cores):

| Variant | Batch | Peak RSS | Chunks/s | Cosine vs fp32 (mean / min) |
|---|---|---|---|---|
| fp32 (official) | 64 | 1,540 MB | 3.6 | 1 |
| fp16 (fastembed built-in) | 64 | 1,258 MB | 3.3 | 1.0000 / 1.0000 |
| int8 | 64 | 1,416 MB | 5.5 | 0.9966 / 0.9905 |
| **int8** | **1** | **205 MB** | **24.7** | same |
| int8 | 8 | 323 MB | 10.4 | same |

## Alternatives considered

- fastembed's built-in fp16 build — no code needed, but fp16 has weak CPU kernels on x86, and it's twice the size for the same vectors.
- Official fp32 — the reference quality, but 4× the size and the slowest.
- Larger batches — more RAM and slower here, because padding to the longest chunk wastes most of the compute.

## Consequences

- An ONNX file is architecture-neutral; only onnxruntime is per-architecture, and it ships aarch64 wheels. int8 (MatMulInteger) has fast kernels on both x86 and ARM.
- int8 vectors differ slightly from fp32 (cosine ≥ 0.99). The Sprint 4 eval is the real quality check.
- The model comes from a community repo (Xenova, the transformers.js ONNX builds), not BAAI's; pinned by repo + file in `.env`.
- A full vault index (~2k chunks) takes ~80 s on the laptop; the A1 figure is still to be measured.
