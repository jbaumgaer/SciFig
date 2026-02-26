import matplotlib.pyplot as plt
import numpy as np

# Data simulation
cycles = np.linspace(0, 500, 100)
# NT-NCM: Gradual decline from 205 to ~171 (83.4% of 205)
nt_ncm = 205 * (1 - 0.166 * (cycles / 500))
# P-NCM: Fast decline
p_ncm_base = 195 * np.exp(-0.005 * np.linspace(0, 40, 10))
p_ncm_ext = np.linspace(p_ncm_base[-1], 158, 5)
p_ncm = np.concatenate([p_ncm_base, p_ncm_ext])
p_cycles = np.linspace(0, 45, len(p_ncm))

# Plotting
fig, ax = plt.subplots(figsize=(10, 4), dpi=100)

ax.plot(cycles, nt_ncm, 's', color='salmon', markersize=4, markerfacecolor='none', label='NT-NCM')
ax.plot(p_cycles, p_ncm, 's', color='steelblue', markersize=4, markerfacecolor='none', label='P-NCM')

# Annotations
ax.axvline(300, color='black', linestyle='--', linewidth=1)
ax.text(250, 210, '300 cycles 91.1%', fontsize=10)
ax.text(460, 210, '500 cycles 83.4%', fontsize=10)
ax.annotate('Lower than 80%', xy=(40, 158), xytext=(20, 100),
            arrowprops=dict(arrowstyle='->', color='slategray'), fontsize=10)
ax.text(10, 20, '1 C, 2.8–4.8 V versus Li$^+$/Li, RT', fontsize=10)

# Formatting
ax.set_xlabel('Cycle number', fontsize=12)
ax.set_ylabel('Discharge capacity (mAh g$^{-1}$)', fontsize=12)
ax.set_xlim(0, 500)
ax.set_ylim(0, 300)
ax.legend(loc='center right', frameon=False)
plt.tight_layout()
plt.show()
