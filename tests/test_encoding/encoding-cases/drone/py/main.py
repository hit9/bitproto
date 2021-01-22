import drone_bp as bp


def main() -> None:
    # Encode.
    drone = bp.Drone()

    drone.status = bp.DRONE_STATUS_RISING
    drone.position.longitude = 2000
    drone.position.latitude = 2000
    drone.position.altitude = 1080
    drone.flight.pose.yaw = 4321
    drone.flight.pose.pitch = 1234
    drone.flight.pose.roll = 5678
    drone.flight.acceleration[0] = -1001
    drone.flight.acceleration[1] = 1002
    drone.flight.acceleration[2] = 1003
    drone.power.is_charging = False
    drone.power.battery = 98
    drone.propellers[0].id = 1
    drone.propellers[0].direction = bp.ROTATING_DIRECTION_CLOCK_WISE
    drone.propellers[0].status = bp.PROPELLER_STATUS_ROTATING
    drone.network.signal = 15
    drone.network.heartbeat_at = 1611280511628
    drone.landing_gear.status = bp.LANDING_GEAR_STATUS_FOLDED

    s = drone.encode()  # bytearray

    for b in s:
        print(int(b), end=" ")

    # Decode
    drone_new = bp.Drone()
    drone_new.decode(s)

    assert drone_new.status == drone.status
    assert drone_new.position.longitude == drone.position.longitude
    assert drone_new.position.latitude == drone.position.latitude
    assert drone_new.position.altitude == drone.position.altitude
    assert drone_new.flight.pose.yaw == drone.flight.pose.yaw
    assert drone_new.flight.pose.pitch == drone.flight.pose.pitch
    assert drone_new.flight.pose.roll == drone.flight.pose.roll
    assert drone_new.flight.acceleration[0] == drone.flight.acceleration[0]
    assert drone_new.flight.acceleration[1] == drone.flight.acceleration[1]
    assert drone_new.flight.acceleration[2] == drone.flight.acceleration[2]
    assert drone_new.power.is_charging == drone.power.is_charging
    assert drone_new.power.battery == drone.power.battery
    assert drone_new.propellers[0].id == drone.propellers[0].id
    assert drone_new.propellers[0].direction == drone.propellers[0].direction
    assert drone_new.propellers[0].status == drone.propellers[0].status
    assert drone_new.network.signal == drone.network.signal
    assert drone_new.network.heartbeat_at == drone.network.heartbeat_at
    assert drone_new.landing_gear.status == drone.landing_gear.status


if __name__ == "__main__":
    main()
