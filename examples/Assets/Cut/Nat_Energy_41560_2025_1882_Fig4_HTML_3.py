import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Literature Data (Voc, PCE)
# Roughly digitizing from image
voc = [1.14, 1.15, 1.155, 1.165, 1.17, 1.173, 1.175, 1.175, 1.178, 1.188, 1.19, 1.192, 1.192, 1.194]
pce = [25.0, 25.0, 25.8, 25.85, 26.1, 26.15, 24.6, 25.7, 25.3, 25.4, 26.6, 24.5, 25.6, 25.85]
labels = ['24', '12', '3', '44', '45', '11', '39', '43', '40', '41', '46', '4', '42', '13']

# This work
this_voc = 1.195
this_pce = 26.9

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# Literature
ax.scatter(voc, pce, s=100, color='#330066', edgecolors='white', zorder=2)
# Sphere effect (gradient) simulated by overlay
ax.scatter(voc, pce, s=20, color='#9966CC', edgecolors='none', zorder=3, alpha=0.5)

# Labels
for x, y, l in zip(voc, pce, labels):
    ax.text(x, y-0.25, f'Ref.$^{{{l}}}$', ha='center', fontsize=10)
    # Draw line for some crowded ones?
    # Simplified: just placing text below

# This work
ax.scatter(this_voc, this_pce, s=300, marker='*', color='#AA4433', edgecolors='white', zorder=4)
ax.text(this_voc, this_pce + 0.2, 'This work', color='#AA4433', fontsize=14, ha='center')

# Styling
ax.set_xlabel(r'$V_{\mathrm{OC}}$ (V)', fontsize=14)
ax.set_ylabel('PCE (%)', fontsize=14)
ax.set_xlim(1.135, 1.20)
ax.set_ylim(24, 27.2)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='out', top=False, right=False)

plt.tight_layout()
plt.show()
