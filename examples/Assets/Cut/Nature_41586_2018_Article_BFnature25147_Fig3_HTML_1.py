import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
energy = np.linspace(2.554, 2.564, 200)

def peak(x, center, width, height):
    return height / (1 + ((x - center)/width)**2)

# Peaks
# Main peak (Grey)
y_main = peak(energy, 2.5565, 0.0005, 0.95)
# Side peak (Red)
y_side = peak(energy, 2.558, 0.0003, 0.45)
# Small bump (Blue)
y_bump = peak(energy, 2.5585, 0.0008, 0.05)

# Total fit
y_fit = y_main + y_side + y_bump
# Noisy data
y_data = y_fit + np.random.normal(0, 0.03, len(energy))
y_data = np.maximum(0, y_data) # Non-negative

# --- Plotting ---
fig = plt.figure(figsize=(6, 5), dpi=150)

# Main Plot
ax = fig.add_axes([0.15, 0.15, 0.6, 0.7])
ax.scatter(energy[::2], y_data[::2], facecolors='none', edgecolors='black', s=20)
ax.plot(energy, y_fit, color='gray', lw=1)

# Filled components
ax.fill_between(energy, 0, y_main, color='lightgray', alpha=0.5)
ax.plot(energy, y_side, color='#CC3333', lw=1.5)
ax.plot(energy, y_bump, color='#334488', lw=1.5)

ax.set_xlabel('Energy (eV)', fontsize=14)
ax.set_ylim(-0.05, 1.05)
ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
ax.set_xlim(2.554, 2.564)
ax.tick_params(direction='in', top=True, right=True)

# Polar Inset
ax_ins = fig.add_axes([0.55, 0.55, 0.35, 0.35], projection='polar')
theta = np.linspace(0, 2*np.pi, 100)
# Grey lobes (Dipole along ~70 deg)
r_grey = 0.8 * (np.cos(theta - np.deg2rad(70))**2 + 0.2) + 0.1*np.random.normal(0,0.1,len(theta))
# Red lobes (Dipole along 0/180)
r_red = 0.3 * (np.cos(theta)**2) * (np.abs(np.cos(theta)) > 0.5)
# Blue lobes (Dipole along 90/270)
r_blue = 0.2 * (np.sin(theta)**2) * (np.abs(np.sin(theta)) > 0.5)

ax_ins.fill(theta, r_grey, color='lightgray', alpha=0.8, edgecolor='black')
ax_ins.fill(theta, r_red, color='#CC3333', alpha=0.8)
ax_ins.fill(theta, r_blue, color='#334488', alpha=0.8)

# Styling Polar
ax_ins.set_xticks(np.deg2rad([0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]))
ax_ins.set_xticklabels(['0', '30', '60', '90', '120', '150', '180', '210', '240', '270', '300', '330'], fontsize=8)
ax_ins.set_yticklabels([])
ax_ins.grid(True, linestyle=':')

plt.show()
