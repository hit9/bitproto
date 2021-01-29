import time

import drone_bp as bp


def bench_encode(n: int) -> None:
    start = time.time()
    for i in range(n):
        drone = bp.Drone()
        drone.encode()
    end = time.time()
    cost = int((end - start) * 1000000)
    print(
        "called encode {0} times, total {1}ms, per encode {2}us".format(
            n, int(cost / 1000), int(cost / n)
        )
    )


def bench_decode(n: int) -> None:
    b = bytearray(bp.Drone.BYTES_LENGTH)
    start = time.time()
    for i in range(n):
        drone = bp.Drone()
        drone.decode(b)
    end = time.time()
    cost = int((end - start) * 1000000)  # us
    print(
        "called decode {0} times, total {1}ms, per decode {2}us".format(
            n, int(cost / 1000), int(cost / n)
        )
    )


def main() -> None:
    n = 10000
    bench_encode(n)
    bench_decode(n)


if __name__ == "__main__":
    main()
