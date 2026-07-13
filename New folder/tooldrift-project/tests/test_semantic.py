from tooldrift.semantic import TfidfSimilarity, SequenceMatcherSimilarity


def test_identical_strings_have_similarity_one():
    backend = TfidfSimilarity()
    assert backend.similarity("read a file", "read a file") == pytest_approx(1.0)


def pytest_approx(x, tol=1e-6):
    class _Approx:
        def __eq__(self, other):
            return abs(other - x) < tol
    return _Approx()


def test_unrelated_strings_have_low_similarity():
    backend = TfidfSimilarity()
    sim = backend.similarity(
        "Read the contents of a local file on disk.",
        "Synchronize a note to the user's account by transmitting it to backup-sync.example.com.",
    )
    assert sim < 0.55


def test_fallback_backend_works_without_sklearn():
    backend = SequenceMatcherSimilarity()
    sim = backend.similarity("hello world", "hello world")
    assert sim == 1.0
