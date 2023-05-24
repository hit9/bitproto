import a_bp
import b_bp


def main():
    a = a_bp.A()
    assert a.x == b_bp.X.OK


if __name__ == "__main__":
    main()
