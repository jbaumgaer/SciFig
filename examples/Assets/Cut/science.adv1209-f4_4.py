import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
omega = np.linspace(0, 2.5, 100)

# Critical points shifting
xc1 = 1.5
xc2 = 2.05
xc3 = 2.4 # estimated

# Curves: y = A * sqrt(1 - (x/xc)^2)
def curve(x, xc, A):
    return A * np.sqrt(np.maximum(0, 1 - (x/xc)**2))

y1 = curve(omega, xc1, 0.45)
y2 = curve(omega, xc2, 0.6)
y3 = curve(omega, xc3, 0.75)

# Data points
x_d1 = np.linspace(0, 1.4, 6)
y_d1 = curve(x_d1, xc1, 0.45) + np.random.normal(0, 0.01, len(x_d1))

x_d2 = np.linspace(0, 2.0, 8)
y_d2 = curve(x_d2, xc2, 0.6) + np.random.normal(0, 0.015, len(x_d2))

x_d3 = np.linspace(0, 2.3, 8)
y_d3 = curve(x_d3, xc3, 0.75) + np.random.normal(0, 0.02, len(x_d3))


# --- Plotting ---
fig, ax = plt.subplots(figsize=(5, 4), dpi=150)

# Plot curves and data
# Dark Blue
ax.plot(omega, y1, color='#1f3b5c', lw=2)
ax.plot(x_d1, y_d1, 'o', color='#2b5585', markeredgecolor='#1f3b5c', markersize=8, mew=1.5)

# Medium Blue
ax.plot(omega, y2, color='#4d7096', lw=2)
ax.plot(x_d2, y_d2, 'o', color='#6e90b8', markeredgecolor='#4d7096', markersize=8, mew=1.5)

# Light Blue
ax.plot(omega, y3, color='#8baecf', lw=2)
ax.plot(x_d3, y_d3, 'o', color='#adcce3', markeredgecolor='#8baecf', markersize=8, mew=1.5) # Using hollow-ish looking colors


# Styling
ax.set_xlabel(r'Raman coupling $\Omega$ ($E_{m R}/\hbar$)', fontsize=14)
ax.set_ylabel(r'Frequency $\omega$ ($\omega_x$)', fontsize=14)
ax.set_xlim(-0.1, 2.6)
ax.set_ylim(0, 1.0)

# Ticks
ax.tick_params(direction='in', top=True, right=True, width=1.5)
ax.set_xticks([0, 1, 2])
ax.set_yticks([0.0, 0.5, 1.0])
for spine in ax.spines.values():
    spine.set_linewidth(1.5)

plt.tight_layout()
plt.show()
