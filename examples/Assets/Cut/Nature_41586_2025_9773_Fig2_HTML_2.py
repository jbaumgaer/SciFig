import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
time = np.linspace(0, 20000, 500)

def biexp_decay(t, t1, a1, t2, a2):
    return a1 * np.exp(-t/t1) + a2 * np.exp(-t/t2)

# Control (Light Blue)
# t1=132, t2=1882
y_ctrl_fit = biexp_decay(time, 132, 0.8, 1882, 0.2)
y_ctrl_data = y_ctrl_fit * np.random.normal(1, 0.1, len(time))

# Dipolar (Dark Blue)
# t1=43, t2=3912
y_dip_fit = biexp_decay(time, 43, 0.6, 3912, 0.4)
y_dip_data = y_dip_fit * np.random.normal(1, 0.05, len(time))

# Normalize roughly
y_ctrl_data /= np.max(y_ctrl_data)
y_dip_data /= np.max(y_dip_data)

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# Plots
# Control
ax.plot(time, y_ctrl_data, color='#88CCEE', lw=2, alpha=0.8) # Noisy data
ax.plot(time, y_ctrl_fit/np.max(y_ctrl_fit), color='#4488BB', lw=2, alpha=0.8) # Fit line (approx)

# Dipolar
ax.plot(time, y_dip_data, color='#004488', lw=2)
ax.plot(time, y_dip_fit/np.max(y_dip_fit), color='#002244', lw=2)

# Legend
ax.text(5000, 0.5, 'Control, $	au_1=132$ ns, $	au_2=1,882$ ns', color='black', fontsize=12)
ax.text(5000, 0.2, 'Dipolar passivation,
$	au_1=43$ ns, $	au_2=3,912$ ns', color='black', fontsize=12)

# Styling
ax.set_xlabel('Time (ns)', fontsize=14)
ax.set_ylabel('Photoluminescence intensity (normalized)', fontsize=14)
ax.set_yscale('log')
ax.set_ylim(0.001, 1.1)
ax.set_xlim(-500, 20000)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='in', top=True, right=True, which='both')

plt.tight_layout()
plt.show()
