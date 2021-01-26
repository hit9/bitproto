#include <assert.h>
#include <stdio.h>
#include <sys/time.h>
#include <time.h>

#include "example_bp.h"

/* Get timestamp (in milliseconds) for now. */
double datetime_stamp_now(void) {
#if defined CLOCK_REALTIME
    struct timespec ts;
    int rc = clock_gettime(CLOCK_REALTIME, &ts);
    assert(rc == 0);
    return ts.tv_sec * 1000 + ts.tv_nsec / 1000000.0;
#else
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (1000000 * tv.tv_sec + tv.tv_usec) / 1000.0;
#endif
}

void encode(unsigned char *s) {
    struct Drone drone = {0};
    EncodeDrone(&drone, s);
}

void decode(unsigned char *s) {
    struct Drone drone_new = {0};
    DecodeDrone(&drone_new, s);
}

void bench_encode(int n, unsigned char *s) {
    double start = datetime_stamp_now();
    for (int i = 0; i < n; i++) {
        encode(s);
    }
    double end = datetime_stamp_now();
    double cost = end - start;
    printf("called encode %d times, total %dms, per encode %dus\n", n,
           (int)(cost), (int)(1000.0 * cost / n));
}

void bench_decode(int n, unsigned char *s) {
    double start = datetime_stamp_now();
    for (int i = 0; i < n; i++) {
        decode(s);
    }
    double end = datetime_stamp_now();
    double cost = end - start;
    printf("called decode %d times, total %dms, per decode %dus\n", n,
           (int)(cost), (int)(1000.0 * cost / n));
}

int main(void) {
    int n = 1000000;
    unsigned char s[BYTES_LENGTH_DRONE] = {0};

    bench_encode(n, s);
    bench_decode(n, s);

    return 0;
}
