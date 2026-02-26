# Materials Characterization Methods & Matplotlib Plot Types

## Microscopy

#### Optical Microscopy (🟡)
- Image display (e.g., micrograph), `imshow(x, y, intensity)`
- intensity histogram, `hist()`  

#### Scanning Electron Microscopy (SEM) (🟡)
- High‑magnification surface image, `imshow(x, y, intensity)`
- feature overlay, `contourf()`  
- Crystallite orientation

#### Transmission Electron Microscopy (TEM) (🟡)
- Internal structure image, `imshow(x, y, intensity)`
- intensity line profile, `plot()`  
- SAED

#### Field Ion Microscopy (FIM) (🟢)
- Atom‑scale field image, `imshow(x, y, intensity)`
- 2D atom positions, `scatter()`  

#### Scanning Probe Microscopy (SPM) (🟡)
- Surface topography, `imshow(x, y, intensity)`
- 3D topology, `plot_surface()`  

#### Atomic Force Microscopy (AFM) (🟡)
- Surface height vs XY, `imshow(x, y, intensity)`
- 3D surface plots, `plot_surface()`  

#### Scanning Tunneling Microscopy (STM) (🟡)
- Electron density image, `imshow(x, y, intensity)`
- I–V curve, `plot()`  

#### X‑ray Diffraction Topography (XRT) (🟢)
- Diffraction contrast image, `imshow(x, y, intensity)`
- integrated intensity vs position, `plot()`  

#### Atom‑Probe Tomography (APT) (🟢)
- 3D atom map & composition profile, `scatter()`
- depth/composition histogram, `hist()`  

---

## Spectroscopy

### Optical Radiation

#### Ultraviolet‑Visible Spectroscopy (UV‑vis) (🟡)
- Absorbance/transmittance spectrum, `plot(wavelength, absorbance)`
- in-situ

#### Fourier Transform Infrared Spectroscopy (FTIR) (🔴)
- Infrared spectrum, `plot(wavenumber, absorbance)`
- in-situ

#### Thermoluminescence (TL) (🟡)
- Emission vs temperature, `plot(temperature, intensity)`  
- in-situ

#### Photoluminescence (PL) (🟡)
- Emission intensity vs wavelength, `plot(wavelength, intensity)`  
- in-situ

---

### X‑ray Techniques

#### X‑ray Diffraction (XRD) (🔴)
- Diffraction pattern, `plot(2θ, intensity)`
    - Possibly with insets
- Rietveld refinement, `plot(2θ, i_calc)`, `scatter(2θ, i_obs)`, `plot(2θ, i_bkg)` , `plot(2θ, i_diff)`,  `bar(2θ_hkl, const)`, 
- in-situ as waterfall plot

#### Small‑Angle X‑ray Scattering (SAXS) (🟡)
- Intensity vs scattering vector, `plot(q, I(q))`  
- in-situ

#### X-ray total scattering

#### Neutron diffraction (🔴)
- Diffraction pattern, `plot(2θ, intensity)`
    - Possibly with insets
- Rietveld refinement, `plot(2θ, i_calc)`, `scatter(2θ, i_obs)`, `plot(2θ, i_bkg)` , `plot(2θ, i_diff)`,  `bar(2θ_hkl, const)`, 

#### XAS
- XANES
- EXAFS (k-space)
- EXAFS (R-space)
- Wavelet transforms
- Time-resolved as line plot

#### Energy‑Dispersive X‑ray Spectroscopy (EDX/EDS) (🟡)
- Elemental spectrum, `plot(energy, counts)`  

#### Wavelength Dispersive X‑ray Spectroscopy (WDX/WDS) (🟢)
- High resolution spectrum, `plot(energy, counts)`  

#### Electron Energy Loss Spectroscopy (EELS) (🟡)
- Loss spectrum, `plot(energy_loss, intensity)`  

#### X‑ray Photoelectron Spectroscopy (XPS) (🔴)
- Binding energy spectrum, `plot(binding_energy, intensity)`  

#### Auger Electron Spectroscopy (AES) (🟡)
- Auger peaks vs energy, `plot(energy, intensity)`  

#### X‑ray Photon Correlation Spectroscopy (XPCS) (🟢)
- Correlation function, `plot(time, correlation)`  
- in-situ

---

## Mass Spectrometry

#### Electron Ionization (EI) (🟡)
- Mass/charge spectrum (EI), `plot(m/z, intensity)`  
- Mass spectrum (TI-MS), `plot(m/z, intensity)`  
- Time‑of‑flight mass spectrum (MALDI-TOF), `plot(m/z, intensity)`  

#### Secondary Ion Mass Spectrometry (SIMS) (🟡)
- Mass spectrum & depth profile, `plot(m/z, intensity)`
- `plot(depth, concentration)`  
- in-situ

---

## Nuclear Spectroscopy

#### Nuclear Magnetic Resonance (NMR) (🔴)
- Chemical shift spectrum, `plot(chemical_shift, intensity)` 
- 2D techniques 

