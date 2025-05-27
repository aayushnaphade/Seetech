import numpy as np
import plotly.graph_objects as go
from CoolProp.CoolProp import PropsSI
from utils.myVCCmodels import myVCCmodel, getMyPR
from utils.myCompressorModels import myCompressor1
import plotly.io as pio
pio.renderers.default = 'browser'  # optional fallback
fluid = 'R134a'

# -----------------------------
# 1. OEM-Matched Cycle
# -----------------------------
Q_evap = 897e3
W_input = 345.5e3
COP_oem = Q_evap / W_input
SH_oem = 5
SC_oem = 5

# Assumed optimal temperatures (you can optimize with scipy if needed)
Tevap_oem = 280.15  # ~7°C
Tcond_oem = 318.15  # ~45°C

PR_oem = getMyPR(Tevap_oem, Tcond_oem, fluid)
_, eta_oem = myCompressor1(PR_oem)
P_oem, H_oem, T_oem, S_oem = myVCCmodel(Tevap_oem, Tcond_oem, SH_oem, SC_oem, eta_oem, fluid)

# -----------------------------
# 2. Actual Sensor-Based Cycle
# -----------------------------
P1_act = 307.7e3  # Suction pressure
P2_act = 1244.0e3 # Condenser pressure

# Derive Tevap and Tcond from measured pressures
Tevap_act = PropsSI("T", "P", P1_act, "Q", 1, fluid)
Tcond_act = PropsSI("T", "P", P2_act, "Q", 0, fluid)

SH_act = 8.6
SC_act = 0.0

PR_act = getMyPR(Tevap_act, Tcond_act, fluid)
_, eta_act = myCompressor1(PR_act)
P_act, H_act, T_act, S_act = myVCCmodel(Tevap_act, Tcond_act, SH_act, SC_act, eta_act, fluid)

# -----------------------------
# 3. Saturation Dome (safe range)
# -----------------------------
T_crit = PropsSI("Tcrit", fluid)
T_min = PropsSI("Tmin", fluid)
T_dome = np.linspace(T_min + 1, T_crit - 0.1, 300)

h_liq_dome = [PropsSI("H", "T", T, "Q", 0, fluid) for T in T_dome]
h_vap_dome = [PropsSI("H", "T", T, "Q", 1, fluid) for T in T_dome]
P_liq_dome = [PropsSI("P", "T", T, "Q", 0, fluid) for T in T_dome]
P_vap_dome = [PropsSI("P", "T", T, "Q", 1, fluid) for T in T_dome]

# -----------------------------
# 4. Interactive Plotly Figure
# -----------------------------
fig = go.Figure()

# Saturation Dome
fig.add_trace(go.Scatter(x=h_liq_dome, y=P_liq_dome,
    mode='lines', name='Sat. Liquid Dome', line=dict(color='black')))
fig.add_trace(go.Scatter(x=h_vap_dome, y=P_vap_dome,
    mode='lines', name='Sat. Vapor Dome', line=dict(color='black')))

# OEM Cycle
fig.add_trace(go.Scatter(x=H_oem, y=P_oem, mode='lines+markers',
    name='OEM Cycle', line=dict(color='blue'),
    hovertemplate=
        'State %{pointIndex}<br>'+
        'h = %{x:.0f} J/kg<br>'+
        'P = %{y:.0f} Pa<br>'+
        'T = %{customdata[0]:.2f} K<br>'+
        's = %{customdata[1]:.2f} J/kg·K',
    customdata=list(zip(T_oem, S_oem))
))

# Actual Cycle
fig.add_trace(go.Scatter(x=H_act, y=P_act, mode='lines+markers',
    name='Actual Cycle', line=dict(color='red'),
    hovertemplate=
        'State %{pointIndex}<br>'+
        'h = %{x:.0f} J/kg<br>'+
        'P = %{y:.0f} Pa<br>'+
        'T = %{customdata[0]:.2f} K<br>'+
        's = %{customdata[1]:.2f} J/kg·K',
    customdata=list(zip(T_act, S_act))
))

# Shaded Degradation Zone (between OEM and Actual)
# Interpolate actual pressure at OEM enthalpy values
P_act_interp = np.interp(H_oem, H_act, P_act)
fig.add_trace(go.Scatter(
    x=np.concatenate([H_oem, H_oem[::-1]]),
    y=np.concatenate([P_oem, P_act_interp[::-1]]),
    fill='toself',
    fillcolor='rgba(255,0,0,0.2)',
    line=dict(color='rgba(255,0,0,0)'),
    hoverinfo='skip',
    name='Degradation Zone'
))

# Layout
fig.update_layout(
    title='Overlay of OEM vs Actual Refrigeration Cycle (p-h Diagram)',
    xaxis_title='Specific Enthalpy [J/kg]',
    yaxis_title='Pressure [Pa]',
    hovermode='closest',
    legend=dict(x=0.7, y=0.9)
)
fig.write_html("refrigeration_cycle.html", auto_open=True)
# fig.show()
