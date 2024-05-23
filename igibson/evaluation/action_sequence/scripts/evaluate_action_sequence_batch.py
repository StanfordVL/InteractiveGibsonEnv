import fire
from multiprocessing import Process
import  os
import json
from igibson.evaluation.action_sequence.action_sequence_evaluator import ActionSequenceEvaluator


def evaluate_action_sequence_parsed(demo_dir,actions,demo_name,rst_path):
    os.makedirs(os.path.dirname(rst_path),exist_ok=True)
    ase=ActionSequenceEvaluator(demo_dir=demo_dir,demo_name=demo_name)
    rst=ase.evaluate_action_sequence(actions)
    with open(rst_path, 'w') as t_f:
        json.dump(rst,t_f,indent=4)
    return rst

def evaluate_action_sequence_raw(demo_dir,actions_raw,demo_name,rst_path):
    os.makedirs(os.path.dirname(rst_path),exist_ok=True)
    ase=ActionSequenceEvaluator(demo_dir=demo_dir,demo_name=demo_name)
    action_parsed=ase.parse_response(actions_raw)
    rst=ase.evaluate_action_sequence(action_parsed)
    with open(rst_path, 'w') as t_f:
        json.dump(rst,t_f,indent=4)
    return rst

def evaluate_action_sequence_batch(demo_dir, rst_dir,llm_output_path=None,llm_output_dir=None):
    assert llm_output_path is not None or llm_output_dir is not None
    args_list=[]
    if llm_output_dir is not None:
        for action_path in os.listdir(llm_output_dir):
            abs_action_path=os.path.join(llm_output_dir,action_path)
            demo_name=action_path.replace(".json","")
            actions=json.load(open(abs_action_path,'r'))
            rst_path=os.path.join(rst_dir,demo_name+".json")
            if action_path.endswith(".json"):
                args_list.append((demo_dir,actions,demo_name,rst_path))
    else:
        with open(llm_output_path, 'r') as f:
            responses = json.load(f)
        for response in responses:
            demo_name=response['identifier']
            llm_response=response['llm_output']
            args_list.append((demo_dir,llm_response,demo_name,os.path.join(rst_dir,demo_name+".json")))


    final_rst=[]
    summary_rst={'tot_tasks':0,
                 'all_goal_satisfied_graph':0,
                 'all_goal_satisfied_ig':0,
                 'execution_error':0,
                 'tot_steps':0,
                 'error_steps':0,
                 'tot_goals':0,
                 'satisfied_goals':0,
                 'tot_edge_predicates': 0,
                 'tot_node_predicates': 0,
                 'satisfied_edge_predicates': 0,
                 'satisfied_node_predicates': 0,}
    

    for args in args_list:
        try:
            if llm_output_dir is not None:
                rst=evaluate_action_sequence_parsed(*args)
            else:
                rst=evaluate_action_sequence_raw(*args)

            final_rst.append(
                {
                    "identifier":args[2],
                    "llm_rst":rst
                }
            )
            summary_rst['tot_tasks']+=1
            for k in summary_rst:
                if k in rst:
                    summary_rst[k]+=rst[k]

        except Exception as e:
            print(f"Error in {args[2]}")
            print(e)
            final_rst.append(
                {
                    "identifier":args[2],
                    "llm_rst":None,
                    "error_info":str(e)
                }
            )
            summary_rst['execution_error']+=1
    

    with open(os.path.join(rst_dir,'final_rst.json'), 'w') as f:
        f.write(json.dumps(final_rst,indent=4))

    summary_rst['tot_predicates']=summary_rst['tot_edge_predicates']+summary_rst['tot_node_predicates']
    summary_rst['satisfied_predicates']=summary_rst['satisfied_edge_predicates']+summary_rst['satisfied_node_predicates']
    summary_rst['predicate_succ_rate']=summary_rst['satisfied_predicates']/summary_rst['tot_predicates'] if summary_rst['tot_predicates']>0 else 0
    summary_rst['goal_succ_rate']=summary_rst['satisfied_goals']/summary_rst['tot_goals'] if summary_rst['tot_goals']>0 else 0
    summary_rst['edge_predicate_succ_rate']=summary_rst['satisfied_edge_predicates']/summary_rst['tot_edge_predicates'] if summary_rst['tot_edge_predicates']>0 else 0
    summary_rst['node_predicate_succ_rate']=summary_rst['satisfied_node_predicates']/summary_rst['tot_node_predicates'] if summary_rst['tot_node_predicates']>0 else 0
    summary_rst['step_succ_rate']=(summary_rst['tot_steps']-summary_rst['error_steps'])/summary_rst['tot_steps'] if summary_rst['tot_steps']>0 else 0
    with open(os.path.join(rst_dir,'summary_rst.json'), 'w') as f:
        f.write(json.dumps(summary_rst,indent=4))

    return final_rst

if __name__ == "__main__":
    fire.Fire(evaluate_action_sequence_batch)