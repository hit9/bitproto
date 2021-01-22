#include <assert.h>
#include <stdio.h>

#include "drone_extended_bp.h"
#include "drone_origin_bp.h"

int main(void) {
    // Encode extended message.
    struct ExtendedDrone drone = {0};

    drone.status = DRONE_STATUS_LANDING;
    drone.position.altitude = 1314;
    drone.position.latitude = 3126;
    drone.position.longitude = 12126;
    drone.flight.pose.pitch = -1001;
    drone.flight.pose.yaw = -1002;
    drone.flight.pose.roll = 1024;
    drone.flight.field_new = 2;
    drone.propellers[0].id = 1;
    drone.propellers[0].direction = ROTATING_DIRECTION_CLOCK_WISE;
    drone.propellers[0].field_new = 1;
    drone.propellers[1].id = 2;
    drone.propellers[1].direction = ROTATING_DIRECTION_ANTI_CLOCK_WISE;
    drone.propellers[1].field_new = 2;
    drone.network.heartbeat_at = 1611280511628;
    drone.network.signal = 14;

    unsigned char s[BYTES_LENGTH_EXTENDED_DRONE] = {0};
    EncodeExtendedDrone(&drone, s);

    // Output
    for (int i = 0; i < BYTES_LENGTH_EXTENDED_DRONE; i++) printf("%u ", s[i]);

    // Decode with old message
    struct Drone drone_old = {0};
    DecodeDrone(&drone_old, s);

    assert(drone_old.status == drone.status);
    assert(drone_old.position.altitude == drone.position.altitude);
    assert(drone_old.position.latitude == drone.position.latitude);
    assert(drone_old.position.longitude == drone.position.longitude);
    assert(drone_old.flight.pose.pitch == drone.flight.pose.pitch);
    assert(drone_old.flight.pose.yaw == drone.flight.pose.yaw);
    assert(drone_old.flight.pose.roll == drone.flight.pose.roll);
    assert(drone_old.propellers[0].id == drone.propellers[0].id);
    assert(drone_old.propellers[0].direction == drone.propellers[0].direction);
    assert(drone_old.propellers[1].id == drone.propellers[1].id);
    assert(drone_old.propellers[1].direction == drone.propellers[1].direction);
    assert(drone_old.network.heartbeat_at == drone.network.heartbeat_at);
    assert(drone_old.network.signal == drone.network.signal);

    return 0;
}
