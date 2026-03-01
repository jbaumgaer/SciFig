import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Control
ctrl_data = np.random.normal(24.2, 0.3, 30)
# Target
trgt_data = np.random.normal(26.5, 0.2, 30)

# --- Plotting ---
fig, ax = plt.subplots(figsize=(5, 5), dpi=150)

# Boxplot props
boxprops = dict(linewidth=2, color='#335577')
medianprops = dict(linewidth=2, color='#335577')
whiskerprops = dict(linewidth=2, color='#335577')
capprops = dict(linewidth=2, color='#335577')

# Boxplot Control
bp1 = ax.boxplot([ctrl_data], positions=[1], widths=0.4,
                 boxprops=boxprops, medianprops=medianprops,
                 whiskerprops=whiskerprops, capprops=capprops,
                 showfliers=False, patch_artist=False)

# Boxplot Target
boxprops['color'] = '#AA4433'
medianprops['color'] = '#AA4433'
whiskerprops['color'] = '#AA4433'
capprops['color'] = '#AA4433'
bp2 = ax.boxplot([trgt_data], positions=[2], widths=0.4,
                 boxprops=boxprops, medianprops=medianprops,
                 whiskerprops=whiskerprops, capprops=capprops,
                 showfliers=False, patch_artist=False)

# Scatter + Distribution (Raincloud style simulation)
# Control
x_jit = np.random.normal(1.3, 0.05, len(ctrl_data))
ax.scatter(x_jit, ctrl_data, color='#335577', alpha=0.8, s=30, edgecolors='gray')
# Curve
y_kde = np.linspace(23.5, 25.2, 50)
x_kde = 1.3 + 0.3 * np.exp(-((y_kde - 24.2)/0.4)**2)
ax.plot(x_kde, y_kde, color='#335577', lw=2)

# Target
x_jit2 = np.random.normal(2.3, 0.05, len(trgt_data))
ax.scatter(x_jit2, trgt_data, color='#AA4433', alpha=0.8, s=30, edgecolors='gray')
# Curve
y_kde2 = np.linspace(25.8, 27.2, 50)
x_kde2 = 2.3 + 0.3 * np.exp(-((y_kde2 - 26.5)/0.3)**2)
ax.plot(x_kde2, y_kde2, color='#AA4433', lw=2)

# Styling
ax.set_ylabel('PCE (%)', fontsize=14)
ax.set_xticks([1.15, 2.15])
ax.set_xticklabels(['Control', 'PHNS + BNAC'], fontsize=12)
ax.set_ylim(23, 28)
ax.set_xlim(0.5, 2.8)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='in', top=True, right=True)

plt.tight_layout()
plt.show()
