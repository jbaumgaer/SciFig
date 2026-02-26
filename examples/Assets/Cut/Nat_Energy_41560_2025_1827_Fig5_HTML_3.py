import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
voltage = np.linspace(3.4, 4.5, 40)

# Volume (SC92) - Red
# Drops sharply
vol_sc92 = 102.0 - 0.5 * (voltage - 3.4)
mask_drop = voltage > 4.0
vol_sc92[mask_drop] = 101.7 - 18 * (voltage[mask_drop] - 4.0)**2
# Add curvature
vol_sc92 = np.maximum(92.5, vol_sc92)

# Volume (IBP-SC92) - Blue
# Drops less
vol_ibp = 102.2 - 0.4 * (voltage - 3.4)
vol_ibp[mask_drop] = 101.9 - 12 * (voltage[mask_drop] - 4.0)**2
vol_ibp = np.maximum(96.0, vol_ibp)

# --- Plotting ---
fig, ax = plt.subplots(figsize=(5, 5), dpi=150)

# SC92
ax.plot(voltage, vol_sc92, 'o-', color='#D64030', mfc='white', mew=2, label='SC92', markersize=8)
# IBP-SC92
ax.plot(voltage, vol_ibp, 'o-', color='#5B9BD5', mfc='white', mew=2, label='IBP-SC92', markersize=8)

# Annotations (Red)
ax.annotate('', xy=(3.45, 102), xytext=(3.45, 95.0), arrowprops=dict(arrowstyle='<->', color='#D64030'))
ax.annotate('', xy=(3.45, 95.0), xytext=(3.45, 92.5), arrowprops=dict(arrowstyle='<->', color='#D64030'))
ax.hlines(95.0, 3.4, 4.3, linestyles='--', colors='#D64030')
ax.hlines(92.5, 3.4, 4.5, linestyles='--', colors='#D64030')
ax.text(3.5, 95.2, r'7.09 $\AA^3$ ($\Delta V = 6.9\%$)', color='#D64030', fontsize=10)
ax.text(3.5, 92.7, r'9.47 $\AA^3$ ($\Delta V = 9.3\%$)', color='#D64030', fontsize=10)

# Annotations (Blue)
ax.annotate('', xy=(3.6, 102.2), xytext=(3.6, 96.1), arrowprops=dict(arrowstyle='<->', color='#5B9BD5'))
ax.hlines(96.1, 3.6, 4.5, linestyles='--', colors='#5B9BD5')
ax.text(3.65, 96.3, r'6.13 $\AA^3$ ($\Delta V = 5.9\%$)', color='#5B9BD5', fontsize=10)

# Styling
ax.set_xlabel('Voltage (V)', fontsize=14)
ax.set_ylabel(r'Volume ($\AA^3$)', fontsize=14)
ax.set_ylim(92, 103)
ax.set_xlim(3.35, 4.6)

# Legend
ax.legend(frameon=False, loc='upper right', fontsize=12)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='out', top=False, right=False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.show()
