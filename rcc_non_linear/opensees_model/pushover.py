from rcc_non_linear.opensees_model.gravity import run_gravity_analysis
import pandas as pd
def pushover_analysis(model, maxU, dU):
    import openseespy.opensees as ops
    ops.node(1, 0.0, 0.0)
    ops.node(2, 0.0, model.L)
    
    ops.fix(1, 1, 1, 1)

    ops.section('Elastic', model.elastic_sec_tag, model.Ec, model.Ag, model.Iz*0.4)

    ops.geomTransf('PDelta', 1)

    ops.beamIntegration('HingeRadau', 1, model.fib_sec_tag, model.lp, model.fib_sec_tag, 0, model.elastic_sec_tag)

    ops.element('forceBeamColumn', 1, *[1, 2], 1, 1)
    
    run_gravity_analysis(model.P_axial, type="pushover")

    # Apply moment through node 2 rotation
    ops.timeSeries('Linear', 2)
    ops.pattern('Plain', 2, 2)
    ops.load(2, 1.0, 0.0, 0.0)
    if model.section_type == "circular":
        ops.integrator('DisplacementControl', 2, 1, dU)
    else:
        ops.integrator('DisplacementControl', 2, 1, -dU)

    results = {
        'displacements': [0.0], 'forces': [0.0],
        'Eps_Conc': [0.0], 'Sig_Conc': [0.0],
        'Eps_Steel': [0.0], 'Sig_Steel': [0.0]
    }
    peak_force = 0.0
    curr_disp = 0.0
    yield_disp = None
    step = 0

    while curr_disp < maxU:
        ok = ops.analyze(1)
        if ok != 0: break
        step += 1
        ops.reactions()
        if model.section_type == "circular": 
            curr_force = -ops.nodeReaction(1, 1)
            curr_disp = ops.nodeDisp(2, 1)
        else:
            curr_force = ops.nodeReaction(1, 1)
            curr_disp = -ops.nodeDisp(2, 1)
        # print(curr_disp, curr_force)
        if curr_force > peak_force: peak_force = curr_force
        
        # --- Fiber Responses ---
        if model.section_type == "circular":
            sig_c, eps_c = ops.eleResponse(1, 'section', model.fib_sec_tag, 'fiber', -model.core_h, 0.0, model.core_tag, 'stressStrain')
            sig_s, eps_s  = ops.eleResponse(1, 'section', model.fib_sec_tag, 'fiber', model.bar_h, 0.0, model.bar_tag, 'stressStrain')   
        else:
            sig_c, eps_c = ops.eleResponse(1, 'section', model.fib_sec_tag, 'fiber', model.core_h, 0.0, model.core_tag, 'stressStrain')
            sig_s, eps_s  = ops.eleResponse(1, 'section', model.fib_sec_tag, 'fiber', -model.bar_h, 0.0, model.bar_tag, 'stressStrain')

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

        # Termination Checks
        if curr_force < 0.85 * peak_force:
            print(f"⚠️ Strength drop at displacement = {curr_disp:.6f}")
            break
        if eps_c < model.confined_props[-1]:
            print(f"⚠️ Concrete crushed at displacement = {curr_disp:.6f}")
            break
        if eps_s > model.e_ult:
            print(f"⚠️ Steel ruptured at displacement = {curr_disp:.6f}")
            break
        
    results_df = pd.DataFrame(results)
    return results_df, yield_step

