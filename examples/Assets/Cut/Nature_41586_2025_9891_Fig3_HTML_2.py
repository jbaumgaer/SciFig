import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Axes
inv_dv = np.linspace(0, 50, 100)
phi_db = np.linspace(-1.0, 1.0, 100)
X, Y = np.meshgrid(inv_dv, phi_db)

# Peaks
Z = np.zeros_like(X)
# Bright spot at ~15, -0.7
Z += 1.0 * np.exp(-((X - 15)**2)/10 - ((Y + 0.7)**2)/0.01)
# Some weak lines
Z += 0.2 * np.exp(-((Y - 0.7)**2)/0.01) # Horizontal line at +0.7?
Z += 0.1 * np.exp(-((Y - 0)**2)/0.005) # Center line
# Vertical streak
Z += 0.1 * np.exp(-((X - 5)**2)/2) * np.exp(-((Y)**2)/0.5)

# Add noise
Z += np.random.normal(0, 0.05, Z.shape)
Z = np.abs(Z) # Magnitude

# --- Plotting ---
fig, ax = plt.subplots(figsize=(5, 5), dpi=150)

# Heatmap
# Copper / pinkish
cmap = plt.cm.pink_r # Or 'copper'
im = ax.imshow(Z, extent=[0, 50, -1.0, 1.0], aspect='auto', cmap=cmap, origin='lower', vmin=0, vmax=1.0)

# Colorbar
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label('|FFT| (a.u.)', fontsize=12)
cbar.set_ticks([0, 1])

# Dashed line at 0
ax.axhline(0, color='gray', linestyle='--')

# Text
ax.text(25, 0.7, r'$\Phi_0/\Delta B = -0.70$ $\mu$m$^2$', color='black', ha='center', fontsize=12)

# Styling
ax.set_xlabel(r'1/$\Delta V_{m PG}$ (V$^{-1}$)', fontsize=14)
ax.set_ylabel(r'$\Phi_0/\Delta B$ ($\mu$m$^2$)', fontsize=14)
ax.set_xlim(0, 50)
ax.set_ylim(-1.0, 1.0)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='out', top=False, right=False)

plt.tight_layout()
plt.show()
