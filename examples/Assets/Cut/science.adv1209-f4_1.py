import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
np.random.seed(42)
time = np.linspace(0, 30, 60) # 60 points
# Sine wave trend
d_spacing = 650 + 15 * np.sin(time * 0.4) + 5 * np.sin(time * 0.1)
# Add noise to data points
noise = np.random.normal(0, 5, len(time))
d_data = d_spacing + noise
# Error bars
yerr = np.random.uniform(5, 15, len(time))

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 4), dpi=150)

# Errorbar Plot
ax.errorbar(time, d_data, yerr=yerr, fmt='o', color='#7aa0c4', ecolor='#3e6082',
            markersize=8, markeredgecolor='#3e6082', elinewidth=1.5, capsize=0)

# Trend Line (Fit)
t_fit = np.linspace(0, 30, 200)
d_fit = 650 + 15 * np.sin(t_fit * 0.4) + 5 * np.sin(t_fit * 0.1)
ax.plot(t_fit, d_fit, color='#3e6082', linewidth=2.5)

# Styling
ax.set_xlabel('Time (ms)', fontsize=14)
ax.set_ylabel('Spacing $d$ (nm)', fontsize=14)
ax.set_xlim(0, 30)
ax.set_ylim(600, 700)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='in', which='both', top=True, right=True, width=1.5)
for spine in ax.spines.values():
    spine.set_linewidth(1.5)

plt.tight_layout()
plt.show()
