# generate_report.py

import os
import io
import base64
import datetime
import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI
from CoolProp import CoolProp as CP
from CoolProp.Plots import PropertyPlot
from utils.myVCCmodels import myVCCmodel, getMyPR
from utils.myCompressorModels import myCompressor1
import plotly.graph_objects as go
from jinja2 import Template

# -----------------------------
# 1. Metadata and Input Summary
# -----------------------------
report_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
company = "Seetech Solutions"
fluid = 'R134a'

# OEM Design Specs
Q_evap = 897000.0  # [W]
W_input = 345500.0  # [W]
COP_oem = Q_evap / W_input
SH_oem = 5
SC_oem = 5
Tevap_oem = 280.15  # K (~7C)
Tcond_oem = 318.15  # K (~45C)

# Actual sensor readings
P1_act = 307.7e3  # Pa
P2_act = 1244.0e3  # Pa
Tevap_act = PropsSI("T", "P", P1_act, "Q", 1, fluid)
Tcond_act = PropsSI("T", "P", P2_act, "Q", 0, fluid)
SH_act = 8.6
SC_act = 0.0

# -----------------------------
# 2. Thermodynamic Modeling
# -----------------------------
PR_oem = getMyPR(Tevap_oem, Tcond_oem, fluid)
_, eta_oem = myCompressor1(PR_oem)
P_oem, H_oem, T_oem, S_oem = myVCCmodel(Tevap_oem, Tcond_oem, SH_oem, SC_oem, eta_oem, fluid)

PR_act = getMyPR(Tevap_act, Tcond_act, fluid)
_, eta_act = myCompressor1(PR_act)
P_act, H_act, T_act, S_act = myVCCmodel(Tevap_act, Tcond_act, SH_act, SC_act, eta_act, fluid)

# COP calculations
COP_oem_calc = (H_oem[0] - H_oem[5]) / (H_oem[1] - H_oem[0])
COP_act_calc = (H_act[0] - H_act[5]) / (H_act[1] - H_act[0])
eff_loss = 100 * (COP_oem_calc - COP_act_calc) / COP_oem_calc

# -----------------------------
# 3. Utility: Matplotlib -> base64
# -----------------------------
def save_matplotlib_plot(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

# -----------------------------
# 4. Generate Matplotlib Diagrams
# -----------------------------
plots_base64 = {}

def make_diagram(P, H, T, S, tag, color):
    # p-h
    ph = PropertyPlot(f'HEOS::{fluid}', 'PH', unit_system='SI', tp_limits='ACHP')
    ph.calc_isolines(CP.iQ, num=11)
    ph.calc_isolines(CP.iT, num=25)
    ph.calc_isolines(CP.iSmass, num=15)
    ax1 = ph.figure.gca()
    ax1.plot(H, P, color=color, marker='o')
    fig1 = plt.gcf()
    fig1.suptitle(f'p-h Diagram ({tag})')
    plots_base64[f'{tag}_ph'] = save_matplotlib_plot(fig1)
    plt.close()

    # T-s
    ts = PropertyPlot(f'HEOS::{fluid}', 'TS', unit_system='SI', tp_limits='ACHP')
    ts.calc_isolines(CP.iQ, num=11)
    ts.calc_isolines(CP.iP, num=25)
    ax2 = ts.figure.gca()
    ax2.plot(S, T, color=color, marker='o')
    fig2 = plt.gcf()
    fig2.suptitle(f'T-s Diagram ({tag})')
    plots_base64[f'{tag}_ts'] = save_matplotlib_plot(fig2)
    plt.close()

make_diagram(P_oem, H_oem, T_oem, S_oem, 'OEM', 'blue')
make_diagram(P_act, H_act, T_act, S_act, 'Actual', 'red')

# -----------------------------
# 5. Generate HTML using Jinja2
# -----------------------------
html_template = Template(open('report_template.html').read())
html_out = html_template.render(
    date=report_date,
    company=company,
    COP_oem=f"{COP_oem_calc:.2f}",
    COP_act=f"{COP_act_calc:.2f}",
    eff_loss=f"{eff_loss:.1f}%",
    plots=plots_base64,
    evap_oem=Tevap_oem - 273.15,
    cond_oem=Tcond_oem - 273.15,
    evap_act=Tevap_act - 273.15,
    cond_act=Tcond_act - 273.15
)

with open("refrigeration_report.html", "w") as f:
    f.write(html_out)

print("✅ Report generated: refrigeration_report.html")
