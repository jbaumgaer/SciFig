import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
two_theta = np.linspace(20, 60, 1000)

def peak_gen(x, center, width, height):
    return height * np.exp(-((x - center)**2) / (2 * width**2))

# RuP2 Reference (Bottom)
rup2_peaks = [
    (23.5, 0.6), (30.1, 0.3), (35.2, 0.2), (36.0, 0.4), 
    (38.5, 0.1), (39.2, 0.1), (46.8, 0.1), (47.5, 0.15),
    (50.2, 0.2), (56.0, 0.1), (57.8, 0.1)
] # (pos, rel_height)

# RuO2 Reference
ruo2_peaks = [
    (32.1, 0.6), (37.2, 0.3), (42.0, 0.1), (44.5, 0.4), 
    (54.2, 0.3)
]

# Carbon Reference
c_peaks = [(44.0, 0.5)] # Very broad usually but ref is sharp line

# Samples (Noisy lines)
noise_level = 0.05
# KB@RuP-800 (Green) - Matches RuP2
y_800 = np.random.normal(0, noise_level, len(two_theta)) + 0.2
for p, h in rup2_peaks:
    y_800 += peak_gen(two_theta, p, 0.3, h)

# KB@RuP-550 (Blue) - Matches RuP2
y_550 = np.random.normal(0, noise_level, len(two_theta)) + 0.2
for p, h in rup2_peaks:
    y_550 += peak_gen(two_theta, p, 0.3, h)

# KB@RuP-300 (Red) - Amorphous / Broad
y_300 = np.random.normal(0, noise_level, len(two_theta)) + 0.2
y_300 += peak_gen(two_theta, 44.5, 1.0, 0.5) # Broad peak
y_300 += peak_gen(two_theta, 38, 1.5, 0.1)

# KB@Ru (Black)
y_ru = np.random.normal(0, noise_level, len(two_theta)) + 0.2
y_ru += peak_gen(two_theta, 44, 0.8, 0.3) # Broad C/Ru


# Offset for stacking
off_800 = 0
off_550 = 0.8
off_300 = 1.6
off_ru = 2.4

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 6), dpi=150)
gs = fig.add_gridspec(3, 1, height_ratios=[4, 0.5, 0.5], hspace=0)
ax_main = fig.add_subplot(gs[0])
ax_ref1 = fig.add_subplot(gs[1], sharex=ax_main)
ax_ref2 = fig.add_subplot(gs[2], sharex=ax_main)

# Main Plot
ax_main.plot(two_theta, y_ru + off_ru, color='#555555', lw=1)
ax_main.text(58, off_ru + 0.3, 'KB@Ru', ha='right')

ax_main.plot(two_theta, y_300 + off_300, color='#993333', lw=1)
ax_main.text(58, off_300 + 0.3, 'KB@RuP-300', ha='right', color='#993333')

ax_main.plot(two_theta, y_550 + off_550, color='#006699', lw=1)
ax_main.text(58, off_550 + 0.3, 'KB@RuP-550', ha='right', color='#006699')

ax_main.plot(two_theta, y_800 + off_800, color='#336633', lw=1)
ax_main.text(58, off_800 + 0.3, 'KB@RuP-800', ha='right', color='#336633')

# Labels on peaks (Blue)
labels = [(23.5, '(110)'), (30.1, '(020)'), (36.0, '(111)'), (39, '(101)'), (44, '(011)'), (47, '(012)'), (50, '(112)')]
# Adjust manually to match image positions roughly
ax_main.text(23.5, off_800+0.7, '(110)', color='#006699', rotation=45, ha='center')
ax_main.text(30.1, off_800+0.8, '(020)', color='#006699', rotation=45, ha='center')
ax_main.text(39.0, off_800+0.7, '(101)', color='#006699', rotation=45, ha='center')
ax_main.text(36.0, off_550+0.7, '(111)', color='#993333', rotation=45, ha='center')
ax_main.text(50.0, off_550+0.7, '(112)', color='#993333', rotation=45, ha='center')
ax_main.text(43.0, off_300+0.7, '(011)', color='black', rotation=45, ha='center')
ax_main.text(47.0, off_ru+0.5, '(012)', color='black', rotation=45, ha='center')


# Ref 1 (RuO2 + C)
for p, h in ruo2_peaks:
    ax_ref1.vlines(p, 0, h, color='#993333', lw=1.5)
ax_ref1.vlines(44, 0, 0.3, color='black', lw=1.5) # C
ax_ref1.text(20.5, 0.4, 'C PDF
no. 50-1083', fontsize=8, va='center')
ax_ref1.text(59.5, 0.6, 'RuO$_2$ PDF no. 50-1428', color='#993333', ha='right', fontsize=9)

# Ref 2 (RuP2)
for p, h in rup2_peaks:
    ax_ref2.vlines(p, 0, h, color='#006699', lw=1.5)
ax_ref2.text(59.5, 0.5, 'RuP$_2$ PDF no. 34-0333', color='#006699', ha='right', fontsize=9)


# Styling
ax_main.set_xlim(20, 60)
ax_main.set_xticks([])
ax_main.set_yticks([])
ax_main.set_ylabel('Intensity (a.u.)', fontsize=14)
ax_main.spines['bottom'].set_visible(False)

ax_ref1.set_xlim(20, 60)
ax_ref1.set_yticks([])
ax_ref1.set_xticks([])
ax_ref1.set_ylim(0, 1)

ax_ref2.set_xlim(20, 60)
ax_ref2.set_yticks([])
ax_ref2.set_xlabel(r'2$	heta$ (°)', fontsize=14)
ax_ref2.set_ylim(0, 0.8)

plt.show()
