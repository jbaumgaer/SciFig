import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
x = np.linspace(40, 60, 60)
y = np.linspace(40, 60, 60)
X, Y = np.meshgrid(x, y)

# Generate Blobs
Z = np.zeros_like(X) + np.random.normal(0, 10, X.shape) # Noise background

# Random blobs
np.random.seed(42)
num_blobs = 40
for _ in range(num_blobs):
    x0 = np.random.uniform(40, 60)
    y0 = np.random.uniform(40, 60)
    amp = np.random.uniform(50, 150)
    Z += amp * np.exp(-((X - x0)**2 + (Y - y0)**2) / (2 * 0.4**2))

# Highlighted Blob
target_x = 55
target_y = 49
Z += 120 * np.exp(-((X - target_x)**2 + (Y - target_y)**2) / (2 * 0.5**2))

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# Heatmap
cmap = plt.cm.RdBu_r
im = ax.imshow(Z, extent=[40, 60, 40, 60], origin='lower', cmap=cmap, vmin=-10, vmax=200)

# Colorbar
cbar = fig.colorbar(im, ax=ax, location='left', pad=0.15)
cbar.set_label('Intensity (a.u.)', fontsize=14)

# Circle Highlight
circle = plt.Circle((target_x, target_y), 1.2, color='#CC2200', fill=False, lw=3)
ax.add_patch(circle)

# Styling
ax.set_xlabel(r'$x$ position ($\mu$m)', fontsize=14)
ax.set_ylabel(r'$y$ position ($\mu$m)', fontsize=14, rotation=270, labelpad=20)
ax.yaxis.set_label_position("right")
ax.yaxis.tick_right()

# Ticks
ax.set_xticks([40, 45, 50, 55, 60])
ax.set_yticks([40, 45, 50, 55, 60])
ax.tick_params(direction='in', top=True, left=True)

plt.tight_layout()
plt.show()
