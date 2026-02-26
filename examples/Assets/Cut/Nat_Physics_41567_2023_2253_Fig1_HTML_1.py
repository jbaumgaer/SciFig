import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec

# --- Data Simulation ---
# Q axis
q = np.linspace(1.2, 6.5, 500)

# Static Diffraction I0 (Top)
def lorentzian(x, center, width, height):
    return height / (1 + ((x - center)/width)**2)

I0 = lorentzian(q, 1.5, 0.1, 1.0) + 
     lorentzian(q, 2.1, 0.15, 2.0) + 
     lorentzian(q, 3.0, 0.2, 0.5) + 
     lorentzian(q, 3.7, 0.2, 0.3) + 
     lorentzian(q, 4.3, 0.2, 0.2) + 
     lorentzian(q, 5.5, 0.3, 0.1)
I0 += 0.1 # Background

# Differential Map (Bottom)
# Time axis: 0-10 linear, break, 50-150
# Let's just simulate one continuous block for simplicity or 3 blocks.
# Simplest: 0 to 20 ps (Main dynamics happen here)
time = np.linspace(-2, 20, 100)
Q, T = np.meshgrid(q, time)

# Delta I/I0
# Negative stripes at Bragg peaks (Debye-Waller)
signal = np.zeros_like(Q)
# Decay time constant
tau = 2.0 
# Activation
act = np.zeros_like(T)
act[T>0] = 1 - np.exp(-T[T>0]/tau)

# Bragg Peaks (Negative)
for pos in [1.5, 2.1, 3.0, 3.7, 4.3, 5.5]:
    signal -= 3.0 * act * np.exp(-((Q - pos)/0.15)**2)

# Diffuse Scattering (Positive, in between)
for pos in [1.8, 2.5, 3.3, 4.0, 4.9]:
    signal += 1.5 * act * np.exp(-((Q - pos)/0.3)**2)

# Add noise
signal += np.random.normal(0, 0.5, signal.shape)

# --- Plotting ---
fig = plt.figure(figsize=(6, 8), dpi=150)
gs = gridspec.GridSpec(2, 1, height_ratios=[1, 3], hspace=0)

# Top: I0
ax0 = fig.add_subplot(gs[0])
ax0.plot(q, I0, 'k-', lw=1)
ax0.set_ylabel(r'$I_0(q)$', fontsize=12)
ax0.set_xlim(1.2, 6.5)
ax0.set_xticks([])
# Peak labels
peaks = [1.5, 2.1, 3.0, 3.7]
labels = ['110', '200', '220', '222']
for p, l in zip(peaks, labels):
    ax0.text(p, I0.max()*1.1, l, rotation=90, ha='center', fontsize=8)

# Bottom: Heatmap
ax1 = fig.add_subplot(gs[1])
# Red-White-Blue (Seismic or bwr)
cmap = plt.cm.bwr
im = ax1.imshow(signal, aspect='auto', extent=[1.2, 6.5, -2, 20], cmap=cmap, vmin=-4, vmax=4, origin='lower')

ax1.set_xlabel(r'$q$ ($\AA^{-1}$)', fontsize=14)
ax1.set_ylabel('Time (ps)', fontsize=14)
ax1.axhline(0, color='black', linestyle='--', lw=1)

# Colorbar
cbar = fig.colorbar(im, ax=ax1, location='right', pad=0.02)
cbar.set_label(r'Differential scattering $\Delta I(t,q)/I_0(q)$ (%)', rotation=270, labelpad=15)

plt.show()
