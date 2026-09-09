"""Hard evidence faithfulness gate."""

from datetime import datetime, timezone

from geode.orchestration.contracts import QueryState, StageLog, StageStatus
from geode.orchestration.gates import append_gate_result, check_faithfulness
from geode.orchestration.stages._stub import PassThroughStage


class CheckFaithfulnessStage(PassThroughStage):
    """Strip answer sentences that fail the evidence support check."""

    def __call__(self, state: QueryState) -> QueryState:
        """Run evidence faithfulness verification."""

        state, result = check_faithfulness(state)
        append_gate_result(state, result)
        state.trace.append(
            StageLog(
                stage_name=self.name,
                status=StageStatus.PASSED,
                message="Faithfulness verification gate executed.",
                completed_at=datetime.now(timezone.utc),
                details=result.model_dump(mode="json"),
            )
        )
        return state
