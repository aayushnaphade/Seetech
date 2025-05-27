# Seetech
create a utils folder and put myCompressorModels.py , myPlots.py ,myVCCmodels.py 
# Refrigeration Cycle State Points Reference

This document explains how the 6–7 thermodynamic state points used in the p-h and T-s diagrams are derived from actual chiller data.

---

## 📌 Purpose

These state points allow us to reconstruct and visualize the actual vapor-compression refrigeration cycle on p-h and T-s diagrams for diagnostic and performance evaluation purposes.

---

## 🔷 Source: Sensor Data

From your input, we used the following fields:

* **Evaporator Pressure** = 307.7 kPa
* **Condenser Pressure** = 1244.0 kPa
* **Suction Temperature** = 18.1°C
* **Discharge Temperature** = 54.2°C
* **Suction Superheat** = 8.6°C
* **Subcooling** = 0.0°C (assumed)

---

## ⚙️ Refrigeration Cycle Point Map

### Point 1 – Compressor Inlet (Evaporator outlet → Suction Line)

* **Known from sensors:**

  * Suction Temperature = 18.1°C
  * Evaporator Pressure = 307.7 kPa
* **Computed using CoolProp:**

  * `h1 = PropsSI("H", "P", P1, "T", T1, fluid)`
  * `s1 = PropsSI("S", ...)`
* Represents **superheated vapor** entering the compressor.

### Point 2 – Compressor Outlet (Discharge line)

* **Known from sensors:**

  * Discharge Temperature = 54.2°C
  * Condenser Pressure = 1244.0 kPa
* **Computed using CoolProp:**

  * `h2 = PropsSI("H", "P", P2, "T", T2, fluid)`
  * `s2 = PropsSI("S", ...)`
* Represents **high-pressure superheated vapor** exiting compressor.

### Point 3 – Condenser Outlet (saturated liquid)

* **Assumption based on P2:**

  * Saturated liquid at 1244.0 kPa
* **Computed using CoolProp:**

  * `h3 = PropsSI("H", "P", P2, "Q", 0, fluid)`
  * `s3 = PropsSI("S", ...)`
* Represents **ideal subcooled liquid**, although SC = 0.0°C assumed.

### Point 4 – Expansion Valve Outlet

* **h4 = h3** (isenthalpic expansion)
* **Evaporator Pressure = 307.7 kPa**
* **Computed using CoolProp:**

  * `s4 = PropsSI("S", "P", P1, "H", h4, fluid)`
  * `T4 = PropsSI("T", ...)`
* Represents **two-phase mixture** entering the evaporator.

---

## 🔁 Cycle Closure Points

### Point 5 (optional) – 100% vapor (Q=1 line)

* Helps plot the dome boundary.

### Point 6 (loop back to Point 1)

* To close the cycle loop for plotting purposes.

---

## 📐 COP Calculation

COP (Coefficient of Performance) is calculated using the enthalpy values at key points:

* **Cooling effect (qᵢₙ):** $q_{in} = h_1 - h_4$

* **Compressor work (w):** $w = h_2 - h_1$

* **COP:** $$\text{COP} = \frac{h_1 - h_4}{h_2 - h_1}$$

* This is computed for both:

  * **OEM cycle:** using enthalpies from `myVCCmodel()` at SH = 5K, SC = 5K
  * **Actual cycle:** using sensor pressures + SH = 8.6K, SC = 0K

This gives us:

* `COP_oem_calc = (h1_oem - h4_oem) / (h2_oem - h1_oem)`
* `COP_act_calc = (h1_act - h4_act) / (h2_act - h1_act)`

The **efficiency loss** is then:

   $$ % \text{Loss} = 100 * \frac{\text{COP}_{OEM} - \text{COP}_{Actual}}{\text{COP}_{OEM}} $$

---

## 🧠 Explanation: What `myVCCmodel()` Does

`myVCCmodel(Tevap, Tcond, SH, SC, η, fluid)` is a function that builds a full refrigeration cycle using input conditions:

* **Inputs:**

  * `Tevap`: Evaporator saturation temperature (K)
  * `Tcond`: Condenser saturation temperature (K)
  * `SH`: Superheat \[K]
  * `SC`: Subcooling \[K]
  * `η`: Isentropic compressor efficiency
  * `fluid`: refrigerant (e.g., R134a)

* **What It Returns:**

  * Lists of pressure (P), enthalpy (H), temperature (T), and entropy (S) for 8 major cycle points
  * These points form a closed loop: 1 → 2 → saturated → 3 → 4 → saturated → 1

* **Used for:**

  * Generating the full thermodynamic path for plotting p-h and T-s diagrams
  * Enables comparison between ideal/OEM and real-world cycles

## ⚙️ What `myCompressor1()` Does

This function estimates compressor **isentropic efficiency** based on **pressure ratio (PR)**:

* Input: PR = P₂ / P₁ (condenser pressure over evaporator pressure)
* Output: tuple `(COP, η)` — where η is estimated from empirical correlations or models

This reflects real-world compressor behavior which varies with pressure lift.

### 📈 Where Does η Come From?

Internally, `myCompressor1()` likely uses a simplified empirical relationship, for example:

```python
if PR < 1.5:
    η = 0.75
elif PR < 3.0:
    η = 0.72
elif PR < 5.0:
    η = 0.68
else:
    η = 0.6
```

Or a log fit:

```python
η = a - b * log(PR)
```

These coefficients (`a`, `b`) are based on compressor maps or field test data from OEMs. For your system:

* Evaporator Pressure = 307.7 kPa
* Condenser Pressure = 1244.0 kPa
* PR ≈ 4.04 → implies η ≈ 0.67 (typical range)

---

## ✅ Summary Table

| Point | Description            | Input Used         | Phase             |
| ----- | ---------------------- | ------------------ | ----------------- |
| 1     | Compressor Inlet       | Suction Temp, P1   | Superheated Vapor |
| 2     | Compressor Outlet      | Discharge Temp, P2 | Superheated Vapor |
| 3     | Condenser Outlet       | P2 (Q=0)           | Saturated Liquid  |
| 4     | Expansion Valve Outlet | h3, P1             | 2-phase Mixture   |

---

## 📎 Notes

* If subcooling were available, Point 3 would shift left.
* If SH varies across sensors (8.6°C vs 14.2°C), take average or validate sensor source.
* EXV position (3.29) confirms partially throttled expansion.
* Press Ratio = P2 / P1 = 3.29 (matches expected value)

---

For debugging or validation, refer to `myVCCmodel()` logic and CoolProp documentation.

Prepared by: **Seetech Solutions**
