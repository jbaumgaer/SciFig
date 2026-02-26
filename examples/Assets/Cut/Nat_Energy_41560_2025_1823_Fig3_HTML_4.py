import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
time = np.linspace(0, 25, 300)

def decay(t, t1, a1, t2, a2):
    return a1 * np.exp(-t/t1) + a2 * np.exp(-t/t2)

# 1. Control (Blue) - Slower (4.91 ns)
y_ctrl = decay(time, 4.91, 0.7, 20, 0.1) + 0.02
y_ctrl += np.random.normal(0, 0.005, len(time))

# 2. HDI Treated (Red) - Faster (3.51 ns)
y_hdi = decay(time, 3.51, 0.8, 15, 0.05) + 0.02
y_hdi += np.random.normal(0, 0.005, len(time))

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# Plots
ax.plot(time, y_ctrl, 'o-', color='#4488CC', mfc='none', markersize=8, mew=2, label='Control')
ax.plot(time, y_hdi, 'o-', color='#FF5555', mfc='none', markersize=8, mew=2, label='HDI treated')

# Labels
ax.text(5, 0.08, '3.51 ns', color='#FF5555', fontsize=12)
ax.text(5, 0.4, '4.91 ns', color='#4488CC', fontsize=12)

# Legend
ax.legend(frameon=False, loc='upper right', fontsize=10)
ax.text(0.05, 0.9, 'm-TiO$_2$+ PVSK', transform=ax.transAxes, fontsize=12, bbox=dict(facecolor='white', edgecolor='black'))

# Styling
ax.set_xlabel('Time (ns)', fontsize=14)
ax.set_ylabel('Nor. intensity', fontsize=14)
ax.set_yscale('log')
ax.set_ylim(0.04, 1.2)
ax.set_xlim(0, 25)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='in', top=True, right=True, which='both')

plt.tight_layout()
plt.show()
