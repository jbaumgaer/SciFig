import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
be = np.linspace(174, 158, 300)

def peak(x, center, width, height):
    return height * np.exp(-((x - center)**2) / (2 * width**2))

# Positions
pos_s0_1 = 163.5
pos_s0_2 = 164.7
pos_s4_1 = 168.0
pos_s4_2 = 169.2

# 1. As-prepared (Bottom)
y_as = peak(be, pos_s0_1, 0.6, 1.0) + peak(be, pos_s0_2, 0.6, 0.5)
y_as_tot = y_as + np.random.normal(0, 0.05, len(be))

# 2. Charged (Middle)
y_chg_s0 = peak(be, pos_s0_1, 0.8, 0.6) + peak(be, pos_s0_2, 0.8, 0.3)
y_chg_s4 = peak(be, pos_s4_1, 1.0, 0.7) + peak(be, pos_s4_2, 1.0, 0.35)
y_chg_tot = y_chg_s0 + y_chg_s4 + np.random.normal(0, 0.05, len(be))

# 3. Discharged (Top)
y_dch_s0 = peak(be, pos_s0_1, 0.8, 0.9) + peak(be, pos_s0_2, 0.8, 0.45)
y_dch_s4 = peak(be, pos_s4_1, 1.5, 0.1) # Weak S4+
y_dch_tot = y_dch_s0 + y_dch_s4 + np.random.normal(0, 0.05, len(be))

datasets = [
    (y_as_tot, y_as, np.zeros_like(be), 'As-prepared'),
    (y_chg_tot, y_chg_s0, y_chg_s4, 'Charged'),
    (y_dch_tot, y_dch_s0, y_dch_s4, 'Discharged')
]

# --- Plotting ---
fig, axes = plt.subplots(3, 1, figsize=(5, 6), dpi=150, sharex=True)
plt.subplots_adjust(hspace=0)

for ax, (tot, s0, s4, lbl) in zip(axes[::-1], datasets): # Reverse order to put As-prepared at bottom
    # Scatter Raw
    ax.scatter(be[::3], tot[::3], facecolors='none', edgecolors='gray', s=20)

    # Fit line
    ax.plot(be, s0+s4, color='#444444', lw=1)

    # Fill S0 (Blue)
    ax.fill_between(be, 0, s0, color='#88CCEE', alpha=0.8, edgecolor='#4488BB')

    # Fill S4 (Red)
    ax.fill_between(be, 0, s4, color='#FF9999', alpha=0.8, edgecolor='#CC4444')

    ax.text(173.5, 0.5, lbl, fontsize=12)

    ax.set_yticks([])
    ax.set_ylim(-0.2, 1.5)

    # Vertical Dashed Lines
    ax.axvline(163.5, color='gray', linestyle='--', lw=1.5, zorder=0)
    ax.axvline(168.0, color='gray', linestyle='--', lw=1.5, zorder=0)

# Labels
axes[0].text(168, 1.2, 'S$^{4+}$', ha='center', fontsize=12)
axes[0].text(161, 1.2, 'S$^0$', ha='center', fontsize=12)
axes[0].text(159, 1.2, 'S 2p', ha='right', fontsize=12)

# Axis
axes[-1].set_xlabel('Binding energy (eV)', fontsize=14)
axes[-1].set_xlim(174, 158)
axes[-1].set_xticks([174, 171, 168, 165, 162, 159])

plt.show()
