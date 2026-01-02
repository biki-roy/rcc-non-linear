import math
from importlib.resources import files
import pandas as pd
from rcc_non_linear.utils.helper import interpolate_z

def load_mander_k():
    data_path = (
        files("rcc_non_linear.concrete_models.data")
        / "rect_conf_k.csv"
    )
    return pd.read_csv(data_path)

class RectConcreteMander:
  def __init__(self, fc_prime, B, H, cover, dh, sh, fyh, esm, nx=2, ny=2):
    Avx = nx * math.pi * dh**2/4
    Avy = ny * math.pi * dh**2/4
    w_corex = B - 2 * cover - dh
    w_corey = H - 2 * cover - dh
    rho_x = Avx / (w_corey*sh)
    rho_y = Avy / (w_corex*sh)

    f_lx = 0.75 * rho_x * fyh / fc_prime
    f_ly = 0.75 * rho_y * fyh / fc_prime

    k = interpolate_z(load_mander_k(), min(f_lx, f_ly), max(f_lx, f_ly))
    self.fc_prime = fc_prime
    self.fcc_prime = k * fc_prime  #peak stress
    self.ecc = 0.002 * (1+5*(self.fcc_prime/fc_prime-1))  #strain at peak stress
    self.ecu = 0.004 + 1.4 * (rho_x + rho_y) * fyh * esm / self.fcc_prime #ultimate strain

  def fc(self, e):
    x = e/self.ecc
    Ec = 57 * math.sqrt(self.fc_prime*1000)
    Esec = self.fcc_prime / self.ecc
    r = Ec / (Ec - Esec)
    fc = self.fcc_prime * x * r / (r - 1 + x**r)
    return fc

  def confined_props(self):
    fc = self.fc(self.ecu)
    return [-self.fcc_prime, -self.ecc, -fc, -self.ecu]

  def unconfined_props(self):
    fc = self.fc(0.005)
    return [-self.fc_prime, -0.002, -0, -0.005]     #0 to be replaced by fc