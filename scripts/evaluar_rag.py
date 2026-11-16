"""Evaluación por línea de comandos (PASO 5) -> results/evaluacion_rag.csv

Uso:  python scripts/evaluar_rag.py [--k 5] [--umbral 0.70] [--pausa 4]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.config import ROOT, load_settings  # noqa: E402
from rag.embeddings import OllamaEmbedder  # noqa: E402
from rag.evaluation import run_evaluation, summarize  # noqa: E402
from rag.llm import GeminiLLM, GenParams  # noqa: E402
from rag.pipeline import RAGPipeline  # noqa: E402
from rag.vectorstore import VectorStore  # noqa: E402


def main() -> None:
    S = load_settings()
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=S.top_k)
    ap.add_argument("--umbral", type=float, default=S.sim_threshold)
    ap.add_argument("--pausa", type=float, default=4.0, help="segundos entre llamadas a Gemini")
    args = ap.parse_args()

    pipe = RAGPipeline(VectorStore(S.database_url, S.table),
                       OllamaEmbedder(S.ollama_host, S.embed_model, S.embed_dim),
                       GeminiLLM(S.gemini_api_key, S.gemini_model))
    df = run_evaluation(pipe, GenParams(temperature=S.temperature), k=args.k, threshold=args.umbral,
                        pause_s=args.pausa, progress=lambda p, q: print(f"[{p:4.0%}] {q}"))
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    df.to_csv(out / "evaluacion_rag.csv", index=False)
    print("\n=== RESUMEN ===")
    for key, val in summarize(df, args.k).items():
        print(f"{key:28s}: {val:.3f}" if isinstance(val, float) else f"{key:28s}: {val}")
    print(f"\nResultados guardados en {out / 'evaluacion_rag.csv'}")


if __name__ == "__main__":
    main()
