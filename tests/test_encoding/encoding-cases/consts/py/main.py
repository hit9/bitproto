import consts_bp as bp


def main() -> None:
    assert bp.A == 1
    assert bp.B == 6
    assert bp.C == "string"
    assert bp.D == True
    assert bp.E == False
    assert bp.F == True
    assert bp.G == False


if __name__ == "__main__":
    main()
