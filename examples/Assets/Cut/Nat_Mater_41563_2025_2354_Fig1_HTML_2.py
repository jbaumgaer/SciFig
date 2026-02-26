import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
two_theta = np.linspace(40, 76, 1000)

def lorentzian(x, center, width, height):
    return height * (width**2 / ((x - center)**2 + width**2))

# Background
bg = 1e3

# Sample 1: PC (Blue, Bottom)
# NSTO (Substrate): Very sharp
y_pc = bg + lorentzian(two_theta, 46.5, 0.1, 5e4) + lorentzian(two_theta, 72.5, 0.15, 4e4)
# KNN-C (Cubic): Broader
y_pc += lorentzian(two_theta, 45.8, 0.5, 1.5e4) + lorentzian(two_theta, 71.5, 0.6, 1e4)

# Sample 2: IM-PNR (Red, Top)
# NSTO
y_im = bg + lorentzian(two_theta, 46.5, 0.1, 5e4) + lorentzian(two_theta, 72.5, 0.15, 4e4)
# KNN-M (Monoclinic/Mixed): Split peaks
y_im += lorentzian(two_theta, 45.2, 0.4, 1.2e4) # KNN-T?
y_im += lorentzian(two_theta, 46.0, 0.3, 1.5e4) # KNN-M
y_im += lorentzian(two_theta, 70.0, 0.5, 0.8e4) # KNN-T
y_im += lorentzian(two_theta, 71.8, 0.4, 1.2e4) # KNN-M

# Log scale effect simulation (just adding noise and ensuring positive)
y_pc += np.random.normal(0, 100, len(two_theta))
y_im += np.random.normal(0, 100, len(two_theta))

# Offset for stacking
offset = 1e5
y_im_shifted = y_im + offset

# --- Plotting ---
fig, ax = plt.subplots(figsize=(8, 4), dpi=150)

# Plot
ax.plot(two_theta, y_im_shifted, color='#990033', lw=1.5)
ax.plot(two_theta, y_pc, color='#336699', lw=1.5)

# Labels and Text
# IM-PNR
ax.text(53, offset + 5e3, 'IM-PNR', color='#990033', fontsize=12)
# PC
ax.text(53, 2e4, 'PC', color='#336699', fontsize=12)

# Peak Labels
# Top
ax.text(47, offset + 6e4, '(002)$_c$', color='#cc3300', fontsize=12)
ax.text(72, offset + 5e4, '(003)$_c$', color='#cc3300', fontsize=12)
ax.text(47.5, offset + 2e4, 'NSTO', rotation=-90, color='#333333', fontsize=10)
ax.text(43.5, offset + 2e4, 'KNN-T', rotation=-90, color='#993333', fontsize=10)
ax.text(45.5, offset + 4e4, 'KNN-M', rotation=-90, color='#993333', fontsize=10)

# Bottom
ax.text(48, 2e4, 'NSTO', rotation=-90, color='#336699', fontsize=10)
ax.text(46, 1.8e4, 'KNN-C', rotation=-90, color='#336699', fontsize=10)


# Styling
ax.set_xlabel(r'2$	heta$ (°)', fontsize=14)
ax.set_ylabel('Intensity (a.u.)', fontsize=14)
ax.set_xlim(40, 76)
ax.set_yscale('log') # Log scale
ax.set_yticks([]) # Hide y ticks
ax.minorticks_on()
ax.tick_params(direction='in', which='both', top=True, right=True)

plt.tight_layout()
plt.show()
