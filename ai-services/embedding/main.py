"""HearSight 本地 embedding 微服务（OpenAI 兼容 /v1/embeddings）。

用 sentence-transformers 加载 BAAI/bge-m3（模型已在 dgx-spark 的 HF 缓存），
离线运行：HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1（远端直连 huggingface.co 不通）。

运行（dgx-spark）：
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ~/xinfer-env/bin/python main.py --port 8004
"""
from __future__ import annotations

import argparse
import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

app = FastAPI(title="HearSight Embedding Service")
_model: SentenceTransformer | None = None
MODEL_NAME = os.environ.get("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


class EmbeddingRequest(BaseModel):
    model: str = "bge-m3"
    input: str | list[str]


@app.get("/health")
def health():
    return {"status": "healthy", "model": MODEL_NAME, "loaded": _model is not None}


@app.post("/v1/embeddings")
def embeddings(req: EmbeddingRequest):
    texts = req.input if isinstance(req.input, list) else [req.input]
    vectors = get_model().encode(texts, normalize_embeddings=True)
    return {
        "object": "list",
        "data": [
            {"object": "embedding", "index": i, "embedding": v.tolist()}
            for i, v in enumerate(vectors)
        ],
        "model": req.model,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8004)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    get_model()  # 启动即加载，首个请求不卡
    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port)
