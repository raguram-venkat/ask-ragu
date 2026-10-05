"""Local embeddings with fastembed (ONNX, no PyTorch) — ADR-0003.

Architecture: the .onnx model file is the same on x86 and arm64; only onnxruntime (the engine)
is per-architecture, and pip/uv picks its aarch64 wheel on ARM. To try arm64 on an x86 laptop,
`docker run --privileged --rm tonistiigi/binfmt --install arm64` registers QEMU with the kernel
(binfmt_misc): when an arm64 binary starts, the kernel hands it to QEMU, which translates each
ARM instruction to x86 on the fly. No VM, no SSH: `docker build/run --platform linux/arm64` then
works like any container. Correct but slow, so never benchmark under it. Gone after a reboot.

Sync and CPU-bound: from async code call these via `await asyncio.to_thread(...)`,
never directly in a route, or every request waits on the model.
"""

from functools import cache

from fastembed import TextEmbedding
from fastembed.common.model_description import ModelSource, PoolingType

from ask_ragu.settings import settings


@cache  # load once per process; first call downloads the model into the cache dir
def _model() -> TextEmbedding:
    if settings.embedding_model not in {m["model"] for m in TextEmbedding.list_supported_models()}:
        # Not in fastembed's built-in list (e.g. an int8 build): describe it so it can load.
        TextEmbedding.add_custom_model(
            model=settings.embedding_model,
            pooling=PoolingType[settings.embedding_pooling.upper()],
            normalization=True,
            sources=ModelSource(hf=settings.embedding_model),
            dim=settings.embedding_dim,
            model_file=settings.embedding_model_file,
        )
    model = TextEmbedding(settings.embedding_model, cache_dir=settings.embedding_cache_dir)
    dim = len(next(iter(model.embed(["dim check"]))))
    if dim != settings.embedding_dim:  # the chunks.embedding column is vector(EMBEDDING_DIM)
        raise RuntimeError(
            f"{settings.embedding_model} gives {dim}-d, expected {settings.embedding_dim}"
        )
    return model


def passage_text(heading_path: str, content: str) -> str:
    """What gets embedded: heading_path starts with the title, so the chunk carries its context."""
    return f"{heading_path}\n{content}"


def embed_passages(texts: list[str]) -> list[list[float]]:
    vectors = _model().passage_embed(texts, batch_size=settings.embedding_batch_size)
    return [v.tolist() for v in vectors]


def embed_query(text: str) -> list[float]:
    # fastembed doesn't add bge's query instruction itself; it's a .env value so it can be ablated.
    return next(iter(_model().query_embed(settings.embedding_query_prefix + text))).tolist()
