"""Runtime compatibility only. This is not the Pass 2 planning formulation."""
from time import perf_counter
start = perf_counter()
import scipy
from scipy.optimize import Bounds, LinearConstraint, milp
print(f"SciPy {scipy.__version__} import: {perf_counter()-start:.3f}s")
for label in ("cold", "warm"):
    start = perf_counter()
    # One integer x: min x, x >= 1.5. Independent expected solution is x=2.
    result = milp(c=[1.], integrality=[1], bounds=Bounds([0],[10]),
                  constraints=LinearConstraint([[1]], [1.5], [10]), options={"time_limit": 2})
    assert result.success and result.x[0] == 2 and result.fun == 2
    print(f"HiGHS {label}: status {result.status}, x={result.x[0]:.0f}, {perf_counter()-start:.3f}s")
