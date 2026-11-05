# INTEGRITY CODE SERIES Week 3 — F1 Lap Simulation

**INTEGRITY CODE SERIES  |  Week 3**

[![CI](https://github.com/felipearocha/integrity-code-series-week3-f1-lap-simulation/actions/workflows/ci.yml/badge.svg)](https://github.com/felipearocha/integrity-code-series-week3-f1-lap-simulation/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests: 9 passing](https://img.shields.io/badge/tests-13%20passing-brightgreen.svg)](src/validation/validate_physics.py)

Physics-informed F1 lap simulation: six first-order state equations and an algebraic
slip-angle proxy, integrated along arc length (space-marched scheme).

## What this repository is

A reproducible, physics-grounded lap simulation with:
- Six integrated states: aero mode $m$, speed $v$, tyre temperature $T$, wear, SOC and fuel
- An algebraic slip-angle proxy $\beta$, computed from speed and curvature at each node
- First-order spatial aero mode filter
- Gaussian thermal grip window
- ERS regen/deploy gate logic
- Full longitudinal dynamics with traction ceiling

No proprietary data. No ML. Classical numerical integration only. See [Limitations](#limitations)
for what the lap time does and does not mean.

## Results

Default run (`python run_all.py`), measured on this repository:

| Output | Value |
|---|---|
| Lap time | 51.94 s |
| Average speed | 228.7 km/h |
| Top speed | 276.0 km/h |
| SOC, start to end of lap | 85.0% to 36.3% |
| Tyre temperature range | 40.0 to 55.0 C |
| Effective friction | 0.40 at every node (the lower clip) |
| Wear at end of lap | 1.77% |
| Fuel used | 1.72 kg |
| Peak lateral demand | 8.27 g |

These are outputs of a synthetic track and assumed coefficients, not a prediction for any real
car or circuit.

## Governing Equations

[**view the full rendered reference**](https://htmlpreview.github.io/?https://github.com/felipearocha/integrity-code-series-week3-f1-lap-simulation/blob/main/docs/equations.html)

Full rendered (MathJax) reference: **[docs/equations.html](docs/equations.html)**; open it in any browser.
Every relation below is transcribed from `src/simulation/physics_model.py`; standard-mechanics
relations are tagged `[SOURCE]` and model-specific proxies/coefficients `[ASSUMED]` in the rendered page.

**Aero mode filter (spatial ODE):**

```math
\frac{dm}{ds} \;=\; \frac{m_{\text{raw}} - m}{\tau_{\text{aero}}}, \qquad \tau_{\text{aero}} = 40\ \text{m}
```

with $m$ the aero mode (0 high downforce, 1 low drag), $m_{\text{raw}}$ the mode requested at arc length $s$ [m],
and $\tau_{\text{aero}}$ the smoothing length.

**Aerodynamic drag and downforce:**

```math
F_{\text{drag}} \;=\; \tfrac{1}{2}\,\rho\,C_d(m)\,A\,v^{2}, \qquad F_{\text{down}} \;=\; \tfrac{1}{2}\,\rho\,C_l(m)\,A\,v^{2}
```

with $\rho$ the air density [kg/m³], $C_d$ and $C_l$ the blended coefficients, $A$ the reference area [m²] and $v$ the speed [m/s].

**Traction ceiling:**

```math
F_{\text{trac,max}} \;=\; \mu_{\text{eff}}\,\bigl(m_{\text{car}}\,g + F_{\text{down}}\bigr)
```

with $m_{\text{car}}$ the car mass [kg] and $g$ gravity [m/s²]. Drive force is
$F_{\text{drive}} = \min(F_{\text{trac,max}},\, P_{\text{drive}}/v)$.

**Master equation of motion:**

```math
m_{\text{car}}\,\frac{dv}{dt} \;=\; F_{\text{drive}} - F_{\text{drag}} - F_{\text{roll}} - F_{\text{grade}} - F_{\text{brake}}
```

**Slip-angle proxy (algebraic):**

```math
\beta \;=\; \operatorname{clip}\!\left(0.35\,\arctan\frac{v^{2}\kappa}{g},\; -0.25,\; 0.25\right)
```

with $\kappa$ the local curvature [1/m].

**Tyre temperature ODE:**

```math
\frac{dT}{dt} \;=\; k_{\text{heat}}\,E_{\text{slip}} - k_{\text{cool}}\,(T - T_{\text{track}}), \qquad E_{\text{slip}} \;=\; \bigl(|\beta| + 0.25\,b\bigr)\,v^{2}\cdot 0.1
```

with $T$ the tyre temperature [C], $T_{\text{track}}$ the track temperature, $b$ the brake proxy (0 to 1)
and $k_{\text{heat}}$, $k_{\text{cool}}$ the heating and cooling coefficients `[ASSUMED]`.

**Gaussian grip window:**

```math
f_T \;=\; \exp\!\left(-\frac{(T - T_{\text{opt}})^{2}}{2\,\sigma^{2}}\right), \qquad \mu_{\text{eff}} \;=\; \operatorname{clip}\bigl(\mu_0\,f_T\,(1 - 10^{4}\,k_w\,w),\; 0.40,\; 2.20\bigr)
```

with $T_{\text{opt}}$ the peak grip temperature, $\sigma$ the window half-width, $\mu_0$ the baseline friction,
$k_w$ the wear coefficient and $w$ the wear state (0 to 1).

**Wear ODE:**

```math
\frac{dw}{dt} \;=\; k_w\,E_{\text{slip}}\,\bigl[\,0.6 + 0.8\,(1 - f_T)\,\bigr]
```

**ERS SOC ODE:**

```math
\frac{d\,\text{SOC}}{dt} \;=\; -\frac{P_{\text{bat}}}{E_{\text{bat}}}
```

with $P_{\text{bat}}$ the battery power [W], positive on deploy, and $E_{\text{bat}}$ the usable energy [J].

**Space-marched integration:**

```math
\Delta t_i \;=\; \frac{\Delta s}{v_i\,\cos\beta_i + \varepsilon}, \qquad t_{\text{lap}} \;=\; \sum_i \Delta t_i
```

with $\Delta s = L/N$ the node spacing and $\varepsilon = 10^{-3}$ m/s.

## Key parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| m_car     | 768 kg | Car + driver mass |
| L         | 3300 m | Track length |
| N         | 1600   | Spatial nodes |
| T_opt     | 95 C   | Peak grip temperature |
| sigma     | 20 C   | Thermal window half-width |
| E_bat     | 4.0 MJ | Battery energy |
| P_deploy_max | 350 kW | MGU-K deploy ceiling |
| P_regen_max  | 250 kW | Regen ceiling |

## Outputs

| File | Description |
|------|-------------|
| lap_telemetry.png | 6-panel: v, T, mu, SOC, P_MGUK, wear |
| thermal_grip_map.png | mu_eff contour vs T and wear |
| sensitivity_v_mu.png | Lap time sensitivity to mu0 and T_opt |
| residual_energy.png | ERS energy audit with SOC |
| track_heatmap.png | XY track colored by speed |
| tyre_thermal_evolution.gif | Animated thermal/grip/SOC evolution |

## Repository structure

```
integrity-code-series-week3-f1-lap-simulation/
├── src/
│   ├── simulation/
│   │   └── physics_model.py      # All governing equations + integrator
│   ├── visualization/
│   │   ├── plot_lap.py           # 5 static visualizations
│   │   └── generate_gif.py       # Animated GIF of tyre thermal evolution
│   └── validation/
│       └── validate_physics.py   # 13 physics consistency tests
├── docs/
│   └── equations.html            # Rendered (MathJax) governing-equations reference
├── notebooks/
│   └── explore_lap.ipynb         # Optional: interactive exploration
├── assets/
│   └── outputs/                  # Generated at run time — all figures + GIF saved here
├── run_all.py                    # Master execution script
├── pytest.ini                    # Test discovery config (collects the validation tests)
├── requirements.txt
├── CHANGELOG.md
├── CITATION.cff
├── LICENSE
└── README.md
```

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run everything
python run_all.py
```

This single command runs validation, simulation, all visualizations,
and the GIF generator in the correct dependency order.

### Individual modules

```bash
# Physics validation only
python src/validation/validate_physics.py

# Simulation only
python src/simulation/physics_model.py

# Visualizations only (runs the simulation itself)
python src/visualization/plot_lap.py

# GIF only
python src/visualization/generate_gif.py
```

## Reproducibility

Results are deterministic. Random seed is fixed at 42 in track geometry
generation. Running run_all.py twice produces identical outputs.

## Limitations

- **The grip window is inactive at the default parameters.** Heating is at most about 0.004 K/s
  against cooling of 5.7 K/s at 95 C, so the tyre falls from 55 C to the 40 C floor and
  $\mu_{\text{eff}}$ sits at its 0.40 lower clip at every node. Changing $\mu_0$ does not change
  the lap time, and `sensitivity_v_mu.png` is flat in $\mu_0$. There is no measured tyre data
  here to calibrate $k_{\text{heat}}$, so it stays `[ASSUMED]` and was not retuned.
- **No lateral grip limit.** Cornering speed is not capped by available grip: peak lateral
  demand is 8.27 g. The lap time is therefore optimistic and is not a lap prediction.
- **Fuel is one-way.** Fuel mass is integrated but does not change $m_{\text{car}}$, so it has no
  effect on the lap.
- **Synthetic track.** The circuit is closed (one net revolution, zero end gap) but crosses
  itself twice, and its corners are generated, not taken from a real track.
- **Single lap.** One lap from a 60 km/h start; the end state is not periodic.

## Cybersecurity (STRIDE)

This is a self-contained, offline research simulation: no network calls, no external
inputs, no secrets, and no persisted state beyond generated figures. The STRIDE attack
surface is therefore limited to code and parameter integrity. Mitigations in scope:

- **Tampering** — deterministic run (fixed seed 42) makes any change to code or
  parameters reproducible and diff-visible; the physics-consistency suite
  (`src/validation/validate_physics.py`, 13 tests) fails closed if governing-equation
  behaviour drifts (grip peak, SOC/temperature bounds, wear monotonicity, lap-time range).
- **Information disclosure** — no proprietary data and no ML; all inputs are the
  published `CarParams`/`TrackParams` defaults.
- **Denial of service** — bounded work (`N` spatial nodes, single stint) and clipped
  state variables prevent runaway integration.

Repudiation, Spoofing, and Elevation-of-Privilege are out of scope for a local,
single-user, no-I/O tool.

## Source Confidence Tiers

Every relation in this package is standard classical mechanics or an explicitly
labelled modelling choice — nothing is attributed to a standard or paper it does not
come from. The tiers below are applied honestly in `docs/equations.html`:

- **T1 (SOURCE)** — textbook physics reproduced as-is: Newton's second law
  (longitudinal EOM), the aerodynamic force law $F = \tfrac{1}{2}\rho C A v^{2}$, and the
  explicit space-marched integrator.
- **T2 (derived)** — quantities computed from T1 relations and the model parameters
  (traction ceiling from friction × downforce, slip-energy, lap time as the sum of
  local time steps).
- **T3 (ASSUMED / heuristic)** — model-specific proxies and tuned coefficients: the
  first-order aero-mode smoothing length, the Gaussian grip window, the curvature-based
  slip-angle and brake proxies, and the tyre heating/cooling/wear coefficients. These are engineering
  choices, not measured or standard values, and are tagged `[ASSUMED]` in the rendered
  equations. No external standard, DOI, or literature citation is claimed anywhere in
  this repository.

## Disclaimer

Research tool only. Not for design, fitness-for-service, or safety-critical decisions without site-specific calibration and independent PE review.

This simulation is a physics-grounded teaching and exploration model. It uses no
proprietary data, no measured tyre/aero maps, and no external standard; several
coefficients are engineering assumptions (see Source Confidence Tiers). It is not a
substitute for validated vehicle-dynamics tools.

## License

MIT — Felipe Rocha. See [LICENSE](LICENSE). Usage restrictions, if any, are covered by
the Disclaimer above; the software itself is released under the MIT License.

## How to Cite

If this software contributes to your work, please cite it:

> Rocha, F. (2026). *Integrity Code Series — Week 3 — F1 Lap Simulation* [Computer software]. GitHub. https://github.com/felipearocha/integrity-code-series-week3-f1-lap-simulation

**BibTeX:**

```bibtex
@software{rocha_2026_ics_week3_f1_lap,
  author    = {Rocha, Felipe},
  title     = {{Integrity Code Series --- Week 3 --- F1 Lap Simulation}},
  year      = 2026,
  publisher = {GitHub},
  url       = {https://github.com/felipearocha/integrity-code-series-week3-f1-lap-simulation}
}
```

No archival DOI (e.g. Zenodo) has been minted for this repository yet; cite the GitHub
URL above. When a DOI is issued it will be added here as concept (latest) and version
(pinned) identifiers.

## Escalation Table

| Week | Topic | Key escalation |
|------|-------|---------------|
| **3** | **F1 lap** | **Six state equations (aero mode, v, T_tire, wear, SOC, fuel) space-marched along arc length, with a Gaussian thermal grip window and an ERS deploy/regen gate** |
| 9 | CUI | 3 coupled PDEs, Strang splitting |
| 10 | NNpHSCC | Chen-Sutherby-Xing crack growth, crack colony, COV=61.2% epistemic |
| 11 | Erosion-corrosion | Coupled DNV erosion + NORSOK CO2 + Beggs-Brill flow + G119 synergy + API 579 Part 5 FFS |

## Integrity Code Series

Part of an ongoing series of physics-first integrity simulators by Felipe Rocha:

| # | Repo | Domain |
|---|---|---|
| **Week 3** | **[integrity-code-series-week3-f1-lap-simulation](https://github.com/felipearocha/integrity-code-series-week3-f1-lap-simulation)** | **F1 lap simulation (space-marched ODEs) — this repo** |
| Week 6 | [integrity-code-series-week6-smartphone-galvanic](https://github.com/felipearocha/integrity-code-series-week6-smartphone-galvanic) | Smartphone galvanic corrosion (Laplace + Butler-Volmer) |
| Week 7 | [integrity-code-series-week7-h2-lferw](https://github.com/felipearocha/integrity-code-series-week7-h2-lferw) | LF-ERW H2 conversion (B31.12 + NACE TM0316) |
| Week 8 | [integrity-code-series-week8-creep-fatigue-heater](https://github.com/felipearocha/integrity-code-series-week8-creep-fatigue-heater) | Creep-fatigue 9Cr-1Mo (Norton/Omega + Coffin-Manson) |
| Week 9 | [integrity-code-series-week9-cui](https://github.com/felipearocha/integrity-code-series-week9-cui) | CUI thermohygro-electrochemical (3 PDEs, Strang) |
| Week 10 | [integrity-code-series-week10-nnph-scc](https://github.com/felipearocha/integrity-code-series-week10-nnph-scc) | NNpHSCC full-physics (Chen-Sutherby-Xing + BS 7910) |
| Week 11 | [integrity-code-series-week11-erosion-corrosion-multiphase](https://github.com/felipearocha/integrity-code-series-week11-erosion-corrosion-multiphase) | Erosion-corrosion multiphase (NORSOK M-506 + DNV-RP-O501 + G119 + API 579) |
| Bonus | [Vibration-Accelerated-Corrosion-Coupled-Mechano-Electrochemical-Simulation](https://github.com/felipearocha/Vibration-Accelerated-Corrosion-Coupled-Mechano-Electrochemical-Simulation) | Vibration-accelerated corrosion (SDOF + Butler-Volmer + Archard) |
| Bonus | [synthetic-integrity-digital-twin-piml](https://github.com/felipearocha/synthetic-integrity-digital-twin-piml) | Physics-informed neural-network surrogate |
| Bonus | [integrity-data-foundation](https://github.com/felipearocha/integrity-data-foundation) | Engineering data validation baseline |

## INTEGRITY CODE SERIES

Physics-first engineering.
Secure digital integrity systems.
Operationally defensible decisions.
Verification over visibility.
