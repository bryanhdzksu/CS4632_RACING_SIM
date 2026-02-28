# CS4632_RACING_SIM
Official repository for the **Stochastic Motorsport Performance Simulator** for CS 4632 Modeling and Simulation.

## Overview
This project is a custom-built Python simulation that models motorsport race performance using physics-inspired equations, stochastic variability, and Monte Carlo trials. The simulation focuses on how vehicle setup, environmental conditions, and driver behavior interact to affect lap times and race outcomes.

This implementation is written from scratch in Python and does **not** rely on prebuilt simulation frameworks or premade simulation engines.

## Current M2 Implementation
The current Milestone 2 implementation establishes a working initial prototype of the simulator. The project now includes:
- core entity classes for track, cars, tires, drivers, and environment
- random track generation with alternating straights and corners
- aerodynamic drag and downforce calculations
- friction-limited corner speed calculations
- simple straight-line acceleration and braking transition logic
- wetness sampling for environment conditions
- driver experience mapped to stochastic performance variance
- Monte Carlo race trials with result aggregation
- sample output logging

This version represents an initial vertical slice of the final simulator and is intended to demonstrate core functionality, not full final realism.

## What Is Implemented
The following features are currently implemented:
- `compute_aero()` for aerodynamic drag and downforce
- `compute_corner_vmax()` for friction-limited corner speed
- straight-segment speed updates
- braking transition logic before corners
- lap simulation across track segments
- race simulation for two drivers
- repeated Monte Carlo trials
- summary metric generation:
  - average race time
  - standard deviation
  - win counts
  - win probability
- console output and file logging

## What Is Not Yet Implemented
The following features are planned for future milestones:
- advanced powertrain modeling
- more detailed corner entry/exit dynamics
- pit strategies
- fuel load effects
- richer parameter tuning from literature sources
- visualization beyond console and text-file output
- more sophisticated balancing between setup factors

## Changes From M1
This implementation directly addresses Milestone 1 feedback by:
- defining performance quantitatively as lowest expected race time
- defining wetness range and sampling rules
- defining driver variance as a function of experience
- adding straight-line acceleration logic
- adding braking logic before corners
- defining a concrete track-generation algorithm
- moving from conceptual equations to executable simulation code

## Dependencies
The current M2 implementation uses only Python standard library modules and does not require external packages.

## Installation Instructions

### Requirements
- Python 3.10 or newer
- A terminal or command prompt
- No external libraries are required for the current milestone

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
4. Run the simulator:
   ```bash
   python main.py
   ```

## Usage
Run the simulator from the repository root:

```bash
python main.py
```

### Current Configuration
The current M2 prototype uses:
- one generated test track per run
- one sampled weather/environment condition per run
- two preconfigured cars
- two preconfigured drivers
- a fixed number of laps and Monte Carlo trials defined in `main.py`

### Expected Output
The simulator currently prints:
- track name and total track length
- number of generated segments
- weather condition and wetness value
- number of laps and Monte Carlo trials
- average race time for both drivers
- standard deviation of race times
- win counts and win probabilities
- best expected performer for the current run

A text copy of the results is also written to:
- `output/sample_results.txt`

## Troubleshooting
- If `python main.py` does not run, confirm that Python 3 is installed and accessible from your terminal.
- If import errors occur, make sure you are running the command from the project root directory.
- If the output file is not created, verify that the `output/` folder exists and is writable.
- If results do not change between runs, check whether a fixed random seed is enabled in `main.py`.

## Architecture Overview
The current implementation follows the conceptual model defined in Milestone 1 and maps directly to the submitted UML design.

### Main Components
- `Track` and `TrackSegment` represent the generated circuit layout using straights and corners.
- `Environment` stores weather, wetness, and visibility conditions.
- `Tire` defines dry and wet friction behavior.
- `RaceCar` stores vehicle parameters such as mass, drag coefficient, downforce coefficient, braking efficiency, suspension factor, and tire choice.
- `Driver` stores experience, aggressiveness, and stochastic performance variance behavior.
- `SimulationEngine` acts as the central controller and handles:
  - aerodynamic calculations
  - corner speed calculations
  - lap simulation
  - race simulation
  - Monte Carlo trial execution
  - metric aggregation

### Relation to UML
The implementation directly follows the UML structure from Milestone 1:
- `SimulationEngine` coordinates the simulation workflow.
- `Track` is composed of multiple `TrackSegment` objects.
- `RaceCar` contains a `Tire`.
- drivers, cars, track, and environment are passed into the simulation engine to compute outcomes.

### Architectural Changes Since M1
The overall structure remains consistent with the original proposal, but the implementation now defines explicit operational rules for:
- straight-line acceleration
- braking before corners
- stochastic driver variance
- wetness sampling and environmental response

These additions make the model more concrete and implementation-ready than the original conceptual design.

## Current Limitations and Early Findings
Initial testing shows that the simulator is functioning end-to-end and producing logically consistent outcomes. Environmental conditions, particularly wetness, clearly affect race results, which confirms that the model is responsive to changing inputs.

However, early testing also shows that race outcomes are currently highly sensitive to wetness and tire selection, which makes the prototype more predictable than intended in some scenarios. This indicates that the core simulation is working, while also identifying balancing and refinement as key next steps.

At this stage:
- the system is producing logical outcomes
- the outcomes respond to environmental changes
- the simulation framework is working end-to-end
- further refinement is needed to make results less binary and more realistic

## Future Improvements
Planned improvements for future milestones include:
- refining powertrain and straight-line dynamics
- improving braking and segment transition realism
- tuning aerodynamic and tire parameters
- linking more parameter values directly to literature sources
- expanding output logging and analysis
- adding more configurability and visualization

## Project Structure
- `main.py` - entry point for running the simulator
- `src/track.py` - track and segment generation
- `src/environment.py` - weather and wetness logic
- `src/tire.py` - tire grip and friction behavior
- `src/car.py` - vehicle parameters
- `src/driver.py` - driver variability model
- `src/simulation.py` - race logic and Monte Carlo trial execution
- `src/utils.py` - helper utilities and metric calculations
- `output/` - saved simulation results

## Notes
This project is an initial implementation milestone and is intended to demonstrate meaningful progress toward the final simulator. Full functionality and full realism are not expected at this stage. The current version establishes the core executable structure that future milestones will refine and expand.