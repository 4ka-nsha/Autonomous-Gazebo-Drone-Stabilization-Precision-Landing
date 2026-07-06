#!/usr/bin/env python3
import asyncio
import math
import logging
from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan

logging.basicConfig(level=logging.INFO)


TARGET_NORTH_M = 2.0 #move 2 units north of initial position
TARGET_EAST_M = 4.0 #move 4 units east of initial position
CRUISE_ALT_M = 3.0  # meters, altitude while flying to the target
CRUISE_SPEED_MS = 5

# --- PID values to apply before this test flight ---
PID_PARAMS = {
    "MC_ROLLRATE_P": 0.16,
    "MC_ROLLRATE_I": 0.20,
    "MC_ROLLRATE_D": 0.003,

    "MC_PITCHRATE_P": 0.16,
    "MC_PITCHRATE_I": 0.20,
    "MC_PITCHRATE_D": 0.003,

    "MC_YAWRATE_P": 0.20,
    "MC_YAWRATE_I": 0.1,
    "MC_YAWRATE_D": 0.000,

    "MPC_Z_VEL_P_ACC": 3.70,
    "MPC_Z_VEL_I_ACC": 2.0,
    "MPC_Z_VEL_D_ACC": 0.0,
}

async def print_status_text(drone):
    try:
        async for status_text in drone.telemetry.status_text():
            print(f"[{status_text.type}] {status_text.text}")
    except asyncio.CancelledError:
        return



def local_offset_to_global(lat, lon, north_m, east_m):
    """Convert a north/east offset in meters to an absolute lat/lon."""
    earth_radius = 6378137.0
    d_lat = north_m / earth_radius
    d_lon = east_m / (earth_radius * math.cos(math.pi * lat / 180))
    return lat + math.degrees(d_lat), lon + math.degrees(d_lon)


async def run():
    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")

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

    print_mission_progress_task = asyncio.ensure_future(print_mission_progress(drone))
    running_tasks = [print_mission_progress_task]
    termination_task = asyncio.ensure_future(observe_is_in_air(drone, running_tasks))

    print("Waiting for home position...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            break
    home = await drone.telemetry.home().__anext__()

    target_lat, target_lon = local_offset_to_global(
        home.latitude_deg, home.longitude_deg, TARGET_NORTH_M, TARGET_EAST_M
    )
    print(f"-- Helipad target: lat={target_lat:.7f}, lon={target_lon:.7f}")

    # Single mission item: fly to the helipad and land there directly
    # (vehicle_action=LAND ends the mission with a landing at this waypoint,
    # so no separate RTL/land call is needed afterward).
    mission_items = [
        MissionItem(
            target_lat,
            target_lon,
            CRUISE_ALT_M,
            CRUISE_SPEED_MS,
            False,  # is_fly_through -- stop at the waypoint before landing
            float("nan"),
            float("nan"),
            MissionItem.CameraAction.NONE,
            float("nan"),
            float("nan"),
            float("nan"),
            float("nan"),
            float("nan"),
            MissionItem.VehicleAction.LAND,
        )
    ]

    mission_plan = MissionPlan(mission_items)
    await drone.mission.set_return_to_launch_after_mission(False)

    print("-- Uploading mission")
    await drone.mission.upload_mission(mission_plan)

    print("-- Arming")
    await drone.action.arm()

    print("-- Starting mission")
    await drone.mission.start_mission()

    await termination_task

    status_task.cancel()


async def print_mission_progress(drone):
    async for mission_progress in drone.mission.mission_progress():
        print(f"Mission progress: {mission_progress.current}/{mission_progress.total}")


async def observe_is_in_air(drone, running_tasks):
    was_in_air = False
    async for is_in_air in drone.telemetry.in_air():
        if is_in_air:
            was_in_air = is_in_air
        if was_in_air and not is_in_air:
            for task in running_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            await asyncio.get_event_loop().shutdown_asyncgens()
            return


if __name__ == "__main__":
    asyncio.run(run())