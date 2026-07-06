#!/usr/bin/env python3
import asyncio
import math
from mavsdk import System

SYSTEM_ADDRESS = "udpin://0.0.0.0:14540"


TARGET_NORTH_M = 2.0 # moves 2 units north of initial position
TARGET_EAST_M = 4.0 # moves 4 units east of initial position
CRUISE_ALT_M = 3.0        # meters above home, altitude to fly at before landing
ARRIVAL_RADIUS_M = 0.5    # how close (meters) before triggering land()

# -- this shit converts the x y coordinates to latitude and longitude values

def local_offset_to_global(lat, lon, north_m, east_m):
    """Convert a north/east offset in meters to an absolute lat/lon."""
    earth_radius = 6378137.0
    d_lat = north_m / earth_radius
    d_lon = east_m / (earth_radius * math.cos(math.pi * lat / 180))
    return lat + math.degrees(d_lat), lon + math.degrees(d_lon)


def distance_m(lat1, lon1, lat2, lon2):
    """Haversine distance in meters between two lat/lon points."""
    r = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return r * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

# -- till here

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

    "MPC_Z_VEL_P_ACC": 3.850,
    "MPC_Z_VEL_I_ACC": 2.0,
    "MPC_Z_VEL_D_ACC": 0.0,
}

async def print_status_text(drone):
    try:
        async for status_text in drone.telemetry.status_text():
            print(f"[{status_text.type}] {status_text.text}")
    except asyncio.CancelledError:
        return


async def run():
    drone = System()
    await drone.connect(system_address=SYSTEM_ADDRESS)

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

    print("Waiting for global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    home = await drone.telemetry.home().__anext__()
    target_lat, target_lon = local_offset_to_global(
        home.latitude_deg, home.longitude_deg, TARGET_NORTH_M, TARGET_EAST_M
    )
    target_alt_amsl = home.absolute_altitude_m + CRUISE_ALT_M
    print(f"-- Helipad target: lat={target_lat:.7f}, lon={target_lon:.7f}")

    print("-- Arming")
    await drone.action.arm()

    print("-- Taking off")
    await drone.action.set_takeoff_altitude(CRUISE_ALT_M)
    await drone.action.takeoff()
    await asyncio.sleep(8)

    print("-- Flying to helipad")
    await drone.action.goto_location(target_lat, target_lon, target_alt_amsl, float("nan"))

    async for position in drone.telemetry.position():
        distance = distance_m(
            position.latitude_deg, position.longitude_deg, target_lat, target_lon
        )
        print(f"Distance to helipad: {distance:.2f} m")
        if distance <= ARRIVAL_RADIUS_M:
            print("-- Reached helipad")
            break

    print("-- Landing")
    await drone.action.land()

    async for in_air in drone.telemetry.in_air():
        if not in_air:
            print("-- Landed on helipad")
            break

    status_task.cancel()


if __name__ == "__main__":
    asyncio.run(run())