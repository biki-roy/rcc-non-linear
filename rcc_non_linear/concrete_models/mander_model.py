import math
import numpy as np

try:
    from importlib.resources import files  # Python ≥3.9
except ImportError:
    from importlib_resources import files  # Python 3.8

import pandas as pd
from rcc_non_linear.utils.helper import interpolate_z


def load_mander_k():
    data_path = files("rcc_non_linear.concrete_models.data") / "rect_conf_k.csv"
    return pd.read_csv(data_path, header=None)

def rect_ke(col):
    """Calculate confinement effectiveness coefficient ke for rectangular columns."""

    bc = col.B - 2 * col.cover - col.dh
    hc = col.H - 2 * col.cover - col.dh
    s_prime = col.sh - col.dh
    rho = col.As / col.Ag
    w_prime_top = (bc-col.dh-col.dbTop)/(col.nBarsTop-1) - col.dh
    w_prime_left = (hc-col.dh-col.dbTop)/(col.nBarsInt+1) - col.dh
    p1 = (1-2*(col.nBarsTop-1)*w_prime_top**2/(6*bc*hc)-2*(col.nBarsInt+1)*w_prime_left**2/(6*bc*hc))
    p2 = 1-s_prime/(2*bc)
    p3 = 1-s_prime/(2*hc)
    ke = p1*p2*p3 / (1-rho)
    return ke

class RectConcreteMander:
    def __init__(self, fc_prime, B, H, cover, dh, sh, fyh, esm,  nx=2, ny=2, ke=None):
        Avx = nx * math.pi * dh**2 / 4
        Avy = ny * math.pi * dh**2 / 4
        w_corex = B - 2 * cover - dh
        w_corey = H - 2 * cover - dh
        rho_x = Avx / (w_corey * sh)
        rho_y = Avy / (w_corex * sh)

        ke = ke if ke is not None else 0.75
        f_lx = ke * rho_x * fyh / fc_prime
        f_ly = ke * rho_y * fyh / fc_prime

        k = interpolate_z(load_mander_k(), min(f_lx, f_ly), max(f_lx, f_ly))
        self.fc_prime = fc_prime
        self.fcc_prime = k * fc_prime  # peak stress
        self.ecc = 0.002 * (
            1 + 5 * (self.fcc_prime / fc_prime - 1)
        )  # strain at peak stress
        self.ecu = (
            0.004 + 1.4 * (rho_x + rho_y) * fyh * esm / self.fcc_prime
        )  # ultimate strain
        self.k = k
        self.Ec = 57 * math.sqrt(self.fc_prime * 1000)

    def fc(self, e, ecc, fcc):
        """gives concrete stress at strain e. fcc is the peak stress at strain of ecc."""
        x = e / ecc
        Esec = fcc / ecc
        r = self.Ec / (self.Ec - Esec)
        fc = fcc * x * r / (r - 1 + x**r)
        return fc

    def confined_props(self):
        fc = self.fc(self.ecu, self.ecc, self.fcc_prime)
        return [-self.fcc_prime, -self.ecc, -fc, -self.ecu]

    def unconfined_props(self):
        fc = self.fc(0.005, 0.002, self.fc_prime)
        return [-self.fc_prime, -0.002, -0, -0.005]  # 0 to be replaced by fc


class CircConcreteMander:
    def __init__(self, fc_prime, D, cover, dh, sh, fyh, esm):
        Asp = math.pi * dh**2 / 4
        self.fc_prime = fc_prime
        self.ds = D - 2 * cover - dh
        self.fl_prime = 2 * Asp * fyh / (self.ds * sh)
        self.fyh = fyh
        self.esm = esm
        self.rho = 4 * Asp / (self.ds * sh)
        self.Ec = 57 * math.sqrt(fc_prime * 1000)
        k1 = 2.254 * math.sqrt(1 + 7.94 * self.fl_prime / self.fc_prime)
        self.fcc_prime = self.fc_prime * (
            -1.254 + k1 - 2 * self.fl_prime / self.fc_prime
        )
        self.ecc = 0.002 * (1 + 5 * (self.fcc_prime / self.fc_prime - 1))
        self.ecu = 0.004 + 1.4 * self.rho * self.fyh * self.esm / self.fcc_prime

    def fc(self, e, ecc, fcc):
        """gives concrete stress at strain e. fcc is the peak stress at strain of ecc."""
        x = e / ecc
        Esec = fcc / ecc
        r = self.Ec / (self.Ec - Esec)
        fc = fcc * x * r / (r - 1 + x**r)
        return fc

    def confined_props(self):
        fc = self.fc(self.ecu, self.ecc, self.fcc_prime)
        return [-self.fcc_prime, -self.ecc, -fc, -self.ecu]

    def unconfined_props(self):
        fc = self.fc(0.005, 0.002, self.fc_prime)
        return [-self.fc_prime, -0.002, -0, -0.005]  # 0 to be replaced by fc


class SteelMander:
    def __init__(self, fy, fu, Es, Esh, esh, esu):
        self.fy, self.fu, self.Es, self.Esh, self.esh, self.esu = (
            fy,
            fu,
            Es,
            Esh,
            esh,
            esu,
        )
        self.p = self.Esh * (self.esu - self.esh) / (self.fu - self.fy)
        self.ey = self.fy / self.Es

    def fs(self, es):
        if es >= 0 and es <= self.ey:
            return self.Es * es
        elif es > self.ey and es <= self.esh:
            return self.fy
        else:
            return (
                self.fu
                + (self.fy - self.fu)
                * abs((self.esu - es) / (self.esu - self.esh)) ** self.p
            )

    def get_fs(self, es):
        """
        Element-wise evaluation of fs for array-like input.
        """
        if np.isscalar(es):
            return self.fs(es)
        es = np.asarray(es, dtype=float)
        return np.array([self.fs(e) for e in es])
