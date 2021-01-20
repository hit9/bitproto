#include <assert.h>
#include <stdio.h>

#include "example_bp.h"

int main(void) {
    // Encode.
    struct Drone drone = {0};

    drone.status = DRONE_STATUS_RISING;
    drone.position.longitude = 2000;
    drone.position.latitude = 2000;
    drone.position.altitude = 1080;
    drone.flight.acceleration[0] = -1001;
    drone.power.is_charging = false;
    drone.propellers[0].direction = ROTATING_DIRECTION_CLOCK_WISE;

    unsigned char s[BYTES_LENGTH_DRONE] = {0};

    EncodeDrone(&drone, s);

    // Decode.
    struct Drone drone_new = {0};
    DecodeDrone(&drone_new, s);

    assert(drone_new.status == drone.status);

    // Json Formatting.
    char buf[512] = {0};
    JsonDrone(&drone_new, buf);
    printf("%s", buf);

    return 0;
}
