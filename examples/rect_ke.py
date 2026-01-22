from rcc_non_linear import RectConcreteMander
from rcc_non_linear.utils.helper import interpolate_z
from rcc_non_linear.concrete_models.mander_model import rect_ke, load_mander_k

print("ke manual=", interpolate_z(load_mander_k(),0.0034581, 0.0082274))

rect1 = RectConcreteMander(fc_prime=5.075, B=27.558, H=13.779, cover=1.77, dh=0.248, sh=11.811, fyh=68, esm=0.1, nx=2, ny=2, ke=0.75)
print("k:", rect1.k)
print("fcc_prime:", rect1.fcc_prime)
print("ecu:", rect1.ecu)