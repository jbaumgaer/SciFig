import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Axes: V_PG (Gate Voltage) vs B (Magnetic Field)
v_pg = np.linspace(2.5, 3.0, 100)
b_field = np.linspace(10.95, 11.05, 100)
V, B = np.meshgrid(v_pg, b_field)

# Quantum Oscillations Simulation
# Diagonal fringes: Phase depends on linear combination of V and B
# Frequency increases or decreases
phase = 200 * (V - 2.5) - 500 * (B - 10.95)
# Add some irregularity/noise
noise = np.random.normal(0, 0.2, V.shape)
delta_R = np.sin(phase) + 0.3 * np.sin(3 * phase) + noise

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# Heatmap
# RdBu_r colormap (Blue negative, Red positive)
cmap = plt.cm.RdBu_r
im = ax.pcolormesh(V, B, delta_R, cmap=cmap, shading='auto', vmin=-2, vmax=2)

# Colorbar
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label(r'$\Delta R_D$ (k$\Omega$)', fontsize=14)
cbar.set_ticks([-2, 0, 2])

# Styling
ax.set_xlabel(r'$V_{PG}$ (V)', fontsize=14)
ax.set_ylabel(r'$B$ (T)$|_{\alpha_c}$', fontsize=14)

# Ticks
ax.set_xticks([2.5, 3.0])
ax.set_yticks([10.95, 11.05])
ax.minorticks_on()
ax.tick_params(which='both', direction='out', top=True, right=True)

# Title annotation
ax.text(0.5, 1.02, r'$
u = -2/3$', transform=ax.transAxes, ha='center', fontsize=14)

# Bold letter 'c'
ax.text(-0.15, 1.0, 'c', transform=ax.transAxes, fontsize=16, fontweight='bold', va='top')

plt.tight_layout()
plt.show()
