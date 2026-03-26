# CS4632_RACING_SIM
Official repository for the **Stochastic Motorsport Performance Simulator** for CS 4632 Modeling and Simulation.

## Overview
This project is a custom-built Python simulation that models motorsport race performance using physics-inspired equations, stochastic variability, and Monte Carlo trials. The simulation focuses on how vehicle setup, environmental conditions, tire strategy, and driver behavior interact to affect lap times and race outcomes.

This implementation is written from scratch in Python and does **not** rely on prebuilt simulation frameworks or premade simulation engines.

## Current M3 Implementation
Milestone 3 completes the core simulator and adds comprehensive data collection, a configuration system, and systematic execution of 12 documented simulation runs. Key changes since M2:

- **N-participant generalization** — the simulator now supports any number of drivers/cars, up from the hardcoded two-driver limit in M2
- **Wetness/tire sensitivity rebalancing** — smoothstep grip blending, traction-limited acceleration, grip-aware braking, and visibility penalties distribute performance across multiple dimensions rather than tire choice alone
- **JSON configuration system** — every run is defined by a self-contained JSON config file; the CLI supports single-config runs, batch `--run-all`, and parameter overrides
- **Full data export** — per-run output includes time-series CSV (trial × lap × entrant), segment-level events CSV, summary JSON, config JSON, and a master run index
- **12 documented runs** varying weather, field size, lap count, track complexity, tire strategy, and trial count

## What Is Implemented
- `Entrant` dataclass pairing a `Driver` with a `RaceCar`
- `Tire.mu_effective()` with smoothstep blending for gradual grip transitions
- `Driver.skill_factor()` multiplicative lap-time scaling by experience/aggressiveness
- `SimulationEngine` with:
  - aerodynamic drag and downforce (`compute_aero`)
  - friction-limited corner speed iteration (`compute_corner_vmax`)
  - traction-limited straight-line acceleration (`_traction_limited_accel`)
  - grip-aware braking deceleration (`_wet_brake_decel`)
  - visibility reaction-time penalty (`_visibility_penalty`)
  - detailed segment/lap/race data collection
  - N-entrant Monte Carlo trial execution
- `SimConfig` with JSON loading, CLI arg parsing, and validation
- `DataCollector` writing per-run CSV/JSON files and master index
- 12 preset configs in `configs/` covering dry, wet, cloudy, foggy, sprint, endurance, complex track, simple track, large field, and tire strategy scenarios

## Scope Updates From Original Proposal
Several items from the original project board were completed, partially addressed, or intentionally deferred during M3. These decisions were driven by the M2 feedback priorities (wetness sensitivity, CSV export, N-participant support) and the goal of producing a defensible, data-ready simulator rather than adding breadth at the cost of depth.

