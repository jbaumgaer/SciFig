import matplotlib.pyplot as plt
import numpy as np

# --- Data Simulation ---
# Categories
labels = ['Control', 'Dipolar
passivation']
# Values (Stacked)
# Start, V_oc, ETL, HTL, Bulk, End
# V_oc (Base)
v_oc_ctrl = 0.875
v_oc_dip = 0.912

# ETL Loss
loss_etl_ctrl = 0.028 # to 0.903
loss_etl_dip = 0.027 # to 0.939 (Wait, Dipolar has higher loss? Or is it gains?)
# The chart shows "Loss from". 
# The bars stack up to the QFLS potential.
# Control: Base=0.875. ETL adds ~0.03 -> 0.905. HTL adds ~0.05 -> 0.96. Bulk adds ~0.04 -> 1.0.
# Dipolar: Base=0.912. ETL adds ~0.03 -> 0.942. HTL adds ~0.03 -> 0.97. Bulk adds ~0.03 -> 1.0.

val_voc = [0.875, 0.912]
val_etl = [0.030, 0.028]
val_htl = [0.055, 0.030]
val_bulk = [0.040, 0.030]

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 3), dpi=150)

# Colors
c_voc = 'lightgray'
c_etl = '#1166AA'
c_htl = '#66AADD'
c_bulk = '#BBDDFF'

y_pos = [0, 1]
height = 0.5

# Stacked Horizontal Bars
p1 = ax.barh(y_pos, val_voc, height, color=c_voc, label='$V_{m oc}$')
p2 = ax.barh(y_pos, val_etl, height, left=val_voc, color=c_etl, label='ETL')
p3 = ax.barh(y_pos, val_htl, height, left=np.array(val_voc)+np.array(val_etl), color=c_htl, label='HTL')
p4 = ax.barh(y_pos, val_bulk, height, left=np.array(val_voc)+np.array(val_etl)+np.array(val_htl), color=c_bulk, label='Bulk')

# Styling
ax.set_yticks(y_pos)
ax.set_yticklabels(labels, fontsize=12)
ax.set_xlabel(r'QFLS, $qV_{m oc}$ (eV)', fontsize=14)
ax.set_xlim(0.80, 1.03)

# Legend
ax.legend(title='Loss from', bbox_to_anchor=(1.05, 1), loc='upper left', frameon=False, fontsize=12)

# Ticks
ax.minorticks_on()
ax.tick_params(direction='in', top=True, right=True)

plt.tight_layout()
plt.show()
