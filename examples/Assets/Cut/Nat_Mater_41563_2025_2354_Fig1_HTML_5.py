import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Axes
temp = np.linspace(430, 530, 100)
duration = np.linspace(20, 180, 100)
T, D = np.meshgrid(temp, duration)

# Function Z (Delta 2theta)
# Increases with both Temp and Duration
# Sigmoid transition from bottom-left (0) to top-right (high)
# "Diagonal" transition
z_val = 1.8 / (1 + np.exp(-0.1 * (T - 475 + 0.5*(D - 100)))) 
# Add some curvature
z_val = 1.8 * ( (T-430)/100 * (D-20)/160 )**1.5 
# Let's adjust to match visual: 
# Low (Blue) at (430-475, <100)
# Transition at diagonal
# High (Red) at (>500, >120)
diag_coord = (T - 430)/100 + (D - 20)/160
z_val = 1.8 * (diag_coord**2) / (0.5 + diag_coord**2) # Sigmoid-ish on diagonal


# --- Plotting ---
fig, ax = plt.subplots(figsize=(5, 4), dpi=150)

# Contourf
# RdBu_r
levels = np.linspace(0, 1.8, 20)
cmap = plt.cm.RdBu_r
cf = ax.contourf(T, D, z_val, levels=levels, cmap=cmap)

# Colorbar
cbar = fig.colorbar(cf, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label(r'$\Delta_{2	heta, \mathrm{M-T}}$ (°)', fontsize=14, rotation=270, labelpad=20)
cbar.set_ticks([0, 0.5, 0.9, 1.4, 1.8])

# Arrow
ax.arrow(465, 60, 40, 70, width=15, head_width=30, head_length=20, color='white', alpha=0.3, length_includes_head=True)
ax.text(480, 95, 'Local strain
fluctuation
enhanced', rotation=50, color='white', ha='center', va='center', fontsize=12)

# Labels
ax.text(435, 25, 'PC', color='white', fontsize=12)
ax.text(525, 170, 'IM-PNR', color='white', ha='right', fontsize=12)

# Styling
ax.set_xlabel('Pyrolysis temperature (°C)', fontsize=14)
ax.set_ylabel('Pyrolysis
duration (s)', fontsize=14)
ax.set_xlim(430, 530)
ax.set_ylim(20, 180)
ax.set_xticks([450, 475, 500, 525])
ax.set_yticks([30, 60, 90, 120, 150, 180])

# Ticks
ax.tick_params(direction='in', top=True, right=True)

plt.tight_layout()
plt.show()
