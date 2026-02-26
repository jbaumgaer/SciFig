import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
j = np.linspace(0, 60, 100)

def eqe_curve(j, max_eqe):
    # Saturating curve
    # Starts at 0, rises quickly, then slightly decays
    return max_eqe * (j / (j + 2)) * (1 - 0.05 * j/60)

# Control (Light Blue)
y_ctrl = eqe_curve(j, 2.5) + 0.1 * np.random.normal(0, 0.1, len(j))
# Start negative/zero
y_ctrl[0] = -0.5

# Dipolar (Dark Blue)
y_dip = eqe_curve(j, 7.5) + 0.1 * np.random.normal(0, 0.1, len(j))
y_dip[0] = 5.0 # Starts higher? No, starts at ~5 in image

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# Plots
ax.plot(j, y_ctrl, 'o-', color='#77AADD', mfc='white', markevery=10, lw=2, label='Control')
ax.plot(j, y_dip, 'o-', color='#115599', ms=8, markevery=10, lw=2, label='Dipolar passivation')

# Dashed Line
ax.axvline(33, color='gray', linestyle=':')
ax.text(33, 0.5, r'$J_{m sc}$ (AM 1.5G) $\approx$ 33 mA cm$^{-2}$', ha='center', fontsize=12)

# Values
ax.text(34, 2.5, '2.40%', color='black', fontsize=12)
ax.text(34, 7.5, '7.05%', color='black', fontsize=12)

# Legend
ax.legend(frameon=False, loc='upper left', fontsize=12)

# Styling
ax.set_xlabel(r'Current density (mA cm$^{-2}$)', fontsize=14)
ax.set_ylabel(r'EQE$_{m EL}$ (%)', fontsize=14)
ax.set_xlim(5, 60)
ax.set_ylim(-1, 10.5)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='in', top=True, right=True)

plt.tight_layout()
plt.show()
