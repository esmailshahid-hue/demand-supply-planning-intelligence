"""Earliest application-owned monotonic timestamp; standard library only."""
from time import perf_counter

STARTED = perf_counter()
