import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
energy = np.linspace(2465, 2490, 500)

def lorentzian(x, center, width, height):
    return height * (width**2 / ((x - center)**2 + width**2))

# Reference Spectra
# Elemental Sulfur (S): Peak ~2472.5
ref_S = lorentzian(energy, 2472.5, 1.0, 1.2) + lorentzian(energy, 2479, 4, 0.2)
# Na2SO3: Peak ~2478
ref_Na2SO3 = lorentzian(energy, 2478, 0.8, 1.8) + lorentzian(energy, 2480.5, 1, 0.3)

# Sample Spectra (Mixtures of oxidation states)
# Peaks: S0 (2472.5), S1+ (2474), S2+ (2476), S4+ (2478)
peak_S0 = lorentzian(energy, 2472.5, 1.0, 1.0)
peak_S1 = lorentzian(energy, 2474, 0.8, 1.0)
peak_S2 = lorentzian(energy, 2476, 0.8, 1.0)
peak_S4 = lorentzian(energy, 2478, 0.8, 1.0)
peak_post = lorentzian(energy, 2482, 2.0, 0.5)

# Fully discharged: Mostly lower oxidation states
y_discharged = 0.8*peak_S0 + 0.4*peak_S1 + 0.6*peak_S2 + 0.6*peak_S4 + 0.4*peak_post + 0.1
# Charge 400: S4+ growing
y_chg400 = 0.6*peak_S0 + 0.5*peak_S1 + 1.2*peak_S2 + 1.2*peak_S4 + 0.4*peak_post + 0.1
# Charge 800: S4+ dominant
y_chg800 = 0.5*peak_S0 + 0.4*peak_S1 + 0.9*peak_S2 + 1.8*peak_S4 + 0.8*peak_post + 0.1

# Normalize/Offset for stacking
offset_top = 2.5
y_discharged += offset_top
y_chg400 += offset_top
y_chg800 += offset_top

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 7), dpi=150)

# Bottom Panel (References)
ax.plot(energy, ref_S, color='orange', label='S')
ax.plot(energy, ref_Na2SO3, color='rebeccapurple', label='Na$_2$SO$_3$')

# Top Panel (Samples)
ax.plot(energy, y_chg800, color='#EE5544', label='Charge 800 mAh g$^{-1}$')
ax.plot(energy, y_chg400, color='#555555', label='Charge 400 mAh g$^{-1}$')
ax.plot(energy, y_discharged, color='#4488EE', label='Fully discharged')

# Dashed Vertical Lines
vlines = [2472.5, 2474, 2476, 2478]
labels = ['S$^0$', 'S$^{1+}$', 'S$^{2+}$', 'S$^{4+}$']
for v, l in zip(vlines, labels):
    ax.axvline(v, ymin=0.1, ymax=0.9, color='gray', linestyle='--', linewidth=1.5)
    ax.text(v, 6.2, l, ha='center', fontsize=12)

# Styling
ax.set_xlabel('Photon energy (eV)', fontsize=14)
ax.set_ylabel('Normalized absorption (a.u.)', fontsize=14)
ax.set_xlim(2465, 2490)
ax.set_ylim(0, 7)

# Remove Y ticks
ax.set_yticks([])
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(True) # Keep left spine line but no ticks

# Custom Legends
# Top legend
leg1 = ax.legend(handles=[
    plt.Line2D([],[], color='#EE5544'),
    plt.Line2D([],[], color='#555555'),
    plt.Line2D([],[], color='#4488EE')],
    labels=['Charge 800 mAh g$^{-1}$', 'Charge 400 mAh g$^{-1}$', 'Fully discharged'],
    loc='upper left', frameon=False, bbox_to_anchor=(0.1, 1.1))

# Bottom legend (References) manually placed
ax.text(2473, 1.5, '— S', color='black', fontsize=12, fontweight='bold')
ax.plot([2472.5, 2473], [1.55, 1.55], color='orange', lw=2) # Fake legend line
ax.text(2477, 1.5, '— Na$_2$SO$_3$', color='black', fontsize=12, fontweight='bold')
# ... better to use standard legend for simplicity in script
# ax.legend(loc='lower center', ncol=2, frameon=False) # This would override the first one

plt.tight_layout()
plt.show()
