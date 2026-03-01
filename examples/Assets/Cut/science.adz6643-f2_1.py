import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# --- Data Simulation ---
# Size
size = 100
X, Y = np.meshgrid(np.linspace(0, 20, size), np.linspace(0, 20, size))

Z = np.zeros_like(X)

# Random Blobs
np.random.seed(42)
num_blobs = 60
for _ in range(num_blobs):
    x0 = np.random.uniform(1, 19)
    y0 = np.random.uniform(1, 19)
    # Pairs?
    if np.random.rand() > 0.6:
        # Create pair
        offset = 0.8
        angle = np.random.uniform(0, 2*np.pi)
        x1 = x0 + offset * np.cos(angle)
        y1 = y0 + offset * np.sin(angle)
        Z += np.exp(-((X - x1)**2 + (Y - y1)**2) / 0.3)

    Z += np.exp(-((X - x0)**2 + (Y - y0)**2) / 0.3)

# Background
Z += 0.1 * np.random.normal(0, 0.1, Z.shape)

# --- Plotting ---
fig, ax = plt.subplots(figsize=(5, 5), dpi=150)

# Colormap: Dark Blue to Yellow
# 'plasma' or 'viridis' is close, but let's make custom Blue-Yellow
colors = ['#000044', '#222288', '#CCCC44', '#FFFF00']
cmap = LinearSegmentedColormap.from_list('custom', colors)

im = ax.imshow(Z, cmap=cmap, origin='lower', extent=[0, 20, 0, 20])
ax.axis('off')

# Scale Bar
ax.plot([2, 7], [2, 2], color='gold', lw=3)
ax.text(4.5, 3, '5 nm', color='gold', ha='center', fontsize=14)

# Colorbar Text
ax.text(21, 18, 'Hi', fontsize=12)
ax.text(21, 2, 'Lo', fontsize=12)
# Bar
grad = np.linspace(0, 1, 100).reshape(-1, 1)
ax_cbar = ax.inset_axes([1.05, 0.2, 0.05, 0.6])
ax_cbar.imshow(grad, cmap=cmap, aspect='auto')
ax_cbar.axis('off')

plt.show()
