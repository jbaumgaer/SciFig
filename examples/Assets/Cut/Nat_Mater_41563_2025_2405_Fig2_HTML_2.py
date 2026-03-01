import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
be = np.linspace(140, 126, 300)

def peak(x, center, width, height):
    return height * np.exp(-((x - center)**2) / (2 * width**2))

# Peak Positions
# P 2p 3/2 and 1/2 doublet
pos_rup = 129.5
pos_pc = 133.0 # P-C
pos_po = 134.0 # P-O

# 1. 800 (Bottom)
y_800_rup = peak(be, pos_rup, 0.8, 0.8) + peak(be, pos_rup+0.9, 0.8, 0.4) # Doublet
y_800_po = peak(be, pos_po, 1.0, 0.1)
y_800_pc = peak(be, pos_pc, 1.0, 0.1)
y_800_tot = y_800_rup + y_800_po + y_800_pc + np.random.normal(0, 0.02, len(be))

# 2. 550 (Middle)
y_550_rup = peak(be, pos_rup, 0.8, 0.8) + peak(be, pos_rup+0.9, 0.8, 0.4)
y_550_pc = peak(be, pos_pc, 1.2, 0.2)
y_550_po = peak(be, pos_po, 1.0, 0.05)
y_550_tot = y_550_rup + y_550_po + y_550_pc + np.random.normal(0, 0.02, len(be))

# 3. 300 (Top)
y_300_rup = peak(be, pos_rup, 0.8, 0.8) + peak(be, pos_rup+0.9, 0.8, 0.4)
y_300_pc = peak(be, pos_pc, 1.2, 0.3) # Stronger P-C
y_300_po = peak(be, pos_po, 1.0, 0.05)
y_300_tot = y_300_rup + y_300_po + y_300_pc + np.random.normal(0, 0.02, len(be))

datasets = [
    (y_800_tot, y_800_rup, y_800_pc, y_800_po, 'KB@RuP-800'),
    (y_550_tot, y_550_rup, y_550_pc, y_550_po, 'KB@RuP-550'),
    (y_300_tot, y_300_rup, y_300_pc, y_300_po, 'KB@RuP-300')
]

# --- Plotting ---
fig, axes = plt.subplots(3, 1, figsize=(6, 6), dpi=150, sharex=True)
plt.subplots_adjust(hspace=0)

for ax, (tot, rup, pc, po, lbl) in zip(axes, datasets):
    # Scatter for raw data
    ax.scatter(be[::3], tot[::3], facecolors='none', edgecolors='black', s=30, lw=1)

    # Fit line
    fit_sum = rup + pc + po
    ax.plot(be, fit_sum, color='#444444', lw=1)

    # Fill areas
    # Ru-P (Blue)
    ax.fill_between(be, 0, rup, color='#6699CC', alpha=0.9) # Light blue
    # The doublet split logic for filling (simplified as one block here)
    # P-C (Red/Brown)
    ax.fill_between(be, 0, pc, color='#AA6666', alpha=0.7)
    # P-O (Green)
    ax.fill_between(be, 0, po, color='#66AA66', alpha=0.6)

    # Label
    ax.text(139.5, 0.2, lbl, fontsize=11, va='bottom')

    ax.set_yticks([])
    ax.set_ylim(-0.1, 1.5)

    if ax == axes[0]: # Bottom one in list iteration but Top visually? No, zip order.
        pass

# Add Arrows/Labels on specific plots
# Top Plot (300) - Index 2
axes[2].text(131, 1.1, 'Ru-P', color='#005588', ha='center')
axes[2].annotate('', xy=(129.5, 0.9), xytext=(131, 1.1), arrowprops=dict(arrowstyle='->'))
axes[2].text(128, 1.3, 'Ar 10 nm', ha='center')

# Middle Plot (550) - Index 1
axes[1].text(134, 0.5, 'P-C', color='#883333', ha='center')
axes[1].annotate('', xy=(133, 0.3), xytext=(134, 0.5), arrowprops=dict(arrowstyle='->'))

# Bottom Plot (800) - Index 0
axes[0].text(135, 0.5, 'P-O', color='#336633', ha='center')
axes[0].annotate('', xy=(134, 0.2), xytext=(135, 0.5), arrowprops=dict(arrowstyle='->'))

# Axis
axes[0].set_xlabel('Binding energy (eV)', fontsize=14)
axes[0].set_xlim(140, 126) # Reversed

# Common Y Label
fig.text(0.04, 0.5, 'Intensity (a.u.)', va='center', rotation='vertical', fontsize=14)
axes[2].text(139.5, 1.3, 'P 2p', fontsize=12)

plt.show()
