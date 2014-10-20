class StackException(Exception):
    pass


class BlueprintException(Exception):
    pass


class NoAdminException(Exception):
    pass


class IncompatibleVersionException(Exception):
    pass


class InvalidVersionStringException(ValueError):
    pass
