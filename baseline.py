# -*- coding: utf-8 -*-
r"""Baseline: frozen multilingual embeddings + nearest centroid (intent accuracy on template-held-out test).
Runs monolingual (tr->tr, en->en) and cross-lingual (train on one language, test on the other).
Usage: python baseline.py [model]   (default intfloat/multilingual-e5-small)
"""
import json, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
MODEL = sys.argv[1] if len(sys.argv) > 1 else "intfloat/multilingual-e5-small"


def load(lang, split):
    return [json.loads(l) for l in open(HERE / "data" / lang / f"{split}.jsonl", encoding="utf-8")]


def main():
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(MODEL, device="cpu")
    emb, lab = {}, {}
    t0 = time.time()
    for lang in ("tr", "en"):
        for split in ("train", "test"):
            rows = load(lang, split)
            emb[lang, split] = m.encode(["query: " + r["text"] for r in rows], batch_size=64, normalize_embeddings=True, show_progress_bar=False)
            lab[lang, split] = np.array([r["intent"] for r in rows])
    print(f"embedded in {time.time()-t0:.0f}s with {MODEL}")
    res = {}
    for tr_lang in ("tr", "en"):
        Xtr, ytr = emb[tr_lang, "train"], lab[tr_lang, "train"]
        intents = sorted(set(ytr))
        C = np.stack([Xtr[ytr == i].mean(0) for i in intents]); C /= np.linalg.norm(C, axis=1, keepdims=True)
        for te_lang in ("tr", "en"):
            Xte, yte = emb[te_lang, "test"], lab[te_lang, "test"]
            pred = np.array(intents)[(Xte @ C.T).argmax(1)]
            acc = float((pred == yte).mean())
            res[f"{tr_lang}->{te_lang}"] = round(acc, 4)
            print(f"train {tr_lang} -> test {te_lang}: {acc:.3f}  (n={len(yte)})")
    (HERE / "data" / "baseline_results.json").write_text(json.dumps({"model": MODEL, "method": "nearest centroid", "accuracy": res}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
