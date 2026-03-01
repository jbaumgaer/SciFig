import matplotlib.pyplot as plt
import numpy as np


# --- Data Simulation ---
# Voltage Profile
def voltage_profile(capacity, cap_max, charge=True):
    # Sigmoidal-like shape for battery
    soc = capacity / cap_max
    if charge:
        v = 3.4 + 0.5 * soc + 0.1 * np.tan((soc - 0.5) * 2) + 0.4 * soc**3
        # Add start/end steepness
        v = np.maximum(2.8, np.minimum(4.5, v))
        return v
    else: # Discharge
        v = 4.2 - 0.5 * (1-soc) - 0.1 * np.tan((0.5 - soc) * 2) - 0.4 * (1-soc)**3
        v = np.maximum(2.8, np.minimum(4.5, v))
        return v

# Generate curves
cycles = [5, 50, 100, 140]
colors = ['#88CCEE', '#6699CC', '#DDCC77', '#CC6677'] # Blue to Red/Yellow/Red
colors = ['#ADD8E6', '#6495ED', '#F0E68C', '#CD5C5C']

fig, ax = plt.subplots(figsize=(5, 5), dpi=150)

for i, (cyc, col) in enumerate(zip(cycles, colors)):
    cap_max = 1200 - i * 100 # Capacity fading

    # Charge
    q_chg = np.linspace(0, cap_max, 100)
    v_chg = 3.4 + (q_chg/cap_max) * 0.8 + 0.1 * np.exp((q_chg - cap_max)/100)
    v_chg[0] = 3.0 # Start
    # Smooth start

    # Simple polynomial fit for visual look
    x = np.linspace(0, 1, 100)
    v_chg = 3.4 + 0.6 * x + 0.2 * x**3 + 0.3 * np.exp(10*(x-1))
    v_chg = np.clip(v_chg, 2.8, 4.5)

    # Discharge
    v_dch = 4.4 - 0.6 * (1-x) - 0.2 * (1-x)**3 - 0.4 * np.exp(10*((1-x)-1))
    v_dch = np.clip(v_dch, 2.8, 4.5)

    # Hysteresis increase
    v_chg += i * 0.02
    v_dch -= i * 0.02

    ax.plot(q_chg * cap_max, v_chg, color=col, lw=1.5)
    ax.plot(q_chg * cap_max, v_dch, color=col, lw=1.5)

# Text labels
ax.text(1000, 3.8, 'P-NCM', fontsize=12)
ax.text(700, 2.6, '140th', fontsize=12, ha='right')
ax.text(1100, 2.6, '5th', fontsize=12, ha='left')
ax.annotate('', xy=(720, 2.65), xytext=(1080, 2.65), arrowprops=dict(arrowstyle='->', color='#555555'))

# Styling
ax.set_xlabel('Cell capacity (mAh)', fontsize=14)
ax.set_ylabel('Cell voltage (V)', fontsize=14)
ax.set_xlim(0, 1300)
ax.set_ylim(2.5, 4.7)
ax.set_xticks([0, 400, 800, 1200])
ax.set_yticks([2.5, 3.0, 3.5, 4.0, 4.5])
ax.tick_params(direction='in', top=True, right=True)

plt.tight_layout()
plt.show()
