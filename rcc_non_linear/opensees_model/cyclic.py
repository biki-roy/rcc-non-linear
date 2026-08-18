"""
Quasi-static Reversed Cyclic Pushover Analysis for OpenSees RC Column Model.
Supports user-defined drift ratio cycles or displacement peaks, multi-cycle repetitions,
and robust multi-algorithm adaptive convergence fallback during load reversals.
"""

import pandas as pd
import numpy as np
from rcc_non_linear.opensees_model.gravity import run_gravity_analysis
from rcc_non_linear.utils.helper import extract_backbone_curve


def _build_displacement_protocol(L, drift_peaks=None, disp_peaks=None, num_cycles_per_peak=1):
    """
    Builds the target displacement reversal peaks list [0.0, D1, D2, ..., 0.0].
    
    Parameters
    ----------
    L : float
        Column length / height (in).
    drift_peaks : list of float, optional
        List of drift peaks (as fractions e.g. [0.005, -0.005, 0.01, -0.01] or percentages if max > 0.2).
    disp_peaks : list of float, optional
        List of displacement peaks in inches (e.g. [1.5, -1.5, 3.0, -3.0]).
    num_cycles_per_peak : int
        Number of full cycle repetitions at each peak drift level.
    """
    if disp_peaks is not None:
        raw_peaks = list(disp_peaks)
    elif drift_peaks is not None:
        raw_peaks = []
        for d in drift_peaks:
            # If user provided drift in percent (e.g., 0.5, -0.5, 1.0, -1.0), convert to ratio
            drift_ratio = d / 100.0 if abs(d) > 0.2 else d
            raw_peaks.append(drift_ratio * L)
    else:
        # Default standard cyclic drift protocol: 0.25%, 0.5%, 1%, 1.5%, 2%, 3%, 4%, 5%
        standard_drifts = [0.0025, -0.0025, 0.005, -0.005, 0.01, -0.01, 0.015, -0.015,
                           0.02, -0.02, 0.03, -0.03, 0.04, -0.04, 0.05, -0.05]
        raw_peaks = [d * L for d in standard_drifts]

    # Build sequence with repetitions if specified
    peaks_sequence = [0.0]
    if num_cycles_per_peak > 1 and drift_peaks is not None:
        # Pair up (+, -) cycles if user provided symmetric peaks
        i = 0
        while i < len(raw_peaks):
            if i + 1 < len(raw_peaks) and raw_peaks[i] * raw_peaks[i+1] < 0:
                pos_p = raw_peaks[i]
                neg_p = raw_peaks[i+1]
                for _ in range(num_cycles_per_peak):
                    peaks_sequence.extend([pos_p, neg_p])
                i += 2
            else:
                for _ in range(num_cycles_per_peak):
                    peaks_sequence.append(raw_peaks[i])
                i += 1
    else:
        peaks_sequence.extend(raw_peaks)

    if peaks_sequence[-1] != 0.0:
        peaks_sequence.append(0.0)

    return peaks_sequence


def _adaptive_step(ops, step_size, tol=1e-5, max_iter=100):
    """
    Attempts to solve a single displacement step using multiple robust algorithms.
    """
    ops.integrator('DisplacementControl', 2, 1, step_size)
    ops.test('NormDispIncr', tol, max_iter, 0)
    
    # 1. Standard Newton-Raphson
    ops.algorithm('Newton')
    ok = ops.analyze(1)
    if ok == 0:
        return 0

    # 2. Newton with Line Search
    ops.algorithm('NewtonLineSearch', 0.75)
    ok = ops.analyze(1)
    if ok == 0:
        return 0

    # 3. Krylov-Newton
    ops.algorithm('KrylovNewton')
    ok = ops.analyze(1)
    if ok == 0:
        return 0

    # 4. Modified Newton with initial stiffness
    ops.algorithm('ModifiedNewton', '-initial')
    ok = ops.analyze(1)
    if ok == 0:
        return 0

    # 5. Broyden (Secant quasi-Newton)
    ops.algorithm('Broyden', 10)
    ok = ops.analyze(1)
    if ok == 0:
        return 0

    # 6. Sub-stepping fallback: divide into 4 smaller sub-increments
    sub_step = step_size / 4.0
    ops.integrator('DisplacementControl', 2, 1, sub_step)
    ops.algorithm('NewtonLineSearch', 0.8)
    sub_ok = 0
    for _ in range(4):
        sub_ok = ops.analyze(1)
        if sub_ok != 0:
            ops.algorithm('KrylovNewton')
            sub_ok = ops.analyze(1)
            if sub_ok != 0:
                break
                
    return sub_ok


