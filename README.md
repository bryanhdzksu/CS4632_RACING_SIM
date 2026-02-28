# CS4632_RACING_SIM
This is the official repository for the Stochastic Motorsport Performance Simulator.

## Overview
This project is a custom-built Python simulation for CS 4632. It models motorsport race performance using physics-inspired equations, stochastic variability, and Monte Carlo trials. No prebuilt simulation framework is used.

## Current M2 Implementation
The current milestone includes:
- core entity classes for track, cars, tires, drivers, and environment
- random track generation with alternating straights and corners
- aerodynamic drag and downforce calculations
- friction-limited corner speed calculations
- simple straight-line acceleration and braking transition logic
- wetness sampling for environment conditions
- driver experience to variance mapping
- Monte Carlo race trials with result aggregation
- sample output logging

## What Is Implemented
- `compute_aero()`
- `compute_corner_vmax()`
- straight-segment speed update
- lap simulation
- race simulation for two drivers
- repeated Monte Carlo trials
- summary metrics:
  - average race time
  - standard deviation
  - win counts
  - win probability

## What Is Not Yet Implemented
- advanced powertrain modeling
- pit strategies
- detailed corner entry/exit dynamics
- fuel load effects
- visualization beyond console/file output

## Changes From M1
This implementation directly addresses M1 feedback by:
- defining performance quantitatively as lowest expected race time
- defining wetness range and sampling rules
- defining driver variance as a function of experience
- adding straight-line acceleration logic
- adding braking logic before corners
- defining a concrete track-generation algorithm

## Important Notes
Initial testing shows that race outcomes are currently highly sensitive to wetness and tire selection, with less nuanced tradeoffs than originally intended. This confirms that the core simulation is functioning, while also identifying model balancing and refinement as important next steps.

At this stage:
- the system is producing logical outcomes
- the outcomes respond to environmental changes
- the simulation framework is working end-to-end
- further refinement is needed to make results less binary and more realistic

## How To Run
From the project root, run:

```bash
python main.py