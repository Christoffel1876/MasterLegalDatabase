"""Hard coverage completeness gate."""

from datetime import datetime, timezone

from geode.orchestration.contracts import QueryState, StageLog, StageStatus
from geode.orchestration.gates import append_gate_result, check_completeness
from geode.orchestration.stages._stub import PassThroughStage


class CheckCompletenessStage(PassThroughStage):
    """Disclose missing required coverage categories."""

    def __call__(self, state: QueryState) -> QueryState:
        """Run coverage completeness verification."""

        state, result = check_completeness(state)
        append_gate_result(state, result)
        state.trace.append(
            StageLog(
                stage_name=self.name,
                status=StageStatus.PASSED,
                message="Completeness verification gate executed.",
                completed_at=datetime.now(timezone.utc),
                details=result.model_dump(mode="json"),
            )
        )
        return state