def run_cyclic_analysis(
    model,
    drift_peaks=None,
    disp_peaks=None,
    num_cycles_per_peak=1,
    dU=0.05,
    self_wt=True,
    verbose=True,
):
    """
    Runs quasi-static reversed cyclic pushover analysis on the RC column model.

    Parameters
    ----------
    model : Model
        The RCC column Model instance.
    drift_peaks : list of float, optional
        List of drift peaks (as fractions e.g. [0.005, -0.005, 0.01, -0.01] or percentages e.g. [0.5, -0.5]).
    disp_peaks : list of float, optional
        Direct displacement peaks in inches (e.g. [1.5, -1.5, 3.0, -3.0]).
    num_cycles_per_peak : int, default=1
        Number of repetitions per peak level.
    dU : float, default=0.05
        Target displacement increment per sub-step (in).
    self_wt : bool, default=True
        Whether to include column self-weight in gravity loads.
    verbose : bool, default=True
        Whether to print cycle progress.

    Returns
    -------
    results_df : pandas.DataFrame
        DataFrame containing 'displacements', 'forces', 'drift_ratios', 'Eps_Conc', 'Sig_Conc', 'Eps_Steel', 'Sig_Steel'.
    """
    import openseespy.opensees as ops

    ops.node(1, 0.0, 0.0)
    ops.node(2, 0.0, model.L)
    ops.fix(1, 1, 1, 1)

    # 1. Setup elastic section, transformation, integration, and element
    ops.section('Elastic', model.elastic_sec_tag, model.Ec, model.Ag, model.Iz * model.k_eff)
    geom_transf_type = getattr(model, "geom_transf", "PDelta")
    ops.geomTransf(geom_transf_type, 1)

    integration_rule = getattr(model, "integration", None)
    if integration_rule is not None:
        integration_rule.build(1, model)
    else:
        ops.beamIntegration('HingeRadau', 1, model.fib_sec_tag, model.lp, model.fib_sec_tag, 0, model.elastic_sec_tag)

    element_type = getattr(model, "element_type", "forceBeamColumn")
    ops.element(element_type, 1, *[1, 2], 1, 1)

    # 2. Gravity Analysis
    col_wt = (0.15 / 12**3) * model.Ag * model.L if self_wt else 0.0
    total_wt = model.P_axial + col_wt / 2
    if verbose:
        print(f"Total axial load applied on column: {total_wt:.2f} kips")
    run_gravity_analysis(total_wt, type="pushover")

    # 3. Setup Pushover Analysis Pattern
    ops.timeSeries('Linear', 2)
    ops.pattern('Plain', 2, 2)
    ops.load(2, 1.0, 0.0, 0.0)

    # 4. Build Displacement Protocol
    peaks_sequence = _build_displacement_protocol(
        L=model.L,
        drift_peaks=drift_peaks,
        disp_peaks=disp_peaks,
        num_cycles_per_peak=num_cycles_per_peak
    )

    # Output storage
    history = {
        'displacements': [0.0],
        'forces': [0.0],
        'drift_ratios': [0.0],
        'Eps_Conc': [0.0],
        'Sig_Conc': [0.0],
        'Eps_Steel': [0.0],
        'Sig_Steel': [0.0],
    }

    current_disp = 0.0
    total_steps = 0

    if verbose:
        print(f"Starting cyclic analysis: {len(peaks_sequence)-1} reversal segments...")

    # 5. Execute Cyclic Loading Path
    for seg_idx in range(len(peaks_sequence) - 1):
        start_u = peaks_sequence[seg_idx]
        target_u = peaks_sequence[seg_idx + 1]
        delta_total = target_u - start_u
        
        if abs(delta_total) < 1e-9:
            continue

        n_sub_steps = max(1, int(np.ceil(abs(delta_total) / dU)))
        step_inc = delta_total / n_sub_steps

        if verbose:
            target_drift = (target_u / model.L) * 100.0
            print(f"  Segment {seg_idx + 1}/{len(peaks_sequence)-1}: Target Disp = {target_u:.2f} in ({target_drift:+.2f}% drift), Steps = {n_sub_steps}")

        for _ in range(n_sub_steps):
            ok = _adaptive_step(ops, step_inc)
            if ok != 0:
                print(f"⚠️ Warning: Convergence challenge at disp = {current_disp:.3f} in during segment {seg_idx + 1}")

            ops.reactions()
            current_disp = ops.nodeDisp(2, 1)
            lateral_force = ops.nodeReaction(1, 1)

            # Fiber responses at critical section (base node 1)
            try:
                sig_c, eps_c = ops.eleResponse(1, 'section', model.fib_sec_tag, 'fiber', model.core_h, 0.0, model.core_tag, 'stressStrain')
                sig_s, eps_s = ops.eleResponse(1, 'section', model.fib_sec_tag, 'fiber', -model.bar_h, 0.0, model.bar_tag, 'stressStrain')
            except Exception:
                sig_c, eps_c, sig_s, eps_s = 0.0, 0.0, 0.0, 0.0

            history['displacements'].append(current_disp)
            history['forces'].append(-lateral_force)
            history['drift_ratios'].append(current_disp / model.L)
            history['Eps_Conc'].append(eps_c)
            history['Sig_Conc'].append(sig_c)
            history['Eps_Steel'].append(eps_s)
            history['Sig_Steel'].append(sig_s)
            total_steps += 1

    results_df = pd.DataFrame(history)
    results_df["drift %"] = results_df["displacements"] * 100 / model.L
    if verbose:
        print(f"✅ Cyclic analysis completed! Total data points: {len(results_df)}")

    return results_df
