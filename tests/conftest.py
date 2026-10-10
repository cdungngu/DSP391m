import pytest

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
