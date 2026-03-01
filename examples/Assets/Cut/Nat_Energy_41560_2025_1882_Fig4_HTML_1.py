import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Single Diode Model Approximation
# J = JL - J0 * (exp(q(V+J*Rs)/nkT) - 1)
# Simplified: J approx JL - J0 * exp(V/Vt)

def solar_cell_jv(v, j_sc, v_oc, ff_factor=10):
    # Normalized curve shape
    # v is array of voltage
    # j_sc is short circuit current
    # v_oc is open circuit voltage
    # Returns j

    # Simple explicit approximation: J = Jsc * (1 - exp(A * (V - Voc)))? No
    # J = Jsc * (1 - (exp(V/Vt) - 1)/(exp(Voc/Vt) - 1))

    vt = v_oc / ff_factor # Shape factor
    j = j_sc * (1 - (np.exp(v/vt) - 1) / (np.exp(v_oc/vt) - 1))
    return j

voltage = np.linspace(0, 1.25, 100)

# Control
# Forward: Lower FF, hysteresis
j_ctrl_fwd = solar_cell_jv(voltage, j_sc=25.6, v_oc=1.14, ff_factor=18)
# Reverse: Better FF
j_ctrl_rev = solar_cell_jv(voltage, j_sc=25.6, v_oc=1.15, ff_factor=25)

# Target (PHNS + BNAC)
# Forward: High FF, low hysteresis
j_trgt_fwd = solar_cell_jv(voltage, j_sc=26.3, v_oc=1.20, ff_factor=28)
# Reverse: Similar to forward
j_trgt_rev = solar_cell_jv(voltage, j_sc=26.3, v_oc=1.205, ff_factor=30)

# Mask negative currents for clean plot like original
mask = voltage < 1.21

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# Control
ax.plot(voltage[mask], j_ctrl_fwd[mask], 'o--', color='#335577', label='Forward control', markersize=6, markevery=4, lw=2)
ax.plot(voltage[mask], j_ctrl_rev[mask], 'o-', color='#335577', label='Reverse control', markersize=6, markevery=4, lw=2)

# Target
ax.plot(voltage[mask], j_trgt_fwd[mask], 'o--', color='#AA4433', label='Forward PHNS + BNAC', markersize=6, markevery=4, lw=2)
ax.plot(voltage[mask], j_trgt_rev[mask], 'o-', color='#AA4433', label='Reverse PHNS + BNAC', markersize=6, markevery=4, lw=2)

# Styling
ax.set_xlabel('Voltage (V)', fontsize=14)
ax.set_ylabel(r'Current density (mA cm$^{-2}$)', fontsize=14)
ax.set_ylim(0, 27.5)
ax.set_xlim(0, 1.22)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='in', which='both', top=True, right=True)

# Legend
ax.legend(frameon=False, loc='lower left', fontsize=12)

plt.tight_layout()
plt.show()
