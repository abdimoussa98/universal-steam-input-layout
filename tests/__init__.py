"""Canonical test package; ordinary discovery also enforces scenario completeness."""


def load_tests(loader, tests, pattern):
    from tests.runner import discovery_suite
    return discovery_suite(loader, pattern=pattern)
