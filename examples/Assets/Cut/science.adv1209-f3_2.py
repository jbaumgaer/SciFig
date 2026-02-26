import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Top Panel
time = np.linspace(0, 30, 60)
# Oscillating signal
sigma = 6.0 + 0.2 * np.sin(time * 0.8) + 0.1 * np.cos(time * 2)
# Noise
sigma_data = sigma + np.random.normal(0, 0.15, len(time))
sigma_err = np.random.uniform(0.1, 0.3, len(time))

# Bottom Panel (Zoom region 9-12 ms)
time_zoom = np.linspace(9, 12, 8)
stripes = np.linspace(8.5, 10.2, 8) + np.random.normal(0, 0.2, 8)
stripes_err = np.random.uniform(0.2, 0.4, 8)

# --- Plotting ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 6), dpi=150, gridspec_kw={'height_ratios': [1, 0.8]})
plt.subplots_adjust(hspace=0.4)

# Top Panel
ax1.errorbar(time, sigma_data, yerr=sigma_err, fmt='o', color='#CC8888', ecolor='#AA5555', 
             markersize=8, markeredgecolor='#AA5555', elinewidth=1.5, capsize=0)
# Fit line
t_fit = np.linspace(0, 30, 200)
s_fit = 6.0 + 0.2 * np.sin(t_fit * 0.8) + 0.1 * np.cos(t_fit * 2)
ax1.plot(t_fit, s_fit, color='#AA5555', lw=2)

# Shaded region
ax1.axvspan(9, 12, color='lightgray', alpha=0.5, zorder=0)

# Zoom lines (Connector)
# con1 = ConnectionPatch(xyA=(9, 5), xyB=(9, 11), coordsA="data", coordsB="data", axesA=ax1, axesB=ax2, color="gray", alpha=0.2)
# fig.add_artist(con1)
# Simply drawing polygon between axes is hard in static script without transforms. 
# We'll just align them visually.

ax1.set_ylabel(r'Cloud size $\sigma$ ($\mu$m)', fontsize=14)
ax1.set_xlim(0, 30)
ax1.set_ylim(5, 7)
ax1.set_xticks([0, 10, 20, 30])

# Bottom Panel
ax2.errorbar(time_zoom, stripes, yerr=stripes_err, fmt='o', color='#9966CC', ecolor='#663399', 
             markersize=8, markeredgecolor='#663399', elinewidth=1.5, capsize=0)

ax2.set_xlabel('Time (ms)', fontsize=14)
ax2.set_ylabel('Number of
stripes', fontsize=14)
ax2.set_xlim(8.8, 12.2)
ax2.set_ylim(8, 11)
ax2.set_xticks([9, 10, 11, 12])

# Ticks
for ax in [ax1, ax2]:
    ax.minorticks_on()
    ax.tick_params(direction='in', top=True, right=True, width=1.5)
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)

plt.show()
