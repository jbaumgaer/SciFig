import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Axes: Raman coupling Omega vs Magnetic Field B
omega = np.linspace(0, 3.5, 100)
b_field = np.linspace(51.25, 51.95, 100)
O, B = np.meshgrid(omega, b_field)

# Transition Boundary
# B = 51.3 + 0.1 * exp(omega) or similar sigmoid
# Visual fit from image: B starts low at omega=0.5, rises to 51.9 at omega=3
# Use a logistic or tanh function
# Center around omega=1.5, B=51.5?
boundary_B = 51.3 + 0.6 / (1 + np.exp(-2.5 * (omega - 1.8)))

# Contrast C Calculation
# High contrast (purple) above/left of boundary? No, looks like transition region
# Image: White on bottom-left, Purple on top-right, separated by dashed line?
# Actually, it looks like:
# Low contrast (white/blue) for B < boundary
# High contrast (purple) for B > boundary?
# Let's assume Contrast depends on distance from boundary
dist = B - (51.3 + 0.6 / (1 + np.exp(-2.5 * (O - 1.8))))
# Contrast is high when B is slightly above the curve?
contrast = 0.8 / (1 + np.exp(-10 * dist))
# Mask: Contrast is 0 if B < boundary (approx)
# The image shows the boundary line itself.
# Let's just make a smooth gradient from bottom-right to top-left?
# No, looks like distinct phase transition.
# Let's set contrast proportional to B but modulated by Omega

# Refined Simulation
# Dashed line is the phase boundary.
# Top-right region (above line) has color (Purple).
# Bottom-left region (below line) is white/light blue.
contrast = 0.7 * (1 / (1 + np.exp(-15 * (B - (51.25 + 0.65 / (1 + np.exp(-2.0 * (O - 1.5))))))))

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# Heatmap
# BuPu (Blue-Purple)
cmap = plt.cm.BuPu
im = ax.imshow(contrast, extent=[0, 3.5, 51.25, 51.95], origin='lower', aspect='auto', cmap=cmap, vmin=0, vmax=0.75)

# Boundary Line (Dashed)
boundary_line_y = 51.25 + 0.65 / (1 + np.exp(-2.0 * (omega - 1.5)))
ax.plot(omega, boundary_line_y, color='#555555', linestyle='--', linewidth=2.5)

# Horizontal Cuts (Experimental paths)
y_cuts = [51.52, 51.76, 51.84]
colors = ['#2b3a4f', '#566981', '#9eadc4']
for y, col in zip(y_cuts, colors):
    ax.axhline(y, color=col, linewidth=2)

# Colorbar
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label('Contrast $C$', fontsize=14)
cbar.set_ticks([0.00, 0.75])

# Styling
ax.set_xlabel(r'Raman coupling $\Omega$ ($E_{m R}/\hbar$)', fontsize=14)
ax.set_ylabel(r'Magnetic field $B$ (G)', fontsize=14)
ax.set_xlim(0, 3.5)
ax.set_ylim(51.25, 51.95)

# Ticks
ax.set_xticks([0, 2])
ax.set_yticks([51.4, 51.6, 51.8])
ax.tick_params(direction='in', top=True, right=True, width=1.5)
for spine in ax.spines.values():
    spine.set_linewidth(1.5)

plt.tight_layout()
plt.show()
