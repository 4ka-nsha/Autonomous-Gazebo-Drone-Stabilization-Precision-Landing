#!/usr/bin/env python3
import asyncio
from mavsdk import System

# --- PID values to apply before this test flight ---
PID_PARAMS = {
    "MC_ROLLRATE_P": 0.14,
    "MC_ROLLRATE_I": 0.20,
    "MC_ROLLRATE_D": 0.003,

    "MC_PITCHRATE_P": 0.14,
    "MC_PITCHRATE_I": 0.20,
    "MC_PITCHRATE_D": 0.003,

    "MC_YAWRATE_P": 0.20,
    "MC_YAWRATE_I": 0.1,
    "MC_YAWRATE_D": 0.000,

    "MPC_Z_VEL_P_ACC": 3.80,
    "MPC_Z_VEL_I_ACC": 2.0,
    "MPC_Z_VEL_D_ACC": 0.0,
}

TAKEOFF_ALTITUDE = 3.0  # meters
HOVER_TIME = 8          # seconds to hover before landing


async def print_status_text(drone):
    try:
        async for status_text in drone.telemetry.status_text():
            print(f"[{status_text.type}] {status_text.text}")
    except asyncio.CancelledError:
        return


async def run():
    drone = System()
    await drone.connect(system_address="udp://:14540")

    status_task = asyncio.ensure_future(print_status_text(drone))

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("-- Connected to drone!")
            break

    print("-- Applying PID parameters")
    for name, value in PID_PARAMS.items():
        await drone.param.set_param_float(name, value)
        print(f"   Set {name} = {value}")

    # Give the flight controller a moment to settle after param changes
    await asyncio.sleep(2)

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        print(f"   gps_ok={health.is_global_position_ok} home_ok={health.is_home_position_ok}")
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    status_task.cancel()


if __name__ == "__main__":
    asyncio.run(run())