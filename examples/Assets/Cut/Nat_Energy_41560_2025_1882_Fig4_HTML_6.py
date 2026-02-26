import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Time
time_ctrl = np.linspace(0, 1000, 500)
time_trgt = np.linspace(0, 2000, 1000)

# Control (Blue) - Degrades
pce_ctrl = 1.0 - 0.15 * (time_ctrl / 1000) + np.random.normal(0, 0.02, len(time_ctrl))

# Target (Red) - Stable
pce_trgt = 1.0 - 0.02 * (time_trgt / 2000) + np.random.normal(0, 0.015, len(time_trgt))

# --- Plotting ---
fig, ax = plt.subplots(figsize=(10, 4), dpi=150)

# Scatter
ax.scatter(time_ctrl, pce_ctrl, s=15, color='#335577', edgecolors='black', lw=0.5, label='Control')
ax.scatter(time_trgt, pce_trgt, s=15, color='#AA4433', edgecolors='black', lw=0.5, label='PHNS + BNAC')

# Styling
ax.set_xlabel('Time (h)', fontsize=14)
ax.set_ylabel('Normalized PCE', fontsize=14)
ax.set_ylim(0.4, 1.1)
ax.set_xlim(-100, 2100)

# Legend
ax.legend(frameon=False, loc='center left', fontsize=12, bbox_to_anchor=(0.01, 0.4))

# Text
ax.text(0.02, 0.25, r'Encapsulated FA$_{0.95}$Cs$_{0.05}$PbI$_3$ PSC devices', transform=ax.transAxes, fontsize=12)
ax.text(0.02, 0.15, 'MPPT under 1-Sun illumination in ambient air, 65 °C', transform=ax.transAxes, fontsize=12)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='in', top=True, right=True)

plt.tight_layout()
plt.show()
