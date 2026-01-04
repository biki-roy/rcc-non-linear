from rcc_non_linear.opensees_model.gravity import run_gravity_analysis
import pandas as pd
def moment_curvature_analysis(model, maxK, dK):
    import openseespy.opensees as ops
    ops.node(1, 0.0, 0.0)
    ops.node(2, 0.0, 0.0)
    
    ops.fix(1, 1, 1, 1)
    ops.fix(2, 0, 1, 0)
    # ops.fix(2, 1, 0, 0)

    ops.element('zeroLengthSection', 1, 1, 2, model.fib_sec_tag)

    run_gravity_analysis(model.P_axial)

    # Apply moment through node 2 rotation
    ops.timeSeries('Linear', 2)
    ops.pattern('Plain', 2, 2)
    ops.load(2, 0.0, 0.0, 1.0)
    ops.integrator('DisplacementControl', 2, 3, dK)

    results = {
        'curvatures': [0.0], 'moments': [0.0],
        'Eps_Conc': [0.0], 'Sig_Conc': [0.0],
        'Eps_Steel': [0.0], 'Sig_Steel': [0.0]
    }
    peak_moment = 0.0
    curr_K = 0.0
    yield_curv = None
    step = 0
    while curr_K < maxK:
        ok = ops.analyze(1)
        if ok != 0: break
        step += 1
        ops.reactions()
        curr_moment = -ops.nodeReaction(1, 3)
        curr_K = ops.nodeDisp(2,3)
        if curr_moment > peak_moment: peak_moment = curr_moment
        
        # --- Fiber Responses ---
        # Concrete Core (Material 1) at bottom extreme fiber
        sig_c, eps_c = ops.eleResponse(1, 'section', 'fiber', model.core_h, 0.0, model.core_tag, 'stressStrain')

        # Steel (Material 3) at top extreme fiber
        sig_s, eps_s  = ops.eleResponse(1, 'section', 'fiber', -model.bar_h, 0.0, model.bar_tag, 'stressStrain')

        if (yield_curv is None) and (eps_s >= model.fy / model.Es):
            yield_curv = curr_K
            yield_step = step
            print(f"✅ Yield point reached at curvature = {yield_curv:.6f}")

        results['curvatures'].append(curr_K)
        results['moments'].append(curr_moment)
        results['Eps_Conc'].append(eps_c)
        results['Sig_Conc'].append(sig_c)
        results['Eps_Steel'].append(eps_s)
        results['Sig_Steel'].append(sig_s)

        # Termination Checks
        if curr_moment < 0.85 * peak_moment:
            print(f"⚠️ Strength drop at curvature = {curr_K:.6f}")
            break
        if eps_c < model.confined_props[-1]:
            print(f"⚠️ Concrete crushed at curvature = {curr_K:.6f}")
            break
        if eps_s > model.e_ult:
            print(f"⚠️ Steel ruptured at curvature = {curr_K:.6f}")
            break
        
    results_df = pd.DataFrame(results)
    return results_df, yield_step
