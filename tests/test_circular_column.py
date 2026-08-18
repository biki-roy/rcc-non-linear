import pytest
from rcc_non_linear import Model

@pytest.fixture
def circular_col_props():
    return {
        'fc': 6.1,
        'D': 48,
        'L': 324,
        'cover': 2,
        'nBars': 18,
        'db': 1.41,
        'fy': 75.2,
        'fu': 102.4,
        'Es': 29000,
        'Esh': 1247,
        'e_sh': 0.005,
        'e_ult': 0.122,
        'dh': 0.888,
        'sh': 6,
        'fyh': 54.8,
        'esm': 0.125,
        'P_axial': 570,
        'failure_criteria': ['rebar'],
        'nAng': 12,
        'nRad': 6,
        'nRad_cover': 3
    }


def test_circular_m_phi(circular_col_props):
    model = Model(circular_col_props)
    results_df, bilinear_df, yield_step = model.run_M_phi_analysis(maxK=0.002, dK=0.0001)

    assert len(results_df) > 5
    assert len(bilinear_df) == 4
    assert yield_step > 0
    assert model.k_eff > 0.0


def test_circular_pushover(circular_col_props):
    model = Model(circular_col_props)
    results_df, bilinear_df, yield_step = model.run_pushover_analysis()

    assert len(results_df) > 5
    assert yield_step is not None
    assert 'displacements' in results_df.columns
    assert 'forces' in results_df.columns
    assert results_df['forces'].max() > 0.0
    assert len(bilinear_df) == 4
