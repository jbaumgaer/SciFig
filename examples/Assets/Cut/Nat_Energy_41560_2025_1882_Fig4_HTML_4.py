import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
def solar_cell_jv(v, j_sc, v_oc, ff_factor=15):
    vt = v_oc / ff_factor
    j = j_sc * (1 - (np.exp(v/vt) - 1) / (np.exp(v_oc/vt) - 1))
    return j

voltage = np.linspace(0, 2.2, 100)

# Tandem Cell (High Voltage)
j_sc_val = 16.0
v_oc_val = 2.15

# Forward
j_fwd = solar_cell_jv(voltage, j_sc_val, v_oc_val, ff_factor=25)
# Reverse (Almost identical)
j_rev = solar_cell_jv(voltage, j_sc_val, v_oc_val+0.01, ff_factor=26)

mask = voltage < 2.18

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# Plot
ax.plot(voltage[mask], j_fwd[mask], 'o--', color='#AA4433', mfc='white', label='Forward', markevery=3, lw=2)
ax.plot(voltage[mask], j_rev[mask], 'o-', color='#AA4433', label='Reverse', markevery=3, lw=2)

# Styling
ax.set_xlabel('Voltage (V)', fontsize=14)
ax.set_ylabel(r'Current density (mA cm$^{-2}$)', fontsize=14)
ax.set_ylim(0, 17)
ax.set_xlim(0, 2.2)

# Legend
ax.legend(frameon=False, loc='lower left', fontsize=12)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='in', top=True, right=True)

plt.tight_layout()
plt.show()
