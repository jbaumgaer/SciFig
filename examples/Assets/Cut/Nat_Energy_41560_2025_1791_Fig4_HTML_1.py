import matplotlib.pyplot as plt
import numpy as np


# --- Data Simulation ---
# J-V Curve
def solar_cell_jv(v, j_sc, v_oc, ff_factor=15):
    vt = v_oc / ff_factor
    j = j_sc * (1 - (np.exp(v/vt) - 1) / (np.exp(v_oc/vt) - 1))
    return j

voltage = np.linspace(0, 1.2, 100)
# Ref
j_ref = solar_cell_jv(voltage, j_sc=25.5, v_oc=1.12, ff_factor=18)
# SP
j_sp = solar_cell_jv(voltage, j_sc=25.8, v_oc=1.16, ff_factor=25)

# Histogram Data
# Ref: Center 22.5, sigma 0.5
pce_ref = np.random.normal(22.5, 0.5, 20)
# SP: Center 24.3, sigma 0.4
pce_sp = np.random.normal(24.3, 0.4, 20)


# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 6), dpi=150)

# Main Plot
ax.plot(voltage, j_ref, 'o-', color='#006688', mfc='white', label='Ref', markevery=5)
ax.plot(voltage, j_sp, 'o-', color='#004455', mfc='#004455', label='SP', markevery=5)

# Styling
ax.set_xlabel('Voltage (V)', fontsize=14)
ax.set_ylabel(r'Current density (mA cm$^{-2}$)', fontsize=14)
ax.set_ylim(0, 26.5)
ax.set_xlim(0, 1.25)
ax.legend(frameon=False, loc='lower left', fontsize=14, bbox_to_anchor=(0.05, 0.05))

# Composition Text
ax.text(0.5, 0.1, r'Cs$_{0.05}$FA$_{0.95}$PbI$_3$', transform=ax.transAxes, fontsize=14)

plt.tight_layout()
plt.show()

