import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# --- Data Simulation ---
# Grid
x = np.linspace(-10, 10, 100)
y = np.linspace(-10, 10, 100)
X, Y = np.meshgrid(x, y)

def c_shape(x, y, angle_deg):
    # Rotate coordinates
    rad = np.deg2rad(angle_deg)
    xr = x * np.cos(rad) - y * np.sin(rad)
    yr = x * np.sin(rad) + y * np.cos(rad)
    
    # C-shape: Ring segment
    r = np.sqrt(xr**2 + yr**2)
    theta = np.arctan2(yr, xr)
    
    # Gaussian Ring
    ring = np.exp(-((r - 4)**2)/4)
    # Angular cut (Gap at angle 0)
    gap = (np.cos(theta) < 0.5) # Keep left side
    # Smooth gap
    angular_mod = np.exp(-((theta)**2)/0.5) # Gap at 0
    # Actually keep intensity away from 0
    angular_mod = 1 - 0.8 * np.exp(-((theta)**2)/1.0)
    
    return ring * angular_mod

# 4 Orientations
Z1 = c_shape(X, Y, 90)  # Gap up? Image 1: Gap top
Z2 = c_shape(X, Y, 180) # Gap left
Z3 = c_shape(X, Y, 270) # Gap down
Z4 = c_shape(X, Y, 0)   # Gap right

# --- Plotting ---
fig, axes = plt.subplots(1, 4, figsize=(12, 3), dpi=150)
plt.subplots_adjust(wspace=0.05)

# Custom Colormap: Yellow-White-Blue-Black
colors = ['#FFFFDD', '#FFEEAA', '#4466AA', '#000000']
cmap = LinearSegmentedColormap.from_list('custom', colors)

for ax, Z in zip(axes, [Z1, Z2, Z3, Z4]):
    ax.imshow(Z, cmap=cmap, origin='lower', extent=[-10, 10, -10, 10])
    ax.axis('off')

# Scale Bar on first
axes[0].plot([-8, -3], [-8, -8], color='#BB9955', lw=4)
axes[0].text(-5.5, -6.5, '5 $\AA$', color='#BB9955', ha='center', fontweight='bold', fontsize=14)

# Colorbar text on last
axes[-1].text(12, 8, 'Hi', fontweight='bold', fontsize=14)
axes[-1].text(12, -8, 'Lo', fontweight='bold', fontsize=14)
# Draw gradient bar manually
grad = np.linspace(0, 1, 100).reshape(-1, 1)
ax_cbar = axes[-1].inset_axes([1.1, 0.2, 0.1, 0.6])
ax_cbar.imshow(grad, cmap=cmap, aspect='auto')
ax_cbar.axis('off')

plt.show()
