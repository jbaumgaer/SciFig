import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
r = np.linspace(0, 6, 100)

def fit_curve(x, center, width, amp, phase=0):
    # Simulated EXAFS FT magnitude
    return amp * np.exp(-((x - center)**2) / (2 * width**2)) * (1 + 0.2*np.cos(10*x + phase))

# Base structure
y_base = fit_curve(r, 1.5, 0.4, 1.0) + fit_curve(r, 2.5, 0.5, 0.4) + fit_curve(r, 3.2, 0.5, 0.3)

# 1. 800 (Top)
y_800_data = y_base + np.random.normal(0, 0.05, len(r))
y_800_fit = y_base # Perfect fit

# 2. 550 (Middle)
y_550_data = y_base * 0.9 + np.random.normal(0, 0.05, len(r))
y_550_fit = y_base * 0.9

# 3. 300 (Bottom)
y_300_data = y_base * 0.8 + fit_curve(r, 2.0, 0.3, 0.2) + np.random.normal(0, 0.05, len(r))
y_300_fit = y_base * 0.8 + fit_curve(r, 2.0, 0.3, 0.2)

datasets = [
    (y_800_data, y_800_fit, '#337733', 'KB@RuP-800'),
    (y_550_data, y_550_fit, '#006699', 'KB@RuP-550'),
    (y_300_data, y_300_fit, '#993333', 'KB@RuP-300')
]

# --- Plotting ---
fig, axes = plt.subplots(3, 1, figsize=(6, 6), dpi=150, sharex=True)
plt.subplots_adjust(hspace=0)

for ax, (data, fit, col, lbl) in zip(axes, datasets):
    # Fit (Open circles)
    ax.plot(r[::3], fit[::3], 'o', mfc='none', mec='black', markersize=8, label='Fit', mew=1)
    
    # Data (Solid Line)
    ax.plot(r, data, color=col, lw=1.5, label=lbl)
    
    # Label
    ax.legend(frameon=False, loc='upper right', fontsize=10)
    
    ax.set_ylim(-0.2, 1.5)
    ax.set_yticks([])
    
    if ax != axes[-1]:
        ax.spines['bottom'].set_visible(True) # Keep border

# X Label
axes[-1].set_xlabel(r'$R + \alpha$ ($\AA$)', fontsize=14)
axes[-1].set_xlim(0, 6)

# Common Y Label
fig.text(0.04, 0.5, r'FT ($k^3 \chi(k)$)', va='center', rotation='vertical', fontsize=14)

plt.show()
