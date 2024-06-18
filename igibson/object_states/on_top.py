import pybullet as p
from IPython import embed

import igibson
from igibson.object_states.adjacency import VerticalAdjacency
from igibson.object_states.memoization import PositionalValidationMemoizedObjectStateMixin
from igibson.object_states.object_state_base import BooleanState, RelativeObjectState
from igibson.object_states.touching import Touching
from igibson.object_states.utils import clear_cached_states, sample_kinematics
from igibson.utils.utils import restoreState
from igibson.object_states.aabb import AABB

MAX_DISTANCE_POS = 0.015
MAX_DISTANCE_NEG = 0.02
class OnTop(PositionalValidationMemoizedObjectStateMixin, RelativeObjectState, BooleanState):
    @staticmethod
    def get_dependencies():
        return RelativeObjectState.get_dependencies() + [Touching, VerticalAdjacency]

    def _set_value(self, other, new_value, use_ray_casting_method=False):
        state_id = p.saveState()

        for _ in range(10):
            sampling_success = sample_kinematics(
                "onTop", self.obj, other, new_value, use_ray_casting_method=use_ray_casting_method
            )
            if sampling_success:
                clear_cached_states(self.obj)
                clear_cached_states(other)
                if self.get_value(other) != new_value:
                    sampling_success = False
                if igibson.debug_sampling:
                    print("OnTop checking", sampling_success)
                    embed()
            if sampling_success:
                break
            else:
                restoreState(state_id)

        p.removeState(state_id)

        return sampling_success

    def _get_value(self, other, use_ray_casting_method=False):
        del use_ray_casting_method


        # redefine the get_value function
        lo,hi=self.obj.states[AABB].get_value()
        other_lo,other_hi=other.states[AABB].get_value()
        flag=True
        # given two segments, check if they overlap
        def is_overlap(a_low, a_high, b_low, b_high):
            return (a_low <= b_low and b_low <= a_high) or \
            (a_low <= b_high and b_high <= a_high) or \
            (a_low <= b_low and b_high <= a_high) or \
            (b_low <= a_low and a_high <= b_high)
        
        if not is_overlap(lo[0], hi[0], other_lo[0], other_hi[0]) or not is_overlap(lo[1], hi[1], other_lo[1], other_hi[1]):
            flag=False
        if (lo+hi)[2]<(other_lo+other_hi)[2]:
            flag=False
        if lo[2]-other_hi[2] > MAX_DISTANCE_POS or other_hi[2]-lo[2] > MAX_DISTANCE_NEG:
            flag=False

        
        if flag:
            return True
        else:
            # # Touching is the less costly of our conditions.
            # # Check it first.
            # if not self.obj.states[Touching].get_value(other):
            #     return False

            # # Then check vertical adjacency - it's the second least
            # # costly.
            # other_bids = set(other.get_body_ids())
            # adjacency = self.obj.states[VerticalAdjacency].get_value()
            # return not other_bids.isdisjoint(adjacency.negative_neighbors) and other_bids.isdisjoint(
            #     adjacency.positive_neighbors
            # )
            return False
