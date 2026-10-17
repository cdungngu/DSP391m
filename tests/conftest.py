import numpy as np
import pandas as pd
import pytest

from dsp391m import etl, splits

COMBO = """STITCH 1,STITCH 2,Polypharmacy Side Effect,Side Effect Name
CID000000003,CID000000001,C0000002,nausea
CID000000001,CID000000003,C0000002,nausea
CID000000001,CID000000002,C0000001,anaemia
CID000000002,CID000000003,C0000001,anaemia
CID000000002,CID000000003,C0000002,nausea
"""
TARGETS = """STITCH,Gene
CID000000001,10
CID000000001,20
CID000000004,20
"""
PPI = """Gene 1,Gene 2
20,10
10,20
10,30
30,30
"""


@pytest.fixture
def raw_dir(tmp_path):
    d = tmp_path / "raw"
    d.mkdir()
    (d / "bio-decagon-combo.csv").write_text(COMBO)
    (d / "bio-decagon-targets.csv").write_text(TARGETS)
    (d / "bio-decagon-ppi.csv").write_text(PPI)
    return d


@pytest.fixture
def snap(tmp_path):
    """Snapshot tổng hợp: 40 thuốc, 200 cặp, 4 nhãn (nhãn thứ 4 hiếm, nằm ngoài vocab)."""
    rng = np.random.default_rng(1)
    drugs = [f"CID{i:09d}" for i in range(1, 41)]
    all_pairs = [(a, b) for i, a in enumerate(drugs) for b in drugs[i + 1:]]
    chosen = rng.choice(len(all_pairs), 200, replace=False)
    rows = []
    for k in chosen:
        a, b = all_pairs[k]
        for e in rng.choice(3, rng.integers(1, 4), replace=False):
            rows.append((a, b, f"C000000{e}", f"effect {e}"))
    rows.append((drugs[0], drugs[1], "C0000009", "rare"))
    raw = tmp_path / "raw"
    raw.mkdir()
    pd.DataFrame(rows, columns=["STITCH 1", "STITCH 2", "Polypharmacy Side Effect", "Side Effect Name"]) \
        .to_csv(raw / "bio-decagon-combo.csv", index=False)
    pd.DataFrame({"STITCH": drugs[:5], "Gene": range(5)}).to_csv(raw / "bio-decagon-targets.csv", index=False)
    pd.DataFrame({"Gene 1": [0, 1], "Gene 2": [1, 2]}).to_csv(raw / "bio-decagon-ppi.csv", index=False)
    out = tmp_path / "snap"
    etl.run(raw, out)
    splits.run(out, min_rows=20)
    return out
