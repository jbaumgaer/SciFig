import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, ArrowStyle

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# Colors
col_blue = '#0099CC'
col_light = '#CCEEFF'

# Draw "Particles" (Blobs)
# Using FancyBboxPatch or Circle for simplicity
p1 = FancyBboxPatch((0.2, 0.6), 0.2, 0.2, boxstyle="round,pad=0.05", fc='#88CCEE', ec='gray', ls='--', lw=2)
p2 = FancyBboxPatch((0.6, 0.4), 0.2, 0.2, boxstyle="round,pad=0.05", fc='#0099CC', ec='gray', ls='--', lw=2)
p3 = FancyBboxPatch((0.2, 0.1), 0.2, 0.2, boxstyle="round,pad=0.05", fc='#BBDDFF', ec='gray', ls='--', lw=2)

ax.add_patch(p1)
ax.add_patch(p2)
ax.add_patch(p3)

# Bridges
ax.plot([0.4, 0.6], [0.7, 0.5], color='#CCEEFF', lw=15, zorder=0)
ax.plot([0.4, 0.6], [0.2, 0.5], color='#CCEEFF', lw=15, zorder=0)

# Labels
ax.text(0.7, 0.9, 'Fast equilibrium', color=col_blue, fontsize=12, ha='center')
ax.text(0.7, 0.85, 'SC-NC91', color='white', backgroundcolor=col_blue, fontsize=10, ha='center', bbox=dict(boxstyle='square,pad=0.3', fc=col_blue, ec='none'))

# Arrows (Flux)
# Using simple arrows
ax.arrow(0.15, 0.7, -0.05, 0.1, width=0.02, color='#CCEEFF')
ax.arrow(0.15, 0.2, -0.05, -0.1, width=0.02, color='#CCEEFF')

# Colorbar (SoC)
# Custom gradient bar
grad = np.linspace(0, 1, 100).reshape(1, -1)
ax_cbar = ax.inset_axes([0.6, 0.2, 0.25, 0.05])
ax_cbar.imshow(grad, cmap='Blues', aspect='auto')
ax_cbar.set_xticks([])
ax_cbar.set_yticks([])
ax_cbar.set_title('SoC', fontsize=10)
ax.text(0.6, 0.15, 'Low', ha='center')
ax.text(0.85, 0.15, 'High', ha='center')

# Styling
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

plt.tight_layout()
plt.show()
