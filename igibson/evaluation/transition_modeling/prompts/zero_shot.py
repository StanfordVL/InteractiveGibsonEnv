zero_shot="""
You are a software engineer who will be writing action definitions for a household robot in the PDDL planning language given the problem file and predicates in domain file_

The following is predicates defined in this domain file_ Pay attention to the types for each predicate_
(define (domain igibson)

    (:requirements :strips :adl :typing :negative-preconditions)

    (:types 
        vacuum_n_04 facsimile_n_02 dishtowel_n_01 apparel_n_01 seat_n_03 bottle_n_01 mouse_n_04 window_n_01 scanner_n_02 
        sauce_n_01 spoon_n_01 date_n_08 egg_n_02 cabinet_n_01 yogurt_n_01 parsley_n_02 notebook_n_01 dryer_n_01 saucepan_n_01 
        soap_n_01 package_n_02 headset_n_01 fish_n_02 vehicle_n_01 chestnut_n_03 grape_n_01 wrapping_n_01 makeup_n_01 mug_n_04 
        pasta_n_02 beef_n_02 scrub_brush_n_01 cracker_n_01 flour_n_01 sunglass_n_01 cookie_n_01 bed_n_01 lamp_n_02 food_n_02 
        painting_n_01 carving_knife_n_01 pop_n_02 tea_bag_n_01 sheet_n_03 tomato_n_01 agent_n_01 hat_n_01 dish_n_01 cheese_n_01 
        perfume_n_02 toilet_n_02 broccoli_n_02 book_n_02 towel_n_01 table_n_02 pencil_n_01 rag_n_01 peach_n_03 water_n_06 cup_n_01 
        radish_n_01 marker_n_03 tile_n_01 box_n_01 screwdriver_n_01 raspberry_n_02 banana_n_02 grill_n_02 caldron_n_01 vegetable_oil_n_01 
        necklace_n_01 brush_n_02 washer_n_03 hamburger_n_01 catsup_n_01 sandwich_n_01 plaything_n_01 candy_n_01 cereal_n_03 door_n_01 
        food_n_01 newspaper_n_03 hanger_n_02 carrot_n_03 salad_n_01 toothpaste_n_01 blender_n_01 sofa_n_01 plywood_n_01 olive_n_04 briefcase_n_01 
        christmas_tree_n_05 bowl_n_01 casserole_n_02 apple_n_01 basket_n_01 pot_plant_n_01 backpack_n_01 sushi_n_01 saw_n_02 toothbrush_n_01 
        lemon_n_01 pad_n_01 receptacle_n_01 sink_n_01 countertop_n_01 melon_n_01 bracelet_n_02 modem_n_01 pan_n_01 oatmeal_n_01 calculator_n_02 
        duffel_bag_n_01 sandal_n_01 floor_n_01 snack_food_n_01 stocking_n_01 dishwasher_n_01 pencil_box_n_01 chicken_n_01 jar_n_01 alarm_n_02 
        stove_n_01 plate_n_04 highlighter_n_02 umbrella_n_01 piece_of_cloth_n_01 bin_n_01 ribbon_n_01 chip_n_04 shelf_n_01 bucket_n_01 shampoo_n_01 
        folder_n_02 shoe_n_01 detergent_n_02 milk_n_01 beer_n_01 shirt_n_01 dustpan_n_02 cube_n_05 broom_n_01 candle_n_01 pen_n_01 microwave_n_02 
        knife_n_01 wreath_n_01 car_n_01 soup_n_01 sweater_n_01 tray_n_01 juice_n_01 underwear_n_01 orange_n_01 envelope_n_01 fork_n_01 lettuce_n_03 
        bathtub_n_01 earphone_n_01 pool_n_01 printer_n_03 sack_n_01 highchair_n_01 cleansing_agent_n_01 kettle_n_01 vidalia_onion_n_01 mousetrap_n_01 
        bread_n_01 meat_n_01 mushroom_n_05 cake_n_03 vessel_n_03 bow_n_08 gym_shoe_n_01 hammer_n_02 teapot_n_01 chair_n_01 jewelry_n_01 pumpkin_n_02 sugar_n_01 
        shower_n_01 ashcan_n_01 hand_towel_n_01 pork_n_01 strawberry_n_01 electric_refrigerator_n_01 oven_n_01 ball_n_01 document_n_01 sock_n_01 beverage_n_01 
        hardback_n_01 scraper_n_01 carton_n_02
        agent
    )

    (:predicates 
        (inside ?obj1 - object ?obj2 - object)
        (nextto ?obj1 - object ?obj2 - object)
        (ontop ?obj1 - object ?obj2 - object)
        (under ?obj1 - object ?obj2 - object)
        (cooked ?obj1 - object)
        (dusty ?obj1 - object)
        (frozen ?obj1 - object)
        (open ?obj1 - object)
        (stained ?obj1 - object)
        (sliced ?obj1 - object)
        (soaked ?obj1 - object)
        (toggled_on ?obj1 - object)
        (onfloor ?obj1 - object ?floor1 - object)
        (holding ?obj1 - object)
        (handsfull ?agent1 - agent)
        (in_reach_of_agent ?obj1 - object)
    )
    ;; Actions to be predicted
)

Objective: Given the problem file of pddl, which defines objects in the task (:objects), initial conditions (:init) and goal conditions (:goal), write the body of PDDL actions (:precondition and :effect) given specific action names and parameters_ 

Each PDDL action definition consists of four main components: action name, parameters, precondition, and effect_ Here is the general format to follow:
(:action [action name]
  :parameters ([action parameters])
  :precondition ([action precondition])
  :effect ([action effect]) 
)

The :parameters is the list of variables on which the action operates_ It lists variable names and variable types_ 

The :precondition is a first-order logic sentence specifying preconditions for an action_ The precondition consists of predicates and 3 possible logical operators: or, and, and not_ The precondition should be structured in Disjunctive Normal Form (DNF), meaning an OR of ANDs_ The not operator should only be used within these conjunctions_ For example, (or (and (predicate1 ?x) (predicate2 ?y)) (and (predicate3 ?x)))

The :effect lists the changes which the action imposes on the current state_ The precondition consists of predicates and 3 possible logical operators: and, not and when_ 1_ The effects should generally be several effects connected by AND operators_ 2_ For each effect, if it is a conditional effect, use WHEN to check the conditions_ The semantics of (when [condition] [effect]) are as follows: If [condition] is true before the action, then [effect] occurs afterwards_ 3_ If it is not a conditional effect, use predicates directly_ 4_ The NOT operator is used to negate a predicate, signifying that the condition will not hold after the action is executed_ And example of effect is (and (when (predicate1 ?x) (not (predicate2 ?y))) (predicate3 ?x))

In any case, the occurrence of a predicate should agree with its declaration in terms of number and types of arguments defined in DOMAIN FILE at the beginning_

Here is an example of the input problem file and unfinished action_ after ; is a comment to explain the meaning of each line_
Input:
Problem file:
(define (problem cleaning_floor_0)
    (:domain igibson)

    (:objects
    	floor_n_01_1 - floor_n_01
    	rag_n_01_1 - rag_n_01
    	sink_n_01_1 - sink_n_01
    	agent_n_01_1 - agent_n_01
    )
    
    (:init 
        (dusty floor_n_01_1) 
        (stained floor_n_01_2) 
        (ontop rag_n_01_1 table_n_02_1) 
        (inroom sink_n_01_1 storage_room) 
        (onfloor agent_n_01_1 floor_n_01_2)
    )
    
    (:goal 
        (and 
        (not (dusty floor_n_01_1)) 
        (not (stained floor_n_01_2))
        )
    )
)
Action to be finished:
(:action navigate_to
        :parameters (?objto - object ?agent - agent)
        :precondition ()
        :effect ()
    )
(:action clean-stained-floor-rag
  :parameters (?rag - rag_n_01 ?floor - floor_n_01 ?agent - agent_n_01)
  :precondition ()
  :effect ()
)
(:action clean-dusty-floor-rag
  :parameters (?rag - rag_n_01 ?floor - floor_n_01 ?agent - agent_n_01)
  :precondition ()
  :effect ()
)
(:action soak-rag
  :parameters (?rag - rag_n_01 ?sink - sink_n_01 ?agent - agent_n_01)
  :precondition ()
  :effect ()
)
Output:
(:action navigate_to
        :parameters (?objto - object ?agent - agent)
        :precondition (not (in_reach_of_agent ?objto))
        :effect (and (in_reach_of_agent ?objto) 
                    (forall 
                        (?objfrom - object) 
                        (when 
                            (and 
                                (in_reach_of_agent ?objfrom) 
                                (not (= ?objfrom ?objto))
                            )
                            (not (in_reach_of_agent ?objfrom))
                        )
                    )
                )
)
(:action clean-stained-floor-rag
  :parameters (?rag - rag_n_01 ?floor - floor_n_01 ?agent - agent_n_01)
  :precondition (and (in_reach_of_agent ?floor)
                      (stained ?obj)
                      (soaked ?rag)
                      (holding ?rag))
  :effect (not (stained ?floor)) 
)
(:action clean-dusty-floor-rag
  :parameters (?rag - rag_n_01 ?floor - floor_n_01 ?agent - agent_n_01)
  :precondition (and (in_reach_of_agent ?floor)
                      (stained ?obj) 
                      (holding ?rag)) 
  :effect (not (dusty ?floor))
)
(:action soak-rag
  :parameters (?rag - rag_n_01 ?sink - sink_n_01 ?agent - agent_n_01)
  :precondition  (and (holding ?rag)
                      (in_reach_of_agent ?sink)
                      (toggled_on ?sink))
  :effect (soaked ?rag)
)

Above is a good example of given predicates in domain file, problem file, action names and parameters, how to write the action body in PDDL_ REMEMBER: You MUST only use predicates and object types exactly as they appear in the domain file at the beginning_ Now given the input, please fill in the action body for each provided actions in PDDL format_ 

Input:
Problem file:
{problem_file}
Action to be finished:
{action_handler}

Output:
"""


if __name__ == "__main__":
    print(zero_shot.format(problem_file=123,action_handler=456))
    