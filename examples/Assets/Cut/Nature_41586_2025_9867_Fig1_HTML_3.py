import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec

# --- Data Simulation ---
# Capacity
cap_nacl = np.linspace(0, 200, 100) # NaCl capacity is low?
cap_nadca = np.linspace(0, 800, 200)

# Voltage profiles
# NaCl (Blue): Rises sharply then plateaus
v_nacl = 3.8 + 0.6 * (1 - np.exp(-cap_nacl/20)) 
v_nacl = np.clip(v_nacl, 3.8, 4.4)

# NaDCA (Red): Rises more slowly
v_nadca = 3.8 + 0.25 * (1 - np.exp(-cap_nadca/100))
v_nadca = np.clip(v_nadca, 3.8, 4.05)

# Raman Spectra
raman_shift = np.linspace(100, 320, 300)

def peak(x, center, width, height):
    return height * np.exp(-((x - center)**2) / (2 * width**2))

# Pristine (Grey)
y_pristine = peak(raman_shift, 155, 3, 10) + peak(raman_shift, 220, 3, 12) + np.random.normal(0, 0.2, len(raman_shift)) + 1

# NaDCA (Red) - SCl4
y_nadca_raman = peak(raman_shift, 290, 5, 2) + np.random.normal(0, 0.1, len(raman_shift)) + 1

# NaCl (Blue) - S
y_nacl_raman = peak(raman_shift, 155, 4, 12) + peak(raman_shift, 220, 4, 14) + np.random.normal(0, 0.2, len(raman_shift)) + 1

# --- Plotting ---
fig = plt.figure(figsize=(8, 5), dpi=150)
gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1.2], wspace=0.3)

# Left: Voltage
ax1 = fig.add_subplot(gs[0])
ax1.plot(cap_nacl, v_nacl, color='#4488EE', lw=2)
ax1.plot(cap_nadca, v_nadca, color='#EE4444', lw=2)

ax1.text(100, 4.5, 'NaCl
electrolyte', ha='center', color='black', fontsize=12)
ax1.text(400, 4.15, 'NaDCA
electrolyte', ha='center', color='black', fontsize=12)

ax1.set_xlabel(r'Capacity (mAh g$^{-1}$)', fontsize=14)
ax1.set_ylabel('Voltage (V)', fontsize=14)
ax1.set_xlim(0, 800)
ax1.set_ylim(3.7, 4.65)

# Top Axis (mAh cm-2)
ax1t = ax1.twiny()
ax1t.set_xlim(0, 2) # Rough conversion
ax1t.set_xlabel(r'Capacity (mAh cm$^{-2}$)', fontsize=12)

# Right: Raman
ax2 = fig.add_subplot(gs[1])
# Offset
off_p = 0
off_r = 15
off_b = 25

ax2.plot(raman_shift, y_pristine + off_p, color='#555555', lw=1.5)
ax2.text(310, off_p+3, 'Pristine', ha='right', fontsize=12)

ax2.plot(raman_shift, y_nadca_raman + off_r, color='#EE4444', lw=1.5)
ax2.text(290, off_r+3, 'SCl$_4$', ha='center', fontsize=12)

ax2.plot(raman_shift, y_nacl_raman + off_b, color='#4488EE', lw=1.5)
ax2.text(160, off_b+7, 'S', ha='left', fontsize=12)
ax2.annotate('', xy=(155, off_b+12), xytext=(160, off_b+8), arrowprops=dict(arrowstyle='-'))
ax2.text(225, off_b+7, 'S', ha='left', fontsize=12)
ax2.annotate('', xy=(220, off_b+14), xytext=(225, off_b+8), arrowprops=dict(arrowstyle='-'))

ax2.set_xlabel(r'Raman shift (cm$^{-1}$)', fontsize=14)
ax2.set_yticks([])
ax2.spines['left'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.spines['top'].set_visible(False)
ax2.set_xticks([160, 240, 320])

plt.show()
