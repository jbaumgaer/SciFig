import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
wavelengths = np.linspace(900, 1200, 300)

# Gaussian peak generator
def gaussian(x, center, width, height):
    return height * np.exp(-((x - center)**2) / (2 * width**2))

# Control (Light Blue)
# Peak around 1010 nm, lower intensity
y_control = gaussian(wavelengths, 1010, 40, 0.45)

# Dipolar Passivation (Dark Blue)
# Peak around 1010 nm, higher intensity (~2.5x)
y_dipolar = gaussian(wavelengths, 1010, 40, 0.95)

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# Plot curves
ax.plot(wavelengths, y_control, color='#87CEEB', linewidth=2.5, label='Control') # SkyBlue
ax.plot(wavelengths, y_dipolar, color='#1E5AA0', linewidth=2.5, label='Dipolar passivation') # Dark Blue

# Styling
ax.set_xlabel('Wavelength (nm)', fontsize=14)
ax.set_ylabel('Intensity (normalized)', fontsize=14)
ax.set_xlim(900, 1200)
ax.set_ylim(0, 1.1)

# Ticks
ax.tick_params(direction='out', labelsize=12)
ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
ax.set_yticklabels(['', '', '', '', '', '']) # Hide y-values as it is normalized/arbitrary

# Legend
ax.legend(frameon=False, fontsize=12, loc='upper left')

# Inset Schematic (Simplified)
# Using inset_axes or just drawing rectangles
ax_ins = ax.inset_axes([0.65, 0.75, 0.3, 0.2], transform=ax.transAxes)
ax_ins.axis('off')

# Layers
rect_sub = plt.Rectangle((0, 0), 1, 0.3, color='#D0E0F0', ec='none') # Substrate
rect_perov = plt.Rectangle((0, 0.3), 1, 0.4, color='#FA8072', ec='none') # Perovskite (Salmon)
ax_ins.add_patch(rect_sub)
ax_ins.add_patch(rect_perov)

# Text labels
ax_ins.text(0.5, 0.5, 'Perovskite', ha='center', va='center', fontsize=10)
ax_ins.text(0.5, 0.15, 'Substrate', ha='center', va='center', fontsize=10)

# Arrows
ax.annotate('Excite', xy=(0.78, 0.77), xytext=(0.70, 0.65), xycoords='axes fraction',
            arrowprops=dict(arrowstyle='->', color='black', lw=1.5), fontsize=10, ha='center')
ax.annotate('Probe', xy=(0.88, 0.77), xytext=(0.96, 0.65), xycoords='axes fraction',
            arrowprops=dict(arrowstyle='->', color='black', lw=1.5), fontsize=10, ha='center')

plt.tight_layout()
plt.show()
