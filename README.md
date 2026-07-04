# Autonomous Gazebo Drone Stabilization & Precision Landing

## Overview

This repository features an integrated simulation framework for an autonomous multicopter drone operating within a virtual environment. The project bridges intelligent control algorithms with high-fidelity physical simulation. It features an adaptive PID tuning system that dynamically tracks attitude and altitude parameters alongside a precision waypoint navigation script. The system coordinates taking off from a home position, calculating global GPS coordinates from local meter offsets, navigating to a target location and executing a stabilized, centered touchdown on a specific simulated helipad.

## Problem Statement

Standard autonomous flight configurations often suffer from localized drift, sensor calibration lag, and horizontal position inaccuracies during final descents, preventing reliable precision landings. Additionally, static PID parameters fail to account for simulation environments or varying aerodynamic loads. This project addresses these limitations by developing a software-in-the-loop (SITL) automation pipeline that dynamically monitors PID rates and utilizes localized GPS coordinate translation vectors to guide a drone safely to a precise offset landing matrix.

## Tech Stack

- **PX4 Autopilot** — Flight control firmware running in Software-In-The-Loop (SITL) mode
- **Gazebo** — Physics simulation environment hosting the drone model and the custom cluttered world with the helipad
- **MAVSDK (Python)** — Offboard API used to connect to PX4, read/write parameters, and issue action/telemetry commands
- **Python 3 / asyncio** — All mission logic is written as asynchronous coroutines to handle concurrent telemetry streams (position, velocity, health) without blocking
- **MAVLink** — Underlying communication protocol between the scripts and PX4 SITL (`udpin://0.0.0.0:14540`)

## Repository Structure

```
├── demo_video.mp4        # Screen recording of a successful autonomous landing on provided helipad
├── landing_script.py     # Precision navigation and helipad targeting script
├── pid_tuning.py         # Baseline PID readout, adaptive vertical-velocity correction, final gain logging
├── report.pdf            # Write-up including tuning process, parameters modified, challenges faced, final approach
└── README.md             # Project documentation
```

## Features

- **Asynchronous Telemetry Snapshotting:** Solves blocking/ hanging issues by capturing real-time hardware and telemetry states utilizing clean asynchronous stream iterators.
- **Local-to-Global Coordinate Translation:** Utilizes an equirectangular approximation algorithm incorporating Earth's equatorial radius to map local $(X, Y)$ meter targets into precise global GPS coordinates.
- **Background Adaptive Engine:** Concurrently monitors and logs multi-axis rate parameters in the background while the vehicle handles main flight sequences.
- **Precision Descent Stabilization Check:** Tracks real-time velocity and distance parameters, holding the exact absolute position over the helipad until horizontal drift settles before letting the final descent cycle execute.

## Methodology

- **Pre-Flight & Handshake Synchronization:**
The scripts initialize an asynchronous connection string over UDP loopback. The system queries immediate telemetry states using single-frame snapshots to fetch initial home positions and absolute heights without locking up the MAVSDK listener loop.
- **Parameter Extraction & Calibration Hold:**
While a background task monitors and logs multi-axis attitude and altitude rate constants, the main thread triggers an arm command. It introduces a calculated delay to allow the simulated IMU/EKF2 internal sensor calibration parameters to stabilize cleanly before launching.
- **Kinematic Navigation:**
Using the home GPS coordinates as a baseline, local offsets are translated into a global flight plan. The drone climbs to a relative altitude of 5 meters. Absolute altitude commands (AMSL) are computed programmatically:
$$\text{Target Altitude} = \text{Home Altitude} + 5.0\text{m}$$
This formula ensures the values are accepted by the PX4 firmware constraints without command rejection.
- **Precision Centering & Landing Loop:**
The drone traverses the airspace toward the calculated coordinates. An active loop samples real-time position discrepancies and horizontal flight speeds. Once the vehicle maintains a position within a tight tolerance threshold and its velocity approaches zero, the loop breaks, a micro-correction hold is executed and the final autonomous landing sequence is completed.
