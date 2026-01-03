import openseespy.opensees as ops
import opsvis as opsv
from rcc_non_linear import Model

col_props = {
    'fc': 5.366,
    'B': 23.622, 'H': 23.622, 'L': 155.1181,
    'cover': 1.5748,
    'nBarsTop': 5, 'dbTop': 0.984,
    'nBarsBot': 5, 'dbBot': 0.984,
    'nBarsInt': 6, 'dbInt': 0.984,
    'fy': 69.62, 'fu': 101.4, 'Es': 29000, 'e_ult': 0.106,
    'dh':0.512, 'sh':3.937, 'fyh':44.13, 'esm':0.0762, 
    'nx': 5, 'ny':5,
    'P_axial': 197.62
}

model = Model(col_props)

print(model.confined_props)
print(model.fib_section)

#To plot the fiber section, use any of the following methods:
# model.plot_fib_section()
model.fib_section.plot()
