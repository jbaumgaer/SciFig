import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
wl = np.linspace(300, 1100, 400)

# WBG Subcell (Blue) - Cutoff ~700nm
eqe_wbg = np.zeros_like(wl)
mask_wbg = (wl >= 300) & (wl <= 720)
eqe_wbg[mask_wbg] = 90 * (1 - ((wl[mask_wbg]-500)/400)**4) # Flat top
# Add cutoff slope
eqe_wbg = np.where(wl > 680, eqe_wbg * np.exp(-(wl-680)/10), eqe_wbg)
# Start slope
eqe_wbg = np.where(wl < 350, eqe_wbg * (wl-300)/50, eqe_wbg)
# Noise
eqe_wbg += np.random.normal(0, 0.2, len(wl))

# NBG Subcell (Red) - Start ~700nm, End ~1000nm
eqe_nbg = np.zeros_like(wl)
mask_nbg = (wl >= 650) & (wl <= 1050)
eqe_nbg[mask_nbg] = 85 * (1 - ((wl[mask_nbg]-850)/300)**6)
# Start slope
eqe_nbg = np.where(wl < 720, eqe_nbg * (wl-650)/70, eqe_nbg)
# End slope
eqe_nbg = np.where(wl > 950, eqe_nbg * np.exp(-(wl-950)/20), eqe_nbg)
# Noise
eqe_nbg += np.random.normal(0, 0.2, len(wl))


# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

# Plot
ax.plot(wl[::5], eqe_wbg[::5], 'o-', color='#335577', mfc='gray', label='WBG subcell')
ax.plot(wl[::5], eqe_nbg[::5], 'o-', color='#AA4433', mfc='#E6A0A0', label='NBG subcell')

# Labels
ax.text(450, 20, '16.1 mA cm$^{-2}$', color='#335577', fontsize=14, ha='center')
ax.text(800, 20, '15.7 mA cm$^{-2}$', color='#AA4433', fontsize=14, ha='center')

# Styling
ax.set_xlabel('Wavelength (nm)', fontsize=14)
ax.set_ylabel('EQE (%)', fontsize=14)
ax.set_ylim(0, 100)
ax.set_xlim(300, 1100)

# Legend
ax.legend(frameon=False, loc='upper right', fontsize=12)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='in', top=True, right=True)

plt.tight_layout()
plt.show()
