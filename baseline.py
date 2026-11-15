# -*- coding: utf-8 -*-
r"""Taban çizgisi: turkish-e5-large embedding + nearest centroid ve kNN ile intent doğruluğu (test, şablon-ayrık)."""
import json, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
MODEL = "ytu-ce-cosmos/turkish-e5-large"

def oku(ad):
    return [json.loads(l) for l in open(HERE / "data" / f"{ad}.jsonl", encoding="utf-8")]

def main():
    from sentence_transformers import SentenceTransformer
    tr, te = oku("train"), oku("test")
    m = SentenceTransformer(MODEL, device="cpu")
    t0 = time.time()
    Etr = m.encode(["query: " + k["text"] for k in tr], batch_size=32, normalize_embeddings=True, show_progress_bar=False)
    Ete = m.encode(["query: " + k["text"] for k in te], batch_size=32, normalize_embeddings=True, show_progress_bar=False)
    print(f"embedding {len(tr)+len(te)} metin {time.time()-t0:.0f} sn")
    ytr = np.array([k["intent"] for k in tr]); yte = np.array([k["intent"] for k in te])
    intents = sorted(set(ytr))
    C = np.stack([Etr[ytr == i].mean(0) for i in intents]); C /= np.linalg.norm(C, axis=1, keepdims=True)
    pred_c = np.array(intents)[(Ete @ C.T).argmax(1)]
    S = Ete @ Etr.T
    top = np.argsort(-S, axis=1)[:, :5]
    pred_k = np.array([max(set(ytr[r]), key=list(ytr[r]).count) for r in top])
    acc_c = (pred_c == yte).mean(); acc_k = (pred_k == yte).mean()
    print(f"nearest centroid: {acc_c:.3f}   kNN k=5: {acc_k:.3f}   (test n={len(te)})")
    # intent bazında
    print("intent bazında (centroid / kNN):")
    for i in intents:
        mk = yte == i
        print(f"  {i:16s} {(pred_c[mk]==i).mean():.2f} / {(pred_k[mk]==i).mean():.2f}  n={mk.sum()}")
    # en sık karışanlar
    from collections import Counter
    kar = Counter((a, b) for a, b in zip(yte, pred_k) if a != b)
    print("en sık karışan (gerçek → tahmin):", kar.most_common(6))
    (HERE / "data" / "baseline_sonuc.json").write_text(json.dumps({"model": MODEL, "nearest_centroid": round(float(acc_c), 4), "knn5": round(float(acc_k), 4), "test_n": len(te)}, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
