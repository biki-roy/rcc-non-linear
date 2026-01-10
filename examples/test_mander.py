from rcc_non_linear import RectConcreteMander, CircConcreteMander

mander = RectConcreteMander(4.5, 48, 24, 2, 0.5, 3, 68, 0.12, 3, 4)
print(mander.confined_props())
print(mander.unconfined_props())
print("k confinement is:", mander.k)
# concrete = CircConcreteMander(
#     fc_prime=5, D=48, cover=2, dh=0.75, sh=6.0, fyh=68, esm=0.1
# )
# print(concrete.confined_props())
# print(concrete.unconfined_props())
