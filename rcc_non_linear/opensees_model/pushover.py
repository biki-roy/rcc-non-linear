from rcc_non_linear.opensees_model import model
from rcc_non_linear.opensees_model.gravity import run_gravity_analysis
from rcc_non_linear.opensees_model.circ_section import circular_column_bar_fibers, circular_column_core_fibers
from rcc_non_linear.opensees_model.rect_section import rect_col_core_fibers
import pandas as pd
import numpy as np
import os 
def pushover_analysis(model, maxU, dU, self_wt):
    import openseespy.opensees as ops
    ops.node(1, 0.0, 0.0)
    ops.node(2, 0.0, model.L)
    
    ops.fix(1, 1, 1, 1)

    ops.section('Elastic', model.elastic_sec_tag, model.Ec, model.Ag, model.Iz*model.k_eff)

    geom_transf_type = getattr(model, "geom_transf", "PDelta")
    ops.geomTransf(geom_transf_type, 1)

    # Modular Beam Integration setup
    integration_rule = getattr(model, "integration", None)
    if integration_rule is not None:
        integration_rule.build(1, model)
    else:
        ops.beamIntegration('HingeRadau', 1, model.fib_sec_tag, model.lp, model.fib_sec_tag, 0, model.elastic_sec_tag)

    element_type = getattr(model, "element_type", "forceBeamColumn")
    ops.element(element_type, 1, *[1, 2], 1, 1)
    
    col_wt = (0.15 / 12**3) * model.Ag * model.L if self_wt else 0.0
    total_wt = model.P_axial + col_wt/2
    print("Total axial load applied on column:", total_wt)
    run_gravity_analysis(total_wt, type="pushover")

    ops.timeSeries('Linear', 2)
    ops.pattern('Plain', 2, 2)
    ops.load(2, 1.0, 0.0, 0.0)

    ops.integrator('DisplacementControl', 2, 1, -dU)

    results = {
        'displacements': [0.0], 'forces': [0.0],
        'Eps_Conc': [0.0], 'Sig_Conc': [0.0],
        'Eps_Steel': [0.0], 'Sig_Steel': [0.0],
        'drift %': [0.0]
    }
    peak_force = 0.0
    curr_disp = 0.0
    yield_disp = None
    step = 0
    yield_step = None

    if model.section_type == "circular" and model.rupture_limit is not None:
        bar_fibers = circular_column_bar_fibers(model.bar_h, model.nBars)
        ruptured_bars = set()
        rupture_limit = max(1, int(np.floor(model.rupture_limit * model.nBars)))
        model.bar_fibers = bar_fibers
        model.ruptured_bars = ruptured_bars
        fiber_results = {}
        for _, row in bar_fibers.iterrows():
            bar_id = int(row['bar_id'])
            fiber_results[bar_id] = {
                "step": [],
                "eps_bar": [],
                "sig_bar": []
            }
        model.core_fibers = circular_column_core_fibers(model.core_h, model.nAng, model.nRad)

    if model.section_type == "rectangular":
        core_b, core_h = model.B - 2*model.cover - model.dh, model.H - 2*model.cover - model.dh
        model.core_fibers = rect_col_core_fibers(core_b, core_h, model.divB, model.divD)


    model.crushed_cores = set()

    while curr_disp < maxU:
        ok = ops.analyze(1)
        if ok != 0: break
        step += 1
        ops.reactions()

        curr_force = ops.nodeReaction(1, 1)
        curr_disp = -ops.nodeDisp(2, 1)

        # print(curr_disp, curr_force)
        if curr_force > peak_force: peak_force = curr_force
        cum_crushed_cores_area = 0
        if "core" in model.failure_criteria and model.core_crush_limit is not None:
            for _, row in model.core_fibers.iterrows():
                y, z = row['y'], row['z']
                fiber_id = row['fiber_id']
                sig_fiber, eps_fiber = ops.eleResponse(
                    1,
                    'section', model.fib_sec_tag,
                    'fiber', y, z, model.core_tag,
                    'stressStrain'
                )
                if eps_fiber < model.confined_props[-1]:
                    model.crushed_cores.add(int(fiber_id))
                    cum_crushed_cores_area += row['area_ratio']

        # --- Fiber Responses ---
        sig_c, eps_c = ops.eleResponse(1, 'section', model.fib_sec_tag, 'fiber', model.core_h, 0.0, model.core_tag, 'stressStrain')
        
        sig_s, eps_s  = ops.eleResponse(1, 'section', model.fib_sec_tag, 'fiber', -model.bar_h, 0.0, model.bar_tag, 'stressStrain')  #outermost fiber only

        if model.section_type == "circular" and model.rupture_limit is not None:
            for _, row in bar_fibers.iterrows():                
                y, z = row['y'], row['z']
                bar_id = row['bar_id']
                sig_bar, eps_bar = ops.eleResponse(
                    1,
                    'section', model.fib_sec_tag,
                    'fiber', y, z, model.bar_tag,
                    'stressStrain'
                )
                fiber_results[bar_id]["step"].append(step)
                fiber_results[bar_id]["eps_bar"].append(eps_bar)
                fiber_results[bar_id]["sig_bar"].append(sig_bar)

                if eps_bar > model.e_ult: ruptured_bars.add(int(bar_id))

        if (yield_disp is None) and (eps_s >= model.fy / model.Es):
            yield_disp = curr_disp
            yield_step = step
            print(f"✅ Yield point reached at displacement = {yield_disp:.6f}")

        results['displacements'].append(curr_disp)
        results['forces'].append(curr_force)
        results['Eps_Conc'].append(eps_c)
        results['Sig_Conc'].append(sig_c)
        results['Eps_Steel'].append(eps_s)
        results['Sig_Steel'].append(sig_s)
        results['drift %'].append(curr_disp*100/model.L)

        # Termination Checks
        if "strength" in model.failure_criteria and curr_force < 0.85 * peak_force:
            print(f"⚠️ Strength drop at displacement = {curr_disp:.6f}")
            model.failure_mode_pushover = "strength"
            break
        if "core" in model.failure_criteria and model.core_crush_limit is None and eps_c < model.confined_props[-1]:
            print(f"⚠️ Concrete crushed at displacement = {curr_disp:.6f}")
            model.failure_mode_pushover = "core"
            break
        if model.core_crush_limit is not None and "core" in model.failure_criteria and cum_crushed_cores_area >= model.core_crush_limit:
            print(f"⚠️ Concrete crushed at displacement = {curr_disp:.6f}")
            model.failure_mode_pushover = "core"
            print("cumulative crushed core area ratio:", cum_crushed_cores_area)
            break
        if "rebar" in model.failure_criteria and eps_s > model.e_ult and model.section_type == "rectangular":
            print(f"⚠️ Steel ruptured at displacement = {curr_disp:.6f}")
            model.failure_mode_pushover = "rebar"
            break
        if "rebar" in model.failure_criteria and eps_s > model.e_ult and model.section_type == "circular" and model.rupture_limit is None:
            print(f"⚠️ Steel ruptured at displacement = {curr_disp:.6f}")
            model.failure_mode_pushover = "rebar"
            break
        if "rebar" in model.failure_criteria and model.section_type == "circular" and model.rupture_limit is not None and len(ruptured_bars) >= rupture_limit:
            print(f"⚠️  {len(ruptured_bars)} / {model.nBars} bars having IDs {ruptured_bars} ruptured at displacement = {curr_disp:.6f}")
            model.failure_mode_pushover = "rebar"
            model.ruptured_bars = ruptured_bars
            break
    
    if model.section_type == "circular" and model.rupture_limit is not None:
        rows = []

        for bar_id, data in fiber_results.items():
            for i in range(len(data["step"])):
                rows.append({
                    "bar_id": bar_id,
                    "step": data["step"][i],
                    "eps_bar": data["eps_bar"][i],
                    "sig_bar": data["sig_bar"][i],
                })

        df_all = pd.DataFrame(rows)
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        output_path = os.path.join("results", "fiber_stress_strain_all.csv")
        df_all.to_csv(output_path, index=False)

    results_df = pd.DataFrame(results)
    return results_df, yield_step

