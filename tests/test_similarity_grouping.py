import hashlib
import re

import numpy as np
import pytest

from crest.devtools import notebook_code


@pytest.fixture(scope="module")
def mh():
    code = notebook_code()
    seed = int(re.search(r"^SEED = (\d+)", code, re.M).group(1))
    ns = {"np": np, "hashlib": hashlib, "SEED": seed}
    exec(code[code.index("MINHASH_PERM = 128"):code.index('all_ids = [r["transcript_id"] for r in records]')], ns)
    return ns


def test_signatures_are_pinned(mh):
    docs = [f"thank you for calling acme how can i help you today my order number is <num> and it has not arrived "
            f"{i % 7} yes".split() for i in range(50)]
    sig = np.stack([mh["minhash_signature"](mh["shingle_hashes"](d)) for d in docs])
    assert hashlib.sha256(mh["_PERM_A"].tobytes() + mh["_PERM_B"].tobytes()).hexdigest() == \
        "eaf8184a991794aa7a5bb506caf6a376295bbc90f29353914a527e5705d78515"
    assert hashlib.sha256(sig.tobytes()).hexdigest() == \
        "513f7c821de45e4d83f6f62cc7c324ccb007aec7c6fef0928ee319e53e58e89f"


def _partition(labels):
    groups = {}
    for i, lab in enumerate(labels):
        groups.setdefault(lab, set()).add(i)
    return {frozenset(g) for g in groups.values()}


def test_components_equal_checking_every_candidate(mh):
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    rng = np.random.default_rng(0)
    vocab = [f"w{i}" for i in range(2000)]
    base = [list(rng.choice(vocab, 200)) for _ in range(30)]
    docs = []
    for d in range(900):
        t = list(base[d % 30])
        for pos in rng.choice(200, rng.integers(0, 50), replace=False):
            t[pos] = str(rng.choice(vocab))
        docs.append(t)
    hashes = [mh["shingle_hashes"](d) for d in docs]
    sig = np.stack([mh["minhash_signature"](h) for h in hashes])
    g = mh["SimilarityGraph"](hashes, sig, 0.5)
    sets = [set(h.tolist()) for h in hashes]
    n = len(docs)
    for thr in (0.5, 0.7, 0.9):
        fast = g.components(thr)
        edges = [(a, b) for a, b in zip(g.i.tolist(), g.j.tolist()) if len(sets[a] & sets[b]) / len(sets[a] | sets[b]) >= thr]
        a, b = np.array(edges).T if edges else (np.zeros(0, int), np.zeros(0, int))
        naive = connected_components(coo_matrix((np.ones(len(a)), (a, b)), shape=(n, n)), directed=False)[1]
        assert _partition(fast) == _partition(naive), thr
    assert np.isfinite(g.jac).sum() < len(g.i)
