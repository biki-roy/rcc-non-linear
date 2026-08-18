import pytest
from rcc_non_linear import Model

@pytest.fixture
def rect_col_props():
    return {
        'fc': 5.5,
        'B': 20,
        'H': 30,
        'L': 150,
        'cover': 1.5,
        'nBarsTop': 3,
        'dbTop': 1.0,
        'nBarsBot': 5,
        'dbBot': 1.27,
        'fy': 68,
        'fu': 95,
        'Es': 29000,
        'e_sh': 0.0115,
        'e_ult': 0.12,
        'dh': 0.375,
        'sh': 3,
        'fyh': 68,
        'esm': 0.12,
        'nx': 2,
        'ny': 2,
        'P_axial': 100,
        'divB': 8,
        'divD': 10
    }


def test_rect_m_phi(rect_col_props):
    model = Model(rect_col_props)
    results_df, bilinear_df, yield_step = model.run_M_phi_analysis(maxK=0.003, dK=0.0002)

    assert len(results_df) > 5
    assert len(bilinear_df) == 4
    assert yield_step > 0
    assert model.k_eff > 0.0


def test_rect_pushover(rect_col_props):
    model = Model(rect_col_props)
    results_df, bilinear_df, yield_step = model.run_pushover_analysis(maxU=2.0, dU=0.2)

    assert len(results_df) > 5
    assert results_df['forces'].max() > 0.0
    assert len(bilinear_df) == 4
