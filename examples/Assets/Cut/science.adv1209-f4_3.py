import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
omega_coupling = np.linspace(0, 2.5, 100)
# Blue curve (Soft mode) - drops to zero at critical point ~2.05
freq_blue = 0.6 * np.sqrt(np.maximum(0, 1 - (omega_coupling / 2.05)**2))
# Red curve (Another mode) - decreases slowly
freq_red = 1.0 - 0.08 * omega_coupling

# Data points
x_data = np.linspace(0, 2.1, 8)
y_data_blue = 0.6 * np.sqrt(np.maximum(0, 1 - (x_data / 2.05)**2)) + np.random.normal(0, 0.02, len(x_data))
y_data_red = 1.0 - 0.08 * x_data + np.random.normal(0, 0.01, len(x_data))

# --- Plotting Main ---
fig, ax = plt.subplots(figsize=(7, 6), dpi=150)

# Main Curves
ax.plot(omega_coupling, freq_blue, color='#3e6082', lw=2)
ax.plot(omega_coupling, freq_red, color='#b06060', lw=2)
# Data Points
ax.plot(x_data, y_data_blue, 'o', color='#7aa0c4', markeredgecolor='#3e6082', markersize=10, mew=1.5)
ax.plot(x_data, y_data_red, 's', color='#d08080', markeredgecolor='#b06060', markersize=10, mew=1.5)

# Vertical dashed line
ax.axvline(2.05, color='black', linestyle='--')

# Styling
ax.set_xlabel(r'Raman coupling $\Omega$ ($E_{m R}/\hbar$)', fontsize=14)
ax.set_ylabel(r'Frequency $\omega$ ($\omega_x$)', fontsize=14)
ax.set_xlim(0, 2.5)
ax.set_ylim(0, 1.05)
ax.tick_params(direction='in', top=True, right=True)

# --- Insets (Oscillations) ---
# We need 3 insets at the bottom
# 1. Omega ~ 0
ins1 = ax.inset_axes([0.05, -0.4, 0.25, 0.3], transform=ax.transAxes)
t = np.linspace(0, 20, 40)
y1 = 2.0 + 0.2 * np.sin(t) + np.random.normal(0, 0.05, len(t))
ins1.plot(t, y1, 'o-', color='#7aa0c4', mec='#3e6082')
ins1.set_ylabel(r'$\hbar \Delta k (\hbar k_{m R})$')
ins1.set_xlabel('Time (ms)')

# 2. Omega ~ 1.0
ins2 = ax.inset_axes([0.375, -0.4, 0.25, 0.3], transform=ax.transAxes)
y2 = 1.8 + 0.15 * np.sin(t * 0.8) + np.random.normal(0, 0.05, len(t)) # Slower
ins2.plot(t, y2, 'o-', color='#7aa0c4', mec='#3e6082')
ins2.set_xlabel('Time (ms)')
ins2.set_yticklabels([])

# 3. Omega ~ 2.0 (Critical)
ins3 = ax.inset_axes([0.7, -0.4, 0.25, 0.3], transform=ax.transAxes)
y3 = 1.6 + 0.1 * np.exp(-t/5) * np.sin(t * 0.5) + np.random.normal(0, 0.1, len(t)) # Damped/Noisy
ins3.errorbar(t, y3, yerr=0.1, fmt='o', color='#7aa0c4', ecolor='#3e6082')
ins3.set_xlabel('Time (ms)')
ins3.set_yticklabels([])

# Connecting lines (Grey triangles)
# Just simple polygons to suggest zoom
# poly1 = plt.Polygon([[0, 0], [0.15, 0.55], [-0.1, 0]], color='lightgray', alpha=0.3, transform=ax.transAxes, clip_on=False)
# This is tricky to coordinate exactly without interactive tweaking. 
# I'll just use simple lines or skip the gray cones for simplicity as they cross axes.

plt.subplots_adjust(bottom=0.3)
plt.show()
