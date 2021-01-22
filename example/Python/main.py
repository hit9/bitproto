import example_bp as bp


def main() -> None:
    # Encode.
    drone = bp.Drone()
    drone.status = bp.DRONE_STATUS_RISING
    drone.position.longitude = 2000
    drone.position.latitude = 2000
    drone.position.altitude = 1080
    drone.flight.acceleration[0] = -1001
    drone.power.is_charging = True
    drone.propellers[0].direction = bp.ROTATING_DIRECTION_CLOCK_WISE
    s = drone.encode()  # bytearray

    # Decode
    drone_new = bp.Drone()
    drone_new.decode(s)

    assert drone_new.status == drone.status

    print(drone_new.to_json())


if __name__ == "__main__":
    main()