#### Mössbauer Spectroscopy (MBS) (🟡)
- Absorption vs velocity, `plot(velocity, counts)`  
- in-situ

#### Perturbed Angular Correlation (PAC) (🟢)
- Time correlation, `plot(time, anisotropy)`  
- in-situ

---

## Other Techniques

#### Photon Correlation Spectroscopy / Dynamic Light Scattering (DLS) (🟡)
- Size distribution, `hist()` or `plot(size, intensity)`  
- in-situ

#### Terahertz Spectroscopy (THz) (🟡)
- THz absorbance/transmission, `plot(frequency, intensity)`  
- in-situ

#### Electron Paramagnetic / Spin Resonance (EPR/ESR) (🟡)
- Magnetic field vs intensity, `plot(magnetic_field, intensity)`  

#### Small‑Angle Neutron Scattering (SANS) (🟡)
- Intensity vs q, `plot(q, I(q))`  
- in-situ

#### Rutherford Backscattering Spectrometry (RBS) (🟡)
- Energy spectrum, `plot(energy, counts)`  

#### Spatially Resolved Acoustic Spectroscopy (SRAS) (🟢)
- Acoustic response map, `imshow(x, y, intensity)` or `contourf()`  
- in-situ

---

## Macroscopic Testing

#### Mechanical Testing (tensile, compressive, etc.) (🟢)
- Stress–strain curve, `plot(strain, stress)`  

#### Differential Thermal Analysis (DTA) (🟡)
- Temperature vs signal, `plot(temperature, response)`  

#### Dielectric Thermal Analysis (DEA/DETA) (🟡)
- Dielectric constant vs temperature/frequency, `plot(frequency/temperature, dielectric)`  

#### Thermogravimetric Analysis (TGA) (🟡)
- Mass vs temperature/time, `plot(temperature, mass)`  

#### Differential Scanning Calorimetry (DSC) (🟡)
- Heat flow vs temperature, `plot(temperature, heat_flow)`  

#### Impulse Excitation Technique (IET) (🟢)
- Resonance peaks, `plot(frequency, amplitude)`  

#### Ultrasound Techniques (🟢)
- Signal amplitude vs time, `plot(time, amplitude)`
- Signal amplitude vs frequency`plot(frequency, amplitude)`  

---

## Electrochemistry

### Fundamental Electrochemistry

#### Open Circuit Voltage (OCV) (🔴)
- Potential vs time (e.g., equilibrium or relaxation behavior), `plot(time, voltage)`

#### Cyclic Voltammetry (CV) (🔴)
- Current–potential hysteresis loop (e.g., redox processes), `plot(potential, current)`

#### Linear Sweep Voltammetry (LSV) (🔴)
- Current vs potential (e.g., onset potentials, stability windows), `plot(potential, current)`

#### Differential Pulse Voltammetry (DPV) (🟡)
- Peak current vs potential (e.g., trace analysis), `plot(potential, current)`

#### Square Wave Voltammetry (SWV) (🟡)
- Differential current vs potential, `plot(potential, current)`

### Galvanostatic / Potentiostatic Methods

#### Chronoamperometry (CA) (🔴)
- Current vs time after potential step (e.g., diffusion, kinetics), `plot(time, current)`

#### Chronopotentiometry (CP) (🔴)
- Potential vs time at constant current (e.g., stability, phase changes), `plot(time, voltage)`
    
#### Potentiostatic Intermittent Titration Technique (PITT) (🟡)
- Current vs time during potential steps, `plot(time, current)`

#### Galvanostatic Intermittent Titration Technique (GITT) (🟡)
- Voltage vs time during current pulses, `plot(time, voltage)`

### Battery & Energy Storage Testing

#### Galvanostatic Charge–Discharge (GCD) (🔴)
- Voltage vs capacity or time (e.g., cycling behavior), `plot(capacity, voltage)`; `plot(time, voltage)`

#### Rate Capability Testing (🔴)
- Capacity vs current density (C-rate), `scatter(c_rate, capacity)`

#### Cycling Stability / Aging (🔴)
- Capacity and efficiency vs cycle number, `scatter(cycle, capacity)`, `scatter(cycle, efficiency)`

#### Coulombic Efficiency (🟡)
- Efficiency vs cycle number, `plot(cycle, efficiency)`

### Impedance & Frequency-Domain Methods

#### Electrochemical Impedance Spectroscopy (EIS) (🔴)
- Complex impedance (Nyquist plot), `plot(Z_real, -Z_imag)`
- frequency response (Bode plot), `plot(frequency, magnitude/phase)`

#### Distribution of Relaxation Times (DRT) (🟡)
- Relaxation intensity vs time constant, `plot(tau, gamma)`

### Electrocatalysis

#### Rotating Disk Electrode (RDE) (🔴)
- Current vs potential at different rotation rates, `plot(potential, current)`

#### Rotating Ring-Disk Electrode (RRDE) (🟡)
- Disk and ring currents vs potential, `plot(potential, current)`