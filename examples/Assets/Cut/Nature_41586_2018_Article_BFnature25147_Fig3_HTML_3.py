import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Energy (x)
x = np.random.uniform(2.505, 2.585, 15)
# Splitting (y)
y = np.random.uniform(1.1, 2.6, 15)
# Make some trend? Image looks scattered but generally bottom-left to top-right
y = 1.0 + 1.5 * (x - 2.50) / 0.08 + np.random.normal(0, 0.3, 15)
y = np.clip(y, 1.1, 2.5)

# --- Plotting ---
fig, ax = plt.subplots(figsize=(5, 5), dpi=150)

# Scatter
ax.scatter(x, y, marker='s', color='#4466AA', edgecolor='none', s=40)

# Text
ax.text(2.55, 1.1, r'$\bar{\Delta} = 1.63$ meV', fontsize=12, ha='center')

# Inset Schematic
ax_ins = ax.inset_axes([0.4, 0.7, 0.2, 0.2])
ax_ins.axis('off')
t = np.linspace(-3, 3, 100)
p1 = np.exp(-(t + 0.5)**2 / 0.5)
p2 = np.exp(-(t - 0.5)**2 / 0.5)
ax_ins.plot(t, p1, 'k-', lw=1)
ax_ins.fill_between(t, 0, p1, color='#EEEEEE', alpha=0.5)
ax_ins.plot(t, p2, 'k-', lw=1)
ax_ins.fill_between(t, 0, p2, color='#FFCCCC', alpha=0.5)
# Arrow
ax_ins.annotate('', xy=(-0.5, 0.6), xytext=(0.5, 0.6), arrowprops=dict(arrowstyle='<->', lw=1))
ax_ins.text(0, 0.7, r'$\Delta$', ha='center', fontsize=10, color='#335599')

# Styling
ax.set_xlabel('Energy (eV)', fontsize=14)
ax.set_ylabel('Splitting (meV)', fontsize=14)
ax.set_xlim(2.50, 2.59)
ax.set_ylim(1.0, 2.7)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='in', top=True, right=True)

plt.tight_layout()
plt.show()
