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
        (same_obj ?obj1 - object ?obj2 - object)
    )

    (:action navigate_to
        :parameters (?objto - object ?agent - agent)
        :precondition (not (in_reach_of_agent ?objto))
        :effect (and (in_reach_of_agent ?objto) 
                    (forall 
                        (?objfrom - object) 
                        (when 
                            (and 
                                (in_reach_of_agent ?objfrom) 
                                (not (same_obj ?objfrom ?objto))
                            )
                            (not (in_reach_of_agent ?objfrom))
                        )
                    )
                )
    )

    (:action grasp
    :parameters (?obj - object ?agent - agent)
    :precondition (and (not (holding ?obj))
                        (not (handsfull ?agent)) 
                        (in_reach_of_agent ?obj)
                        (not (exists (?obj2 - object) (and (inside ?obj ?obj2) (not (open ?obj2)))))
                    )
    :effect (and (holding ?obj) 
                    (handsfull ?agent)
                    ;; Conditional effects for all predicates involving ?obj and ?other_obj
                    (forall (?other_obj - object)
                        (and (not (inside ?obj ?other_obj))
                             (not (ontop ?obj ?other_obj))
                             (not (under ?obj ?other_obj))
                             (not (under ?other_obj ?obj))
                             (not (nextto ?obj ?other_obj))
                             (not (nextto ?other_obj ?obj))
                             (not (onfloor ?obj ?other_obj))
                             ;; Add other predicates as needed
                        )
                    )
                )
    )

    (:action release
        :parameters (?obj - object ?agent - agent)
        :precondition (and (holding ?obj))
        :effect (and (not (holding ?obj))
                        (not (handsfull ?agent)))
    )
    

    

    (:action place_ontop 
        :parameters (?obj_in_hand - object ?obj - object ?agent - agent)
        :precondition (and (holding ?obj_in_hand) 
                            (in_reach_of_agent ?obj))
        :effect (and (ontop ?obj_in_hand ?obj) 
                        (not (holding ?obj_in_hand)) 
                        (not (handsfull ?agent)))
    )

    (:action place_inside 
        :parameters (?obj_in_hand - object ?obj - object ?agent - agent)
        :precondition (and (holding ?obj_in_hand) 
                            (in_reach_of_agent ?obj) 
                            (open ?obj))
        :effect (and (inside ?obj_in_hand ?obj) 
                        (not (holding ?obj_in_hand)) 
                        (not (handsfull ?agent)))
    )

    (:action open
        :parameters (?obj - object ?agent - agent)
        :precondition (and (in_reach_of_agent ?obj) 
                            (not (open ?obj))
                            (not (handsfull ?agent)))
        :effect (open ?obj)
    )

    (:action close
        :parameters (?obj - object ?agent - agent)
        :precondition (and (in_reach_of_agent ?obj) 
                            (open ?obj)
                            (not (handsfull ?agent)))
        :effect (not (open ?obj))
    )

    (:action slice
        :parameters (?obj - object ?knife - knife_n_01 ?agent - agent)
        :precondition (and (holding ?knife) 
                            (in_reach_of_agent ?obj))
        :effect (sliced ?obj)
    )

    (:action slice_carvingknife
        :parameters (?obj - object ?knife - carving_knife_n_01 ?board - countertop_n_01 ?agent - agent)
        :precondition (and (in_reach_of_agent ?obj)
                           (holding ?knife)
                           (ontop ?obj ?board)
                           (not (sliced ?obj)))
        :effect (sliced ?obj)
    )


    (:action place_onfloor
        :parameters (?obj_in_hand - object ?floor - floor_n_01 ?agent - agent)
        :precondition (and (holding ?obj_in_hand) 
                            (in_reach_of_agent ?floor))
        :effect (and (onfloor ?obj_in_hand ?floor) 
                        (not (holding ?obj_in_hand)) 
                        (not (handsfull ?agent)))
    )

    (:action place_nextto
        :parameters (?obj_in_hand - object ?obj - object ?agent - agent)
        :precondition (and (holding ?obj_in_hand) 
                            (in_reach_of_agent ?obj))
        :effect (and (nextto ?obj_in_hand ?obj) 
                        (nextto ?obj ?obj_in_hand)
                        (not (holding ?obj_in_hand)) 
                        (not (handsfull ?agent)))
    )

    (:action place_nextto_ontop
        :parameters (?obj_in_hand - object ?obj1 - object ?obj2 - object ?agent - agent)
        :precondition (and (holding ?obj_in_hand) 
                            (in_reach_of_agent ?obj1))
        :effect (and (nextto ?obj_in_hand ?obj1) 
                        (nextto ?obj1 ?obj_in_hand)
                        (ontop ?obj_in_hand ?obj2)
                        (not (holding ?obj_in_hand)) 
                        (not (handsfull ?agent)))
    )

    (:action clean_stained_brush
        :parameters (?scrub_brush - scrub_brush_n_01 ?obj - object ?agent - agent)
        :precondition (and (in_reach_of_agent ?obj) 
                            (stained ?obj)
                            (soaked ?scrub_brush)
                            (holding ?scrub_brush))
        :effect (not (stained ?obj))
    )

    (:action clean_stained_cloth
        :parameters (?rag - piece_of_cloth_n_01 ?obj - object ?agent - agent)
        :precondition (and (in_reach_of_agent ?obj) 
                            (stained ?obj)
                            (soaked ?rag)
                            (holding ?rag))
        :effect (not (stained ?obj))
    )

    (:action clean_stained_handowel
        :parameters (?hand_towel - hand_towel_n_01 ?obj - object ?agent - agent)
        :precondition (and (in_reach_of_agent ?obj) 
                            (stained ?obj)
                            (soaked ?hand_towel)
                            (holding ?hand_towel))
        :effect (not (stained ?obj))
    )

    (:action clean_stained_towel
        :parameters (?hand_towel - towel_n_01 ?obj - object ?agent - agent)
        :precondition (and (in_reach_of_agent ?obj) 
                            (stained ?obj)
                            (soaked ?hand_towel)
                            (holding ?hand_towel))
        :effect (not (stained ?obj))
    )

    (:action clean_stained_dishtowel
        :parameters (?hand_towel - dishtowel_n_01 ?obj - object ?agent - agent)
        :precondition (and (in_reach_of_agent ?obj) 
                            (stained ?obj)
                            (soaked ?hand_towel)
                            (holding ?hand_towel))
        :effect (not (stained ?obj))
    )

    (:action clean_stained_dishwasher 
        :parameters (?dishwasher - dishwasher_n_01 ?obj - object ?agent - agent)
        :precondition (and (holding ?obj)
                            (in_reach_of_agent ?dishwasher))
        :effect (not (stained ?obj))
    )

    (:action clean_stained_rag
        :parameters (?rag - rag_n_01 ?obj - object ?agent - agent)
        :precondition (and (in_reach_of_agent ?obj) 
                            (stained ?obj)
                            (soaked ?rag)
                            (holding ?rag))
        :effect (not (stained ?obj))
    )

    (:action soak
        :parameters (?obj1 - object ?sink - sink_n_01 ?agent - agent)
        :precondition (and (holding ?obj1) 
                            (in_reach_of_agent ?sink)
                            (toggled_on ?sink))
        :effect (soaked ?obj1)
    )

    (:action soak_teapot
        :parameters (?obj1 - object ?agent - agent ?teapot - teapot_n_01)
        :precondition (and (holding ?obj1) 
                            (in_reach_of_agent ?teapot))
        :effect (soaked ?obj1)
    )

    (:action place_under ; place object 1 under object 2
        :parameters (?obj_in_hand - object ?obj - object ?agent - agent)
        :precondition (and (holding ?obj_in_hand) 
                            (in_reach_of_agent ?obj))
        :effect (and (under ?obj_in_hand ?obj) 
                        (not (holding ?obj_in_hand)) 
                        (not (handsfull ?agent)))
    )

    (:action toggle_on
        :parameters (?obj - object ?agent - agent)
        :precondition (and (in_reach_of_agent ?obj)
                            (not (handsfull ?agent)))
        :effect (toggled_on ?obj)
    )

    (:action clean_dusty_rag
        :parameters (?rag - rag_n_01 ?obj - object ?agent - agent)
        :precondition (and (in_reach_of_agent ?obj) 
                            (dusty ?obj)
                            (holding ?rag))
        :effect (not (dusty ?obj))
    )

    (:action clean_dusty_towel
        :parameters (?towel - towel_n_01 ?obj - object ?agent - agent)
        :precondition (and (in_reach_of_agent ?obj) 
                            (dusty ?obj)
                            (holding ?towel))
        :effect (not (dusty ?obj))
    )

    (:action clean_dusty_cloth
        :parameters (?rag - piece_of_cloth_n_01 ?obj - object ?agent - agent)
        :precondition (and (in_reach_of_agent ?obj) 
                            (dusty ?obj)
                            (holding ?rag))
        :effect (not (dusty ?obj))
    )

    (:action clean_dusty_brush
        :parameters (?scrub_brush - scrub_brush_n_01 ?obj - object ?agent - agent)
        :precondition (and (in_reach_of_agent ?obj) 
                            (dusty ?obj)
                            (holding ?scrub_brush))
        :effect (not (dusty ?obj))
    )

    (:action clean_dusty_vacuum
        :parameters (?vacuum - vacuum_n_04 ?obj - object ?agent - agent)
        :precondition (and (in_reach_of_agent ?obj) 
                            (dusty ?obj)
                            (holding ?vacuum))
        :effect (not (dusty ?obj))
    )

    (:action freeze
        :parameters (?obj - object ?fridge - electric_refrigerator_n_01)
        :precondition (and (inside ?obj ?fridge)
                           (not (frozen ?obj)))
        :effect (frozen ?obj)
    )

    (:action cook
        :parameters (?obj - object ?pan - pan_n_01)
        :precondition (and (ontop ?obj ?pan)
                           (not (cooked ?obj)))
        :effect (cooked ?obj)
    )

)