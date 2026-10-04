"""Bull's stable public entry points; lifecycle machinery is shared, not its thesis."""

from quantlab.agents.analyst_worker import (
    BULL_MANDATE as BULL_MANDATE,
)
from quantlab.agents.analyst_worker import (
    PIPELINE as PIPELINE,
)
from quantlab.agents.analyst_worker import (
    AnalystWorker,
)
from quantlab.agents.analyst_worker import (
    bull_mandate as bull_mandate,
)
from quantlab.agents.analyst_worker import (
    create_bull_context as create_bull_context,
)
from quantlab.agents.analyst_worker import (
    search_bull_history as search_bull_history,
)


class BullWorker(AnalystWorker):
    pass
