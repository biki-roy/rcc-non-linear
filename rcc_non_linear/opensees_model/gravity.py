def run_gravity_analysis(P_axial, type = "MC"):
    import openseespy.opensees as ops
    ops.timeSeries('Constant', 1)
    ops.pattern('Plain', 1, 1)
    if type == "MC":
        ops.load(2, -P_axial, 0.0, 0.0)
    else:
        ops.load(2, 0.0, -P_axial, 0.0)
    ops.integrator('LoadControl', 0.0)
    ops.system('SparseGeneral', '-piv')
    ops.test('NormUnbalance', 1e-6, 10)
    ops.numberer('Plain')
    ops.constraints('Plain')
    ops.algorithm('Newton')
    ops.analysis('Static')
    ops.analyze(1)
    ops.loadConst('-time', 0.0)

# def run_gravity_analysis(P_axial):        #This was taken for pushover analysis from my colab code
#     import openseespy.opensees as ops
#     ops.timeSeries('Linear', 1)
#     ops.pattern('Plain', 1, 1)
#     ops.load(2, 0.0, -P_axial, 0.0)

#     ops.system('BandGeneral')
#     ops.numberer('RCM')
#     ops.constraints('Transformation')
#     ops.test('NormDispIncr', 1.0e-8, 10)
#     ops.algorithm('Newton')
#     ops.integrator('LoadControl', 1)
#     ops.analysis('Static')
#     ops.analyze(1)
#     ops.loadConst('-time', 0.0)
