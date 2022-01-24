
class FieldSizeError(Exception):
    def __init__(self, length, max_=84):
        super().__init__(f"Maximum supported size for x-axis is {max_}, {length} was given.")


class ShotError(Exception):
    def __init__(self, pos):
        super().__init__(f"Unable to shoot, {pos} was already shot at.")


class LengthError(Exception):
    def __init__(self, given, argument, method, req):
        super().__init__(
            f"Unsupported argument length of {given} (arg: {argument}) of method {method}, {req} is required.")


class InvalidPositionError(Exception):
    def __init__(self, length, ship):
        super().__init__(f"Cannot place ship of length {length} at {ship}.")


class ShipLengthError(Exception):
    def __init__(self, given, req, size):
        super().__init__(
            f"Ship of length {given} cannot be placed, only up to {req} is supported by board of size {size}.")
