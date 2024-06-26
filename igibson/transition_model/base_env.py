from igibson.utils.ig_logging import IGLogReader
from igibson.utils.utils import parse_config
import os
import igibson

class BaseEnv:
    def defalt_init(self,demo_path):
        task = IGLogReader.read_metadata_attr(demo_path, "/metadata/atus_activity")
        if task is None:
            task = IGLogReader.read_metadata_attr(demo_path, "/metadata/task_name")

        task_id = IGLogReader.read_metadata_attr(demo_path, "/metadata/activity_definition")
        if task_id is None:
            task_id = IGLogReader.read_metadata_attr(demo_path, "/metadata/task_instance")

        scene_id = IGLogReader.read_metadata_attr(demo_path, "/metadata/scene_id")

        config_filename = os.path.join(igibson.configs_path, "behavior_robot_mp_behavior_task.yaml")
        config = parse_config(config_filename)
        

        config["task"] = task
        config["task_id"] = task_id
        config["scene_id"] = scene_id
        config["robot"]["show_visual_head"] = True
        config["image_width"]=1024
        config["image_height"]=1024
        self.config = config
    
            
    def __init__(self,config=None,demo_path=None,demo_dir=None,demo_name=None,**kwargs) -> None:
        assert config is not None or demo_path is not None or demo_name is not None
        self.config=config
        if demo_dir is not None and demo_name is not None:
            demo_path=os.path.join(demo_dir,demo_name+'.hdf5')
        if demo_path is not None:
            self.defalt_init(demo_path)



