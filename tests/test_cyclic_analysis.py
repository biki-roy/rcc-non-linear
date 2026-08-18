import pytest
from rcc_non_linear import Model, extract_backbone_curve

@pytest.fixture
def circ_model():
    col_props = {
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
        'nAng': 12,
        'nRad': 6,
        'nRad_cover': 3
    }
    return Model(col_props)


def test_cyclic_analysis_and_backbone(circ_model):
    drift_peaks = [0.25, -0.25, 0.5, -0.5]
    cyclic_df = circ_model.run_cyclic_analysis(
        drift_peaks=drift_peaks,
        dU=0.2,
        self_wt=True,
        verbose=False
    )

    assert len(cyclic_df) > 10
    assert 'displacements' in cyclic_df.columns
    assert 'forces' in cyclic_df.columns
    assert 'drift %' in cyclic_df.columns

    # Verify positive and negative excursions reached
    assert cyclic_df['displacements'].max() > 0.0
    assert cyclic_df['displacements'].min() < 0.0
    assert cyclic_df['forces'].max() > 0.0
    assert cyclic_df['forces'].min() < 0.0

    # Test backbone extraction
    backbone_both = circ_model.get_cyclic_backbone(envelope='both')
    backbone_pos = circ_model.get_cyclic_backbone(envelope='positive')
    backbone_avg = circ_model.get_cyclic_backbone(envelope='average')

    assert len(backbone_both) >= 3
    assert len(backbone_pos) >= 2
    assert len(backbone_avg) >= 2
    assert backbone_pos['displacements'].iloc[0] == 0.0
    assert backbone_pos['forces'].iloc[0] == 0.0
