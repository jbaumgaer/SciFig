import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Energy Spectrum
e = np.linspace(-5, 5, 200)
def gaussian(x, center, width, height):
    return height * np.exp(-((x - center)**2) / (2 * width**2))

y_grey = gaussian(e, -1.5, 0.8, 0.9)
y_red = gaussian(e, 0.5, 0.5, 0.35)
y_blue = gaussian(e, 2.5, 0.4, 0.15)

# --- Plotting ---
fig = plt.figure(figsize=(5, 4), dpi=150)

# Main Plot
ax = fig.add_axes([0.15, 0.15, 0.5, 0.7])
ax.plot(e, y_grey, color='black', lw=1)
ax.fill_between(e, 0, y_grey, color='lightgray', alpha=0.8)
ax.text(-1.5, 0.3, r'$|\Psi_xangle$', ha='center')

ax.plot(e, y_red, color='black', lw=1)
ax.fill_between(e, 0, y_red, color='#AA3333', alpha=0.9)
ax.text(0.5, 0.4, r'$|\Psi_yangle$', ha='center')

ax.plot(e, y_blue, color='black', lw=1)
ax.fill_between(e, 0, y_blue, color='#4466AA', alpha=0.9)
ax.text(2.5, 0.2, r'$|\Psi_zangle$', ha='center')

ax.set_xlabel('Energy', fontsize=12)
ax.set_ylim(0, 1.1)
ax.set_xticks([]) # No units
ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
ax.tick_params(direction='in', top=True, right=True)

# Polar Inset
ax_ins = fig.add_axes([0.6, 0.55, 0.35, 0.35], projection='polar')
theta = np.linspace(0, 2*np.pi, 100)
# Grey lobes (Vertical, Y-axis? Image has grey along ~75/255)
# Actually image says Psi_x is grey. In polar plot, grey is large lobes.
r_grey = 0.9 * (np.cos(theta - np.deg2rad(75))**2)
# Red lobes (Horizontal, X-axis?)
r_red = 0.3 * (np.cos(theta - np.deg2rad(0))**2)
# Blue lobes (Center)
r_blue = 0.15 * (np.ones_like(theta))

ax_ins.fill(theta, r_grey, color='lightgray', alpha=0.8, edgecolor='black')
ax_ins.fill(theta, r_red, color='#CC3333', alpha=0.8, edgecolor='black')
ax_ins.fill(theta, r_blue, color='#4466AA', alpha=0.8, edgecolor='black')

ax_ins.set_xticks(np.deg2rad([0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]))
ax_ins.set_xticklabels(['0', '30', '60', '90', '120', '150', '180', '210', '240', '270', '300', '330'], fontsize=8)
ax_ins.set_yticklabels([])
ax_ins.grid(True, linestyle=':')

plt.show()
