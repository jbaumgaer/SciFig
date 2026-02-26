import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Control (Light Blue)
mu_dc_c = 65
mu_eh_c = 10
Ld_c = 4.5

# Dipolar (Dark Blue)
mu_dc_d = 115
mu_eh_d = 18
Ld_d = 5.8

labels = [r'$\mu_{m dc}$', r'$\mu_{e,h}$', r'$L_{m d}$']
x = np.arange(len(labels))
width = 0.25

# --- Plotting ---
fig, ax1 = plt.subplots(figsize=(6, 5), dpi=150)

# Colors
c_ctrl = '#77AADD'
c_dip = '#115599'

# Plot Left Axis Data (Mobility) - Indices 0 and 1
ax1.bar(x[0] - width/2, mu_dc_c, width, color=c_ctrl, edgecolor='black', label='Control')
ax1.bar(x[0] + width/2, mu_dc_d, width, color=c_dip, edgecolor='black', label='Dipolar passivation')

ax1.bar(x[1] - width/2, mu_eh_c, width, color=c_ctrl, edgecolor='black')
ax1.bar(x[1] + width/2, mu_eh_d, width, color=c_dip, edgecolor='black')

# Right Axis (Diffusion Length) - Index 2
ax2 = ax1.twinx()
ax2.bar(x[2] - width/2, Ld_c, width, color=c_ctrl, edgecolor='black')
ax2.bar(x[2] + width/2, Ld_d, width, color=c_dip, edgecolor='black')

# Axis Labels
ax1.set_ylabel(r'Mobility (cm$^2$ V$^{-1}$ s$^{-1}$)', fontsize=14)
ax2.set_ylabel(r'Diffusion length ($\mu$m)', fontsize=14)
ax1.set_ylim(0, 130)
ax2.set_ylim(0, 9)

# X Ticks
# The labels are actually placed above the bars in the image with arrows
# I'll reproduce the labels as annotations and remove x-tick labels to match style roughly
ax1.set_xticks([]) 

# Annotations
ax1.annotate(r'$\mu_{m dc}$', xy=(0, 115), xytext=(-0.5, 115), arrowprops=dict(arrowstyle='->'), fontsize=14)
ax1.annotate(r'$\mu_{e,h}$', xy=(1, 20), xytext=(0.5, 20), arrowprops=dict(arrowstyle='->'), fontsize=14)
ax2.annotate(r'$L_{m d}$', xy=(2, 6), xytext=(2.5, 6), arrowprops=dict(arrowstyle='->'), fontsize=14)

# Legend
ax1.legend(loc='upper right', fontsize=12, frameon=False)

plt.tight_layout()
plt.show()
