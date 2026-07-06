# Autonomous Drone Stabilization and Precision Landing

A submission for the PX4 PID Tuning & Precision Landing problem statement for AeroHaul 2026, built using the following framework:

- PX4-SITL
- Gazebo Classic
- MAVSDK Python
- Custom `safe_landing.world` helipad environment

This repository documents the PID tuning process and the autonomous flight logic used to stablize the drone, take off, navigate to and land on the helipad.

---

## Demo

(#demo)

[![Watch the demo](assets/thumbnail.png)](demo_video.mp4)

---

## Features

- Two independent autonomous landing implementations:
  - PX4 mission-based navigation script (`mission.py`)
  - Manually sequenced guided flight script (`landing_script_v2.py`)
- PID-tuned rate and velocity controllers for stable flight
- Continuous position feedback during approach and descent
- Local-to-global coordinate conversion for the helipad target

---

## Objectives

The objective was to stabilize the drone that exhibited high-frequency oscillations and significant altitude drift and autonomously navigate the drone and perform a precision landing on a designated helipad.

---

## Repository Structure

```
AutonomousLanding/
│
├── README.md
├── demo_video.mp4
├── report.pdf
│
├── mission.py
├── landing_script_v2.py
├── pid_tuning.py
│
└── asset/
    └── thumbnail.png
```

> Note: `pid_tuning.py` is included as a reference for the tuning process described in `report.pdf`. The final tuned parameter values have already been applied directly within `mission.py` and `landing_script_v2.py` — and does not need to be run separately to reproduce the demo.

---

## Running the Simulation

Start PX4 SITL with the helipad world:

```
cd PX4-Autopilot
PX4_SITL_WORLD=safe_landing make px4_sitl gazebo-classic
```

In another terminal, run either landing script:

```
python3 mission.py
```

or

```
python3 landing_script_v2.py
```

---

## Workflow Pipeline

```text
Drone Connection
        │
        ▼
Telemetry & Position Validation
        │
        ▼
Arming and Autonomous Take-off
        │
        ▼
Target Coordinate Computation
        │
        ▼
Autonomous Navigation
        │
        ▼
Arrival Verification
        │
        ▼
Landing Command
        │
        ▼
Touchdown
```
---

## Project Documentation


See `report.pdf` for the complete project report, including the PID tuning process, autonomous landing approach, parameter modifications and challenges encountered.
