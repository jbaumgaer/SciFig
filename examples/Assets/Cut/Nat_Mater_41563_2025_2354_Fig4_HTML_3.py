import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
voltage = np.array([0, 15, 30, 45, 60, 70])

# c_M (Brown squares)
# Nonlinear increase
c_m = 3.945 + 0.00015 * voltage + 0.000006 * voltage**2
# Adjust to match end point ~3.985
c_m[-1] = 3.986
c_m[-2] = 3.981

# a_M (Pink circles)
# Nearly constant
a_m = np.array([3.94, 3.94, 3.94, 3.941, 3.941, 3.942])

# --- Plotting ---
fig, ax = plt.subplots(figsize=(5, 6), dpi=150)

# c_M
ax.plot(voltage, c_m, 's-', color='#A6611A', markersize=8, label='c$_M$')
ax.text(60, 3.99, '+1.02%', color='#990033', fontsize=12)

# a_M
ax.plot(voltage, a_m, 'o-', color='#E6A2B6', markersize=8, label='a$_M$')
ax.text(60, 3.944, '+0.00%', color='#D68296', fontsize=12)

# Legend
ax.legend(frameon=False, loc='upper left', fontsize=12)

# Styling
ax.set_xlabel('Voltage (V)', fontsize=14)
ax.set_ylabel(r'Lattice parameter ($\AA$)', fontsize=14)
ax.set_xlim(-5, 75)
ax.set_ylim(3.935, 4.005)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='in', top=True, right=True)

plt.tight_layout()
plt.show()
