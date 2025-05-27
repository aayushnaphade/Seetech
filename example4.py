# Re-import necessary modules after environment reset
import os
import io
import base64
import datetime
import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI
from CoolProp.Plots import PropertyPlot
from scipy.optimize import minimize
import plotly.graph_objects as go
import plotly.io as pio

# Load user-defined modules again (simulate here with placeholders if needed)
from utils.myVCCmodels import myVCCmodel, getMyPR
from utils.myCompressorModels import myCompressor1

# -----------------------------
# 1. Metadata and Input Summary
# -----------------------------
now = datetime.datetime.now()
report_date = now.strftime("%Y-%m-%d %H:%M:%S")
company = "Seetech Solutions"

# OEM specs
Q_evap = 897000.0  # [W]
W_input = 345500.0  # [W]
COP_oem = Q_evap / W_input
SH_oem = 5
SC_oem = 5
fluid = 'R134a'

# -----------------------------
# 2. Optimize OEM Cycle to match COP
# -----------------------------
def cycle_error(x):
    Tevap_K, Tcond_K = x
    if Tcond_K - Tevap_K < 10:
        return 1e6
    try:
        P1 = PropsSI("P", "T", Tevap_K, "Q", 1, fluid)
        T1 = Tevap_K + SH_oem
        h1 = PropsSI("H", "P", P1, "T", T1, fluid)
        s1 = PropsSI("S", "P", P1, "H", h1, fluid)

        P2 = PropsSI("P", "T", Tcond_K, "Q", 0, fluid)
        T3 = Tcond_K - SC_oem
        h3 = PropsSI("H", "P", P2, "T", T3, fluid)
        h4 = h3

        h2s = PropsSI("H", "P", P2, "S", s1, fluid)
        eta_guess = 0.75
        h2 = h1 + (h2s - h1) / eta_guess

        lhs = (h2 - h1) / (h1 - h4)
        rhs = 1 / COP_oem
        return abs(lhs - rhs)
    except:
        return 1e6

x0 = [280.15, 318.15]
bounds = [(273.15, 288.15), (308.15, 328.15)]
result = minimize(cycle_error, x0, bounds=bounds)
Tevap_oem, Tcond_oem = result.x

# -----------------------------
# 3. Compute OEM Thermodynamic Points
# -----------------------------
PR_oem = getMyPR(Tevap_oem, Tcond_oem, fluid)
_, eta_oem = myCompressor1(PR_oem)
P_oem, H_oem, T_oem, S_oem = myVCCmodel(Tevap_oem, Tcond_oem, SH_oem, SC_oem, eta_oem, fluid)

# -----------------------------
# 4. Compute Actual Thermodynamic Points
# -----------------------------
# Actual values from hardware
P1_act = 307.7e3
P2_act = 1244.0e3
Tevap_act = PropsSI("T", "P", P1_act, "Q", 1, fluid)
Tcond_act = PropsSI("T", "P", P2_act, "Q", 0, fluid)
SH_act = 8.6
SC_act = 0.0
PR_act = getMyPR(Tevap_act, Tcond_act, fluid)
_, eta_act = myCompressor1(PR_act)
P_act, H_act, T_act, S_act = myVCCmodel(Tevap_act, Tcond_act, SH_act, SC_act, eta_act, fluid)

# -----------------------------
# 5. COP & Efficiency Calculation
# -----------------------------
h1_oem, h2_oem, h3_oem, h4_oem = H_oem[0], H_oem[1], H_oem[4], H_oem[5]
COP_oem_calc = (h1_oem - h4_oem) / (h2_oem - h1_oem)

h1_act, h2_act, h3_act, h4_act = H_act[0], H_act[1], H_act[4], H_act[5]
COP_act_calc = (h1_act - h4_act) / (h2_act - h1_act)
eff_loss_pct = 100 * (COP_oem_calc - COP_act_calc) / COP_oem_calc

(COP_oem_calc, COP_act_calc, eff_loss_pct)

