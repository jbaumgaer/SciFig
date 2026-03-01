import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

# --- Data Simulation ---
# Literature
# Quantum dots
x_qd = [50]
y_qd = [4]
# Fluorescence
x_fl = [55, 70, 80, 100]
y_fl = [1, 3.5, 7, 4.5]
# TADF
x_tadf = [120]
y_tadf = [10]
# Phosphorescence
x_ph = [100]
y_ph = [7]

# This work
x_this = [200]
y_this = [22]

# --- Plotting ---
fig, ax = plt.subplots(figsize=(5, 5), dpi=150)

# Scatter
ax.scatter(x_qd, y_qd, color='#335577', s=80, label='Quantum dots')
ax.scatter(x_fl, y_fl, color='#CCCCCC', s=80, label='Fluorescence')
ax.scatter(x_tadf, y_tadf, color='#009999', s=80, label='TADF')
ax.scatter(x_ph, y_ph, color='#116633', s=80, label='Phosphorescence')

# This work
ax.scatter(x_this, y_this, marker='*', s=400, color='#116633', label='_nolegend_')
ax.text(200, 24, 'This work', ha='center', fontsize=14)

# Ellipse
el = Ellipse((85, 5.5), 120, 12, angle=30, facecolor='#FFFDF5', edgecolor='gray', linestyle='--', lw=1.5, zorder=0)
ax.add_patch(el)

# Legend
ax.legend(frameon=False, loc='upper left', fontsize=12, handletextpad=0.1)

# Styling
ax.set_xlabel('Crack onset strain (%)', fontsize=14)
ax.set_ylabel('EQE (%)', fontsize=14)
ax.set_xlim(0, 220)
ax.set_ylim(0, 25)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='out', top=False, right=False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.show()
