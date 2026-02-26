import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
temp = np.array([50, 100, 150, 200, 250, 300])

# Without PU (Teal Circles)
# 2.1 -> 1.7 -> ... -> 1.0
tau_wo = np.array([2.1, 1.7, 1.5, 1.25, 1.1, 0.95])

# With PU (Green Squares)
# 1.75 -> 1.4 -> ... -> 0.85
tau_w = np.array([1.75, 1.4, 1.25, 1.1, 0.95, 0.85])

# --- Plotting ---
fig, ax = plt.subplots(figsize=(5, 5), dpi=150)

# Plots
ax.plot(temp, tau_wo, 'o-', color='#009999', markersize=8, label='Without PU')
ax.plot(temp, tau_w, 's-', color='#116633', markersize=8, label='With PU')

# Arrow
ax.arrow(150, 1.5, 0, -0.6, width=2, head_width=10, head_length=0.1, color='#CCDDEE', alpha=0.5, length_includes_head=True)
ax.text(250, 1.8, 'Exciplex-free
cohost', ha='center', fontsize=14)

# Styling
ax.set_xlabel('Temperature (K)', fontsize=14)
ax.set_ylabel(r'PL lifetime ($\mu$s)', fontsize=14)
ax.set_xlim(0, 350)
ax.set_ylim(0, 2.2)

# Legend
ax.legend(frameon=False, loc='lower left', fontsize=12)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='out', top=False, right=False)

plt.tight_layout()
plt.show()
