def run_gravity_analysis(P_axial):
    import openseespy.opensees as ops
    ops.timeSeries('Constant', 1)
    ops.pattern('Plain', 1, 1)

    ops.load(2, -P_axial, 0.0, 0.0)

    ops.integrator('LoadControl', 0.0)
    ops.system('SparseGeneral', '-piv')
    ops.test('NormUnbalance', 1e-9, 10)
    ops.numberer('Plain')
    ops.constraints('Plain')
    ops.algorithm('Newton')
    ops.analysis('Static')
    ops.analyze(1)
    ops.loadConst('-time', 0.0)
