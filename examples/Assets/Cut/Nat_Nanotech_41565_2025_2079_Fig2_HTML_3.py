import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
q = np.linspace(1.23, 1.47, 300)

def gaussian(x, center, width, height):
    return height * np.exp(-((x - center)**2) / (2 * width**2))

# Top (Blue)
y_blue = gaussian(q, 1.32, 0.015, 1.0) + 0.1

# Middle (Red)
y_red = gaussian(q, 1.325, 0.015, 1.0) + 0.1

# Bottom (Grey)
y_grey = gaussian(q, 1.38, 0.015, 1.0) + 0.1

# Offset
y_red += 1.5
y_blue += 3.0

# --- Plotting ---
fig, ax = plt.subplots(figsize=(4, 6), dpi=150)

# Plots
ax.plot(q, y_blue, color='#4488EE', lw=2)
ax.plot(q, y_red, color='#FF6666', lw=2)
ax.plot(q, y_grey, color='#555555', lw=2)

# Dashed vertical lines
ax.vlines(1.32, 1.5, 4.2, linestyles='--', colors='#006688', lw=2)
ax.vlines(1.38, 0.2, 2.8, linestyles='--', colors='#006688', lw=2)

# Labels
ax.text(1.24, 3.5, '1 C, 4.5 V
SoC, 78%', fontsize=10)
ax.text(1.24, 2.0, '0.1 C, 4.2 V
SoC, 78%', fontsize=10)
ax.text(1.24, 0.5, '0.1 C, 4.5 V
SoC, 91%', fontsize=10)

ax.annotate('SoC-dependent phase', xy=(1.33, 3.8), xytext=(1.35, 4.3), arrowprops=dict(arrowstyle='->', color='#444444'))

# Styling
ax.set_xlabel(r'$Q$ ($\AA^{-1}$)', fontsize=14)
ax.set_ylabel('Intensity (a.u.)', fontsize=14)
ax.set_xticks([1.25, 1.30, 1.35, 1.40, 1.45])
ax.set_yticks([])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.show()