### Completed in M3 (moved from Todo/In Progress)
- **Tune tire friction values (#18)** — mu values recalibrated with smoothstep blending so per-lap gaps fall within stochastic noise, producing probabilistic rather than deterministic outcomes
- **Tune aerodynamic coefficients (#19)** — cars now have genuine tradeoffs (high-downforce/high-drag vs low-drag/low-downforce) instead of one car dominating every dimension
- **Export results to CSV (#20)** — full DataCollector pipeline: timeseries CSV, events CSV, summary JSON, config JSON, and master run index
- **Add configurable simulation parameters (#21)** — JSON config files, CLI arg parsing, parameter validation, default presets, and batch `--run-all` mode
- **Refine braking model before corners (#24)** — `_wet_brake_decel()` degrades braking proportionally with reduced tire grip in wet conditions
- **Refine wetness/tire sensitivity balance (#16)** — the primary M2 feedback item, addressed through five physics changes across straights, corners, braking, and visibility
- **Implement first-pass straight-line dynamics (#26)** — `_traction_limited_accel()` limits acceleration by whichever is lower: engine output or tire traction

### Partially Addressed
- **Improve segment transition realism (#22)** — braking transitions are now grip-aware, but the core model still passes exit speed directly as entry speed to the next segment without a coasting phase. A full lift-and-coast model was deprioritized in favor of the sensitivity rebalancing work.
- **Define clearer suspension impact (#23)** — `suspension_factor` is a configurable per-car parameter that scales tire mu_effective. A richer multi-parameter suspension model was deferred because the current single-factor approach is sufficient for the tire-strategy sensitivity analysis the simulation targets.
- **Add explicit powertrain / acceleration model (#25)** — traction-limited acceleration was added so grip constrains straight performance in wet conditions. A full torque-curve / gear-ratio powertrain was descoped because the simulation focuses on tire strategy and environmental sensitivity, not drivetrain engineering.

### Updates To Project Scope 
- **Extract parameter values from references (#30)** — current values are calibrated for balanced competitive outcomes; M4 validation will compare simulation behavior against published performance data
- **Add parameter details to UML method definitions (#31)** — architecture documentation is maintained in this README; formal UML updates are planned for the M5 final report
- **Fuel load and pit-stop strategies** — out of scope for the current simulation model
- **Tire degradation over race distance** — planned for potential M4/M5 extension if time allows
- **Visualization and charting** — planned for M4 analysis phase

## Changes From M2
This implementation addresses Milestone 2 feedback by:
- **Fixing the wetness/tire sensitivity imbalance**: replaced linear grip interpolation with a smoothstep S-curve that widens the crossover zone; added traction-limited acceleration, grip-aware braking, and a visibility penalty so that wet conditions affect straights and braking, not just corners
- **Implementing CSV/JSON export**: the `DataCollector` writes four files per run (config, timeseries, events, summary) plus a master index
- **Expanding beyond two drivers/cars**: refactored all simulation data structures to support N entrants; demonstrated with runs of 3, 4, and 6 participants
- **Adding a configuration system**: JSON config files with CLI support, parameter validation, and default scenario presets

## Dependencies
This project uses only the Python standard library and requires no external packages.

## Installation Instructions

### Requirements
- Python 3.10 or newer
- A terminal or command prompt
- No external libraries required

### Setup
1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   ```
2. Open the project directory:
   ```bash
   cd CS4632_RACING_SIM
   ```
3. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   ```
   On Windows:
   ```bash
   venv\Scripts\activate
   ```
   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

## Usage

### Run a single configuration
```bash
python main.py --config configs/run_001_baseline_dry.json
```

### Run all 12 preset configurations
```bash
python main.py --run-all
```

### Run with parameter overrides
```bash
python main.py --config configs/run_001_baseline_dry.json --seed 999 --num-trials 500
```

### Run with defaults (no config file)
```bash
python main.py
```

### CLI Options
| Flag | Description |
|------|-------------|
| `--config PATH` | Path to a JSON configuration file |
| `--run-all` | Run every `.json` config in `configs/` sequentially |
| `--seed N` | Override the random seed |
| `--num-laps N` | Override the number of laps |
| `--num-trials N` | Override the number of Monte Carlo trials |
| `--run-id ID` | Override the run identifier |

## Output Structure
Each run produces a directory under `output/`:
```
output/
├── run_index.json              # Master index of all runs
├── run_001/
│   ├── run_001_config.json     # Full parameter snapshot
│   ├── run_001_timeseries.csv  # One row per trial × lap × entrant
│   ├── run_001_events.csv      # One row per trial × lap × entrant × segment
│   └── run_001_summary.json    # Aggregate statistics
├── run_002/
│   └── ...
```

### File Descriptions
| File | Format | Contents |
|------|--------|----------|
| `*_config.json` | JSON | Track layout, environment, entrant details, random seed |
| `*_timeseries.csv` | CSV | `trial, lap, entrant, lap_time, cumulative_time, weather, wetness` |
| `*_events.csv` | CSV | Segment-level: entry/exit speed, segment time, mu_effective |
| `*_summary.json` | JSON | Per-entrant avg/std/min/max times, wins, win percentage |
| `run_index.json` | JSON | Run metadata: ID, description, execution time, best performer |

## Configuration File Format
Each JSON config specifies:
```json
{
  "run_id": "001",
  "description": "Baseline dry conditions",
  "random_seed": 100,
  "num_laps": 5,
  "num_trials": 200,
  "collect_detail": true,
  "track": { "name": "...", "num_pairs": 6, "straight_range": [...], ... },
  "environment": { "weather": "Sunny", "wetness": 0.05, "visibility": 0.95 },
  "entrants": [
    {
      "driver": { "name": "Hamilton", "experience": 9.0, "aggressiveness": 0.7 },
      "car": { "name": "Mercedes", "mass": 798.0, "cd": 0.90, ... },
      "tire": { "compound": "DRY", "mu_dry": 1.04, "mu_wet": 0.88 }
    }
  ]
}
```

## Preset Configurations (12 Runs)
| Run | Description | Params Varied |
|-----|-------------|---------------|
| 001 | Baseline dry | Default (Sunny, 3 entrants, 5 laps) |
| 002 | Baseline wet | weather=Rainy, wetness=0.80 |
| 003 | Cloudy mixed | weather=Cloudy, wetness=0.30 |
| 004 | Large field dry | 6 entrants, Sunny |
| 005 | Large field wet | 6 entrants, Rainy |
| 006 | Long race | num_laps=10 |
| 007 | Sprint | num_laps=1 |
| 008 | Complex track | num_pairs=8, tight corners |
| 009 | Simple track | num_pairs=2, wide corners |
| 010 | High trials | num_trials=500, 4 entrants |
| 011 | Wrong strategy | All WET tires in dry conditions |
| 012 | Foggy mixed | Foggy, visibility=0.35, 4 entrants |

## Architecture Overview

### Main Components
- `main.py` — entry point, orchestrates config → simulation → data export
- `src/config.py` — JSON config loading, CLI parsing, validation, default entrants
- `src/simulation.py` — physics engine, lap/race/trial simulation, N-entrant support
- `src/data_collector.py` — CSV/JSON export, master index management
- `src/entrant.py` — `Entrant` dataclass pairing `Driver` + `RaceCar`
- `src/track.py` — `Track` and `TrackSegment` generation
- `src/environment.py` — weather, wetness, visibility conditions
- `src/tire.py` — tire compound friction model with smoothstep blending
- `src/car.py` — vehicle parameters (mass, aero, braking, top speed)
- `src/driver.py` — driver experience, aggressiveness, stochastic variance, skill factor
- `src/utils.py` — `RaceMetrics`, `EntrantMetrics`, statistical helpers

### Data Flow
```
JSON Config → SimConfig → build_track / build_environment / build_entrants
                           ↓
                    SimulationEngine.run_trials()
                           ↓
              (RaceMetrics, list[TrialResult])
                           ↓
                    DataCollector.save_run()
                           ↓
              output/run_XXX/ (CSV + JSON files)
```

## Project Structure
```
CS4632_RACING_SIM/
├── main.py
├── README.md
├── requirements.txt
├── .gitignore
├── configs/
│   ├── run_001_baseline_dry.json
│   ├── run_002_baseline_wet.json
│   ├── ... (12 config files)
│   └── run_012_mixed_strategy_foggy.json
├── src/
│   ├── car.py
│   ├── config.py
│   ├── data_collector.py
│   ├── driver.py
│   ├── entrant.py
│   ├── environment.py
│   ├── simulation.py
│   ├── tire.py
│   ├── track.py
│   └── utils.py
├── output/
│   ├── run_index.json
│   ├── test_results.csv
│   └── run_001/ ... run_012/
└── docs/
    └── Project_BOARD.png
```

## Troubleshooting
- If `python main.py` does not run, confirm that Python 3.10+ is installed.
- If import errors occur, make sure you are running from the project root directory.
- If `--run-all` finds no configs, verify the `configs/` directory contains `.json` files.
- If output is not created, verify the `output/` directory exists and is writable.

## Notes
This is a Milestone 3 submission demonstrating complete implementation and systematic testing. The data collected here will serve as the foundation for the M4 analysis and validation phase.
