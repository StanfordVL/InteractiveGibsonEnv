import pybullet as p
from IPython import embed

import igibson
from igibson.object_states.adjacency import VerticalAdjacency
from igibson.object_states.memoization import PositionalValidationMemoizedObjectStateMixin
from igibson.object_states.object_state_base import BooleanState, RelativeObjectState
from igibson.object_states.utils import clear_cached_states, sample_kinematics


class Under(PositionalValidationMemoizedObjectStateMixin, RelativeObjectState, BooleanState):
    @staticmethod
    def get_dependencies():
        return RelativeObjectState.get_dependencies() + [VerticalAdjacency]

    def _set_value(self, other, new_value):
        state_id = p.saveState()

        for _ in range(10):
            sampling_success = sample_kinematics("under", self.obj, other, new_value)
            if sampling_success:
                clear_cached_states(self.obj)
                clear_cached_states(other)
                if self.get_value(other) != new_value:
                    sampling_success = False
                if igibson.debug_sampling:
                    print("Under checking", sampling_success)
                    embed()
            if sampling_success:
                break
            else:
                p.restoreState(state_id)

        p.removeState(state_id)

        return sampling_success

    def _get_value(self, other):
        adjacency = self.obj.states[VerticalAdjacency].get_value()
        return (
            other.get_body_id() in adjacency.positive_neighbors
            and other.get_body_id() not in adjacency.negative_neighbors
        )