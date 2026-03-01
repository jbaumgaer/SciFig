import matplotlib.pyplot as plt
import numpy as np


# --- Data Simulation ---
def solar_cell_jv(v, j_sc, v_oc, ff_factor=15):
    vt = v_oc / ff_factor
    j = j_sc * (1 - (np.exp(v/vt) - 1) / (np.exp(v_oc/vt) - 1))
    return j

voltage = np.linspace(0, 0.95, 100)

# Control
j_ctrl = solar_cell_jv(voltage, 31.8, 0.88, ff_factor=20)

# Dipolar
j_dip = solar_cell_jv(voltage, 32.2, 0.89, ff_factor=22)

# --- Plotting ---
fig, ax = plt.subplots(figsize=(5, 5), dpi=150)

# Plots
ax.plot(voltage, j_ctrl, 'o-', color='#77AADD', mfc='white', markevery=4, label='Control, PCE = 23.1%')
ax.plot(voltage, j_dip, 'o-', color='#1166AA', markevery=4, label='Dipolar passivation, PCE = 24.1%')

# Text
ax.text(0.05, 26, 'SCAPS-1D', fontsize=12)

# Legend
ax.legend(frameon=False, loc='lower left', fontsize=10)

# Styling
ax.set_xlabel('Voltage (V)', fontsize=14)
ax.set_ylabel(r'Current density (mA cm$^{-2}$)', fontsize=14)
ax.set_ylim(0, 35)
ax.set_xlim(0, 0.95)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='in', top=True, right=True)

plt.tight_layout()
plt.show()
