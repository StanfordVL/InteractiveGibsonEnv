zero_shot="""
You are a software engineer who will be writing action definitions for a household robot in the PDDL planning language given the problem file and predicates in domain file.

The following is predicates defined in this domain file. Pay attention to the types for each predicate.
(define (domain igibson-actions)
(:requirements :strips :adl :typing :negative-preconditions)
    ;; types in virtualhome domain
    (:types 
        facsimile.n.02 vacuum.n.04 dishtowel.n.01 apparel.n.01 seat.n.03 bottle.n.01 mouse.n.04 window.n.01 scanner.n.02 
        sauce.n.01 spoon.n.01 date.n.08 egg.n.02 cabinet.n.01 yogurt.n.01 parsley.n.02 notebook.n.01 dryer.n.01 saucepan.n.01 
        soap.n.01 package.n.02 headset.n.01 fish.n.02 vehicle.n.01 chestnut.n.03 grape.n.01 wrapping.n.01 makeup.n.01 mug.n.04 
        pasta.n.02 beef.n.02 scrub_brush.n.01 cracker.n.01 flour.n.01 sunglass.n.01 cookie.n.01 bed.n.01 lamp.n.02 food.n.02 
        painting.n.01 carving_knife.n.01 pop.n.02 tea_bag.n.01 sheet.n.03 tomato.n.01 agent.n.01 hat.n.01 dish.n.01 cheese.n.01 
        perfume.n.02 toilet.n.02 broccoli.n.02 book.n.02 towel.n.01 table.n.02 pencil.n.01 rag.n.01 peach.n.03 water.n.06 cup.n.01 
        radish.n.01 marker.n.03 tile.n.01 box.n.01 screwdriver.n.01 raspberry.n.02 banana.n.02 grill.n.02 caldron.n.01 vegetable_oil.n.01 
        necklace.n.01 brush.n.02 washer.n.03 hamburger.n.01 catsup.n.01 sandwich.n.01 plaything.n.01 candy.n.01 cereal.n.03 door.n.01 
        food.n.01 newspaper.n.03 hanger.n.02 carrot.n.03 salad.n.01 toothpaste.n.01 blender.n.01 sofa.n.01 plywood.n.01 olive.n.04 briefcase.n.01 
        christmas_tree.n.05 bowl.n.01 casserole.n.02 apple.n.01 basket.n.01 pot_plant.n.01 backpack.n.01 sushi.n.01 saw.n.02 toothbrush.n.01 
        lemon.n.01 pad.n.01 receptacle.n.01 sink.n.01 countertop.n.01 melon.n.01 bracelet.n.02 modem.n.01 pan.n.01 oatmeal.n.01 calculator.n.02 
        duffel_bag.n.01 sandal.n.01 floor.n.01 snack_food.n.01 stocking.n.01 dishwasher.n.01 pencil_box.n.01 chicken.n.01 jar.n.01 alarm.n.02 
        stove.n.01 plate.n.04 highlighter.n.02 umbrella.n.01 piece_of_cloth.n.01 bin.n.01 ribbon.n.01 chip.n.04 shelf.n.01 bucket.n.01 shampoo.n.01 
        folder.n.02 shoe.n.01 detergent.n.02 milk.n.01 beer.n.01 shirt.n.01 dustpan.n.02 cube.n.05 broom.n.01 candle.n.01 pen.n.01 microwave.n.02 
        knife.n.01 wreath.n.01 car.n.01 soup.n.01 sweater.n.01 tray.n.01 juice.n.01 underwear.n.01 orange.n.01 envelope.n.01 fork.n.01 lettuce.n.03 
        bathtub.n.01 earphone.n.01 pool.n.01 printer.n.03 sack.n.01 highchair.n.01 cleansing_agent.n.01 kettle.n.01 vidalia_onion.n.01 mousetrap.n.01 
        bread.n.01 meat.n.01 mushroom.n.05 cake.n.03 vessel.n.03 bow.n.08 gym_shoe.n.01 hammer.n.02 teapot.n.01 chair.n.01 jewelry.n.01 pumpkin.n.02 sugar.n.01 
        shower.n.01 ashcan.n.01 hand_towel.n.01 pork.n.01 strawberry.n.01 electric_refrigerator.n.01 oven.n.01 ball.n.01 document.n.01 sock.n.01 beverage.n.01 
        hardback.n.01 scraper.n.01 carton.n.02
    )

    ;; Predicates defined on this domain. Note the types for each predicate.
    (:predicates
        (inside ?obj1 ?obj2) ; obj1 is inside obj2
        (nextto ?obj1 ?obj2) ; obj1 is next to obj2
        (ontop ?obj1 ?obj2) ; obj1 is on top of obj2
        (under ?obj1 ?obj2) ; obj1 is under obj2
        (broken ?obj1) ; obj1 is broken
        (burnt ?obj1) ; obj1 is burnt
        (cooked ?obj1) ; obj1 is cooked
        (dusty ?obj1) ; obj1 is dusty
        (frozen ?obj1) ; obj1 is frozen
        (open ?obj1) ; obj1 is open
        (stained ?obj1) ; obj1 is stained
        (sliced ?obj1) ; obj1 is sliced
        (soaked ?obj1) ; obj1 is soaked
        (toggled_on ?obj1) ; obj1 is toggled on
        (onfloor ?obj1 ?floor1) ; obj1 is on the floor floor1
        (touching ?obj1 ?obj2) ; obj1 is touching obj2
        (holding ?obj1) ; obj1 is being held by agent
        (handsfull ?agent) ; agent's hands are both full
        )
    ;; Actions to be predicted
)

Objective: Given the problem file of pddl, which defines objects in the task (:objects), initial conditions (:init) and goal conditions (:goal), write the body of PDDL actions (:precondition and :effect) given specific action names and parameters. 

Each PDDL action definition consists of four main components: action name, parameters, precondition, and effect. Here is the general format to follow:
(:action [action name]
  :parameters ([action parameters])
  :precondition ([action precondition])
  :effect ([action effect]) 
)

The :parameters is the list of variables on which the action operates. It lists variable names and variable types. 

The :precondition is a first-order logic sentence specifying preconditions for an action. The precondition consists of predicates and 3 possible logical operators: or, and, and not. The precondition should be structured in Disjunctive Normal Form (DNF), meaning an OR of ANDs. The not operator should only be used within these conjunctions. For example, (or (and (predicate1 ?x) (predicate2 ?y)) (and (predicate3 ?x)))

The :effect lists the changes which the action imposes on the current state. The precondition consists of predicates and 3 possible logical operators: and, not and when. 1. The effects should generally be several effects connected by AND operators. 2. For each effect, if it is a conditional effect, use WHEN to check the conditions. The semantics of (when [condition] [effect]) are as follows: If [condition] is true before the action, then [effect] occurs afterwards. 3. If it is not a conditional effect, use predicates directly. 4. The NOT operator is used to negate a predicate, signifying that the condition will not hold after the action is executed. And example of effect is (and (when (predicate1 ?x) (not (predicate2 ?y))) (predicate3 ?x))

In any case, the occurrence of a predicate should agree with its declaration in terms of number and types of arguments defined in DOMAIN FILE at the beginning.

Here is an example of the input problem file and unfinished action. after ; is a comment to explain the meaning of each line.
Input:
Problem file:
(define (problem cleaning_floor_0)
    (:domain igibson)

    (:objects
    	floor.n.01_1 - floor.n.01
    	rag.n.01_1 - rag.n.01
    	sink.n.01_1 - sink.n.01
    	agent.n.01_1 - agent.n.01
    )
    
    (:init 
        (dusty floor.n.01_1) 
        (stained floor.n.01_2) 
        (ontop rag.n.01_1 table.n.02_1) 
        (inroom sink.n.01_1 storage_room) 
        (onfloor agent.n.01_1 floor.n.01_2)
    )
    
    (:goal 
        (and 
            (not 
                (dusty ?floor.n.01_1)
            ) 
            (not 
                (stained ?floor.n.01_2)
            ) 
        )
    )
)
Action to be finished:
(:action clean-stained-floor-rag
  :parameters (?rag - rag.n.01 ?floor - floor.n.01 ?agent - agent.n.01)
  :precondition ()
  :effect ()
)
(:action clean-dusty-floor-rag
  :parameters (?rag - rag.n.01 ?floor - floor.n.01 ?agent - agent.n.01)
  :precondition ()
  :effect ()
)
(:action soak-rag
  :parameters (?rag - rag.n.01 ?agent - agent.n.01 ?sink - sink.n.01)
  :precondition ()
  :effect ()
)
Output: 
(:action clean-stained-floor-rag
  :parameters (?rag - rag.n.01 ?floor - floor.n.01 ?agent - agent.n.01)
  :precondition (and (nextto ?floor ?agent) ; agent is next to floor
                            (stained ?obj) ; floor is stained
                            (soaked ?rag) ; rag is soaked
                            (holding ?rag)) ; agent is holding rag
  :effect (not (stained ?floor)) ; after the action, floor is not stained
)
(:action clean-dusty-floor-rag
  :parameters (?rag - rag.n.01 ?floor - floor.n.01 ?agent - agent.n.01)
  :precondition (and (nextto ?floor ?agent) ; agent is next to floor
                            (stained ?obj) ; floor is stained
                            (holding ?rag)) ; agent is holding rag
  :effect (not (dusty ?floor)) ; after the action, floor is not dusty
)
(:action soak-rag
  :parameters (?rag - rag.n.01 ?agent - agent.n.01 ?sink - sink.n.01)
  :precondition  (and (holding ?rag) ; agent is holding rag
                            (nextto ?sink ?agent) ; agent is next to sink
                            (toggled_on ?sink)) ; sink is toggled on
  :effect (soaked ?rag) ; after the action, rag is soaked
)

Above is a good example of given predicates in domain file, problem file, action names and parameters, how to write the action body in PDDL. REMEMBER: You MUST only use predicates and object types exactly as they appear in the domain file at the beginning. Now given the input, please fill in the action body for each provided actions in PDDL format. 

Input:
Problem file:
{problem_file}
Action to be finished:
{action_handler}

Output:
"""


if __name__ == "__main__":
    print(zero_shot.format(problem_file=123,action_handler=456))
    