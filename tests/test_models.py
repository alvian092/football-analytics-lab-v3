import pytest
from backend.app.models import poisson_pmf, score_matrix, market_probabilities, predict

def test_poisson_distribution_is_valid():
    assert poisson_pmf(0, 1.0) == pytest.approx(0.367879, rel=1e-4)
    with pytest.raises(ValueError): poisson_pmf(-1, 1.0)

def test_score_matrix_normalizes():
    m = score_matrix(1.4, 1.1, rho=-0.08)
    assert m.sum() == pytest.approx(1.0)
    assert (m >= 0).all()

def test_markets_sum_and_are_bounded():
    p = predict(1.5, 1.0)["markets"]
    assert sum(p["1x2"].values()) == pytest.approx(1.0)
    assert p["totals"]["over"] + p["totals"]["under"] == pytest.approx(1.0)
    assert all(0 <= v <= 1 for v in p["1x2"].values())

def test_handicap_quarter_line():
    p = market_probabilities(score_matrix(1.4, 1.0), 2.5, -0.25)["asian_handicap_home"]
    assert sum(p[k] for k in ["win_full","win_half","push","lose_half","lose_full"]) == pytest.approx(1.0)
