import logging
import gym
import librosa
import numpy as np
import pybullet as p
import os
import random
import time
import glob
import xml.etree.ElementTree as ET

from igibson.tasks.point_nav_random_task import PointNavRandomTask
from igibson.reward_functions.reward_function_base import BaseRewardFunction
from igibson.reward_functions.potential_reward import PotentialReward
from igibson.reward_functions.collision_reward import CollisionReward
from igibson.reward_functions.point_goal_reward import PointGoalReward
from igibson.objects.visual_marker import VisualMarker
from igibson.utils.utils import l2_distance, restoreState


class TimeReward(BaseRewardFunction):
    """
    Time reward
    A negative reward per time step
    """

    def __init__(self, config):
        super().__init__(config)
        self.time_reward_weight = self.config.get(
            'time_reward_weight', -0.01)

    def get_reward(self, task, env):
        """
        Reward is proportional to the number of steps
        :param task: task instance
        :param env: environment instance
        :return: reward
        """
        return self.time_reward_weight

class SAViTask(PointNavRandomTask):
    # reward function
    def __init__(self, env):
        super().__init__(env)
        self.reward_funcions = [
            PotentialReward(self.config), # geodesic distance, potential_reward_weight
            PointGoalReward(self.config), # success_reward
            CollisionReward(self.config),
            TimeReward(self.config), # time_reward_weight
        ]
    
    def sample_initial_pose_and_target_pos(self, env):
        """
        Sample robot initial pose and target position

        :param env: environment instance
        :return: initial pose and target position
        """
        _, initial_pos = env.scene.get_random_point(floor=self.floor_num)
        max_trials = 100
        dist = 0.0
        for _ in range(max_trials):
            cat = random.choice(CATEGORIES)
            scene_files = glob.glob(os.path.join(igibson.ig_dataset_path, "scenes", 
                                                 env.scene_id, f"urdf/{env.scene_id}.urdf"), 
                                   recursive=True)
            sf = scene_files[0]
            tree = ET.parse(sf)
            links = tree.findall(".//link[@category='%s']" % cat)
            if len(links) == 0:
                continue
            link = random.choice(links)
            joint_name = "j_"+link.attrib["name"]
            joint = tree.findall(".//joint[@name='%s']" % joint_name)
            target_pos = [float(i) for i in joint[0].find('origin').attrib["xyz"].split()]
            target_pos = np.array(target_pos)
            
            if env.scene.build_graph:
                _, dist = env.scene.get_shortest_path(
                    self.floor_num,
                    initial_pos[:2],
                    target_pos[:2], entire_path=False)
            else:
                dist = l2_distance(initial_pos, target_pos)
            if self.target_dist_min < dist < self.target_dist_max:
                env.cat = cat
                break
        if not (self.target_dist_min < dist < self.target_dist_max):
            print("WARNING: Failed to sample initial and target positions")
        initial_orn = np.array([0, 0, np.random.uniform(0, np.pi * 2)])
        return initial_pos, initial_orn, target_pos
    
    
    def reset_agent(self, env):
        """
        Reset robot initial pose.
        Sample initial pose and target position, check validity, and land it.

        :param env: environment instance
        """
        reset_success = False
        max_trials = 100

        # cache pybullet state
        # TODO: p.saveState takes a few seconds, need to speed up
        state_id = p.saveState()
        for i in range(max_trials):
            initial_pos, initial_orn, target_pos = \
                self.sample_initial_pose_and_target_pos(env)
            reset_success = env.test_valid_position(
                env.robots[0], initial_pos, initial_orn) and \
                env.test_valid_position(
                    env.robots[0], target_pos)
            p.restoreState(state_id)
            if reset_success:
                break

        if not reset_success:
            logging.warning("WARNING: Failed to reset robot without collision")

        p.removeState(state_id)

        self.target_pos = target_pos
        self.initial_pos = initial_pos
        self.initial_orn = initial_orn
        super(PointNavRandomTask, self).reset_agent(env)