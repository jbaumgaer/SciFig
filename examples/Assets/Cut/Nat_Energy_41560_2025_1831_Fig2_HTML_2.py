import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
cycles = np.linspace(0, 140, 70)

# Capacity (Left Axis)
# NT-NCM (Red): 1200 -> 1080 (90%)
cap_nt = 1200 - 0.8 * cycles
# P-NCM (Blue): 1180 -> 930 (rapid drop then steady)
cap_p = 1180 - 1.8 * cycles
# Add noise/steps
cap_p += np.random.normal(0, 5, len(cycles))

# Coulombic Efficiency (Right Axis)
# Stable near 100%
ce_nt = np.ones_like(cycles) * 100 + np.random.normal(0, 0.1, len(cycles))
ce_p = np.ones_like(cycles) * 100 + np.random.normal(0, 0.1, len(cycles))

# --- Plotting ---
fig, ax1 = plt.subplots(figsize=(8, 4), dpi=150)

# Left Axis: Capacity
ax1.plot(cycles, cap_nt, 's', color='white', markeredgecolor='#FF6666', markersize=5, label='NT-NCM', mew=1.5)
ax1.plot(cycles, cap_p, 's', color='white', markeredgecolor='#4488CC', markersize=5, label='P-NCM', mew=1.5)
ax1.set_xlabel('Cycle number', fontsize=14)
ax1.set_ylabel('Cell capacity (mAh)', fontsize=14)
ax1.set_ylim(0, 1600)
ax1.set_xlim(0, 140)

# Right Axis: CE
ax2 = ax1.twinx()
ax2.plot(cycles, ce_nt, 'o', color='white', markeredgecolor='#FF6666', markersize=5, mew=1.5)
ax2.plot(cycles, ce_p, 'o', color='white', markeredgecolor='#4488CC', markersize=5, mew=1.5)
ax2.set_ylabel('Coulombic efficiency (%)', fontsize=14, rotation=270, labelpad=20)
ax2.set_ylim(0, 110)

# Annotations
ax1.axvline(100, color='black', linestyle=':')
ax1.text(100, 1150, '93.9%', ha='right', va='bottom')
ax1.annotate('', xy=(100, 1150), xytext=(90, 1150), arrowprops=dict(arrowstyle='->'))

ax1.text(140, 1050, '90.2%', ha='right', va='bottom')
ax1.annotate('', xy=(140, 1050), xytext=(130, 1050), arrowprops=dict(arrowstyle='->'))

# Arrows pointing to axes
ax1.annotate('', xy=(5, 1000), xytext=(15, 1000), arrowprops=dict(arrowstyle='->', color='#555555', lw=1.5))
ax2.annotate('', xy=(135, 95), xytext=(125, 95), arrowprops=dict(arrowstyle='->', color='#555555', lw=1.5))

# Text
ax1.text(5, 50, '1 C, 2.8–4.5 V versus graphite, RT (pouch-type full cell)', fontsize=12, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

# Inset Image Placeholder
ax_ins = ax1.inset_axes([0.2, 0.3, 0.25, 0.4])
ax_ins.text(0.5, 0.5, '[Pouch Cell
Photo]', ha='center', va='center')
ax_ins.set_xticks([])
ax_ins.set_yticks([])
ax_ins.set_facecolor('#EEEEEE')

# Legend
# Create custom legend handles to match style
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='s', color='w', markeredgecolor='#FF6666', label='NT-NCM', markersize=6, mew=1.5),
    Line2D([0], [0], marker='o', color='w', markeredgecolor='#FF6666', markersize=6, mew=1.5), # CE
    Line2D([0], [0], marker='s', color='w', markeredgecolor='#4488CC', label='P-NCM', markersize=6, mew=1.5),
    Line2D([0], [0], marker='o', color='w', markeredgecolor='#4488CC', markersize=6, mew=1.5)
]
# Simplified Legend
ax1.legend(handles=[legend_elements[0], legend_elements[2]], loc='lower right', bbox_to_anchor=(0.95, 0.2), frameon=False, fontsize=12)

plt.tight_layout()
plt.show()
