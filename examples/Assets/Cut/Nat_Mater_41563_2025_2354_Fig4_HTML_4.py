import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
voltage = np.array([0, 15, 30, 45, 60, 70])

# Top Panel
# c_T (Left Axis, Blue squares)
c_t = 4.02 + 0.0006 * voltage
# c_M (Right Axis, Red squares)
c_m = 3.945 + 0.0005 * voltage

# Bottom Panel
# Calculated Strain
strain = 0.0 + 0.016 * voltage # Linear approx to 1.16% at 70V

# --- Plotting ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 8), dpi=150, sharex=True, gridspec_kw={'height_ratios': [1, 1.2], 'hspace': 0})

# --- Top Panel ---
# Left Axis (Blue)
color_blue = '#336699'
ax1.plot(voltage, c_t, 's-', color=color_blue, markersize=8, label='c$_T$')
ax1.set_ylabel(r'c$_T$ ($\AA$)', color=color_blue, fontsize=14)
ax1.tick_params(axis='y', labelcolor=color_blue)
ax1.set_ylim(4.015, 4.075)

# Arrow
ax1.annotate('', xy=(0, 4.035), xytext=(10, 4.035), arrowprops=dict(arrowstyle='->', color=color_blue, lw=3))

# Right Axis (Red)
ax1r = ax1.twinx()
color_red = '#990033'
ax1r.plot(voltage, c_m, 's-', color=color_red, markersize=8, label='c$_M$')
ax1r.set_ylabel(r'c$_M$ ($\AA$)', color=color_red, fontsize=14, rotation=270, labelpad=20)
ax1r.tick_params(axis='y', labelcolor=color_red)
ax1r.set_ylim(3.935, 4.005)

# Arrow
ax1r.annotate('', xy=(70, 3.98), xytext=(60, 3.98), arrowprops=dict(arrowstyle='->', color=color_red, lw=3))

# Legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax1r.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, frameon=False, loc='upper left', ncol=2)


# --- Bottom Panel ---
color_purple = '#665599'
# Shaded background
ax2.set_facecolor('#E6E0E6')
# Dashed line fit
ax2.plot(voltage, strain, '--', color=color_purple, lw=2)
# Points
# Gradient spheres
ax2.scatter(voltage, strain, s=100, c=strain, cmap='Purples', edgecolors='white', zorder=5)

ax2.set_ylabel('Calculated strain (%)', color=color_purple, fontsize=14)
ax2.set_xlabel('Voltage (V)', fontsize=14)
ax2.set_ylim(-0.2, 1.8)

# Big Arrow
ax2.arrow(18, 1.8, 0, -1.0, width=3, head_width=8, head_length=0.4, color='#9988AA', alpha=0.8, length_includes_head=True)

# Text
ax2.text(60, 1.4, '1.16%', color='#443366', fontsize=12)

# Ticks
ax1.tick_params(direction='in', top=True)
ax2.tick_params(direction='in', top=True, right=True)

plt.show()
