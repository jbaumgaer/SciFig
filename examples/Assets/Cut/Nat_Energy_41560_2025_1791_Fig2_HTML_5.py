import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
ppm = np.linspace(-77, -79, 500) # Reversed

def lorentzian(x, center, width, height):
    return height * (width**2 / ((x - center)**2 + width**2))

# Peak Center
center = -78.1

# 1. FIPA (Top)
y_fipa = lorentzian(ppm, center, 0.02, 10) + np.random.normal(0, 0.02, len(ppm))

# 2. PEAI/FIPA (Bottom)
y_mix = lorentzian(ppm, center+0.01, 0.02, 10) + np.random.normal(0, 0.02, len(ppm))

# Offset
y_fipa += 12

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# Plot
ax.plot(ppm, y_fipa, color='gray', lw=2)
ax.text(-77.8, 15, 'FIPA', fontsize=14)

ax.plot(ppm, y_mix, color='#005566', lw=2)
ax.text(-77.8, 5, 'PEAI/FIPA', fontsize=14)

# Styling
ax.set_xlabel('Chemical shift (ppm)', fontsize=14)
ax.set_xlim(-77, -79) # Reversed
ax.set_yticks([])
ax.set_ylim(-1, 25)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='out', top=False, right=False)

plt.tight_layout()
plt.show()
