(define (domain igibson-actions)

    (:requirements :strips :adl :typing :negative-preconditions)

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

    (:predicates 
        (inside ?obj1 ?obj2)
        (nextto ?obj1 ?obj2)
        (ontop ?obj1 ?obj2)
        (under ?obj1 ?obj2)
        (broken ?obj1)
        (burnt ?obj1)
        (cooked ?obj1)
        (dusty ?obj1)
        (frozen ?obj1)
        (open ?obj1)
        (perished ?obj1)
        (screwed ?obj1)
        (stained ?obj1)
        (sliced ?obj1)
        (soaked ?obj1)
        (timeset ?obj1)
        (toggled_on ?obj1)
        (inroom ?obj1 ?room1)
        (onfloor ?obj1 ?floor1)
        (touching ?obj1 ?obj2)
        ; New Handwritten predicates (njk and wbm3)
        (holding ?obj1)
        (handsfull ?agent)
    )

    (:action navigate_to
        :parameters (?objto - object ?agent - agent.n.01)
        :precondition (not (nextto ?objto ?agent))
        :effect (and (nextto ?objto ?agent) 
                        (when 
                            (exists 
                                (?objfrom - object) 
                                (nextto ?objfrom ?agent)
                            )
                            (not (nextto ?objfrom ?agent))
                        ) 
                )
    )

    (:action grasp
        :parameters (?obj - object ?agent - agent.n.01)
        :precondition (and (not (holding ?obj))
                            (not (handsfull ?agent)) 
                            (nextto ?obj ?agent))
        :effect (and (holding ?obj) 
                        (handsfull ?agent))

    )

    

    (:action place_ontop ; place object 1 onto object 2
        :parameters (?obj2 - object ?agent - agent.n.01 ?obj1 - object)
        :precondition (and (holding ?obj1) 
                            (nextto ?obj2 ?agent))
        :effect (and (ontop ?obj1 ?obj2) 
                        (not (holding ?obj1)) 
                        (not (handsfull ?agent)))
    )

    (:action place_inside ; place object 1 inside object 2
        :parameters (?obj2 - object ?agent - agent.n.01 ?obj1 - object)
        :precondition (and (holding ?obj1) 
                            (nextto ?obj2 ?agent) 
                            (open ?obj2))
        :effect (and (inside ?obj1 ?obj2) 
                        (not (holding ?obj1)) 
                        (not (handsfull ?agent)))
    )

    (:action open
        :parameters (?obj - object ?agent - agent.n.01)
        :precondition (and (nextto ?obj ?agent) 
                            (not (open ?obj))
                            (not (handsfull ?agent)))
        :effect (open ?obj)
    )

    (:action close
        :parameters (?obj - object ?agent - agent.n.01)
        :precondition (and (nextto ?obj ?agent) 
                            (open ?obj)
                            (not (handsfull ?agent)))
        :effect (not (open ?obj))
    )

    (:action grasp-inside ; will need obj open precondition later
        :parameters (?obj1 - object ?agent - agent.n.01 ?obj2 - object)
        :precondition (and (not (holding ?obj1))
                            (not (handsfull ?agent)) 
                            (nextto ?obj2 ?agent)
                            (inside ?obj1 ?obj2))
        :effect (and (holding ?obj1) 
                    (handsfull ?agent)
                    (not (inside ?obj1 ?obj2)))
    )

    (:action slice
        :parameters (?obj - object ?agent - agent.n.01 ?knife - knife.n.01)
        :precondition (and (holding ?knife) 
                            (nextto ?obj ?agent))
        :effect (sliced ?obj)
    )

    (:action slice-carvingknife
        :parameters (?obj - object ?knife - carving_knife.n.01 ?board - countertop.n.01 ?agent - agent.n.01)
        :precondition (and (nextto ?obj ?agent)
                           (holding ?knife)
                           (ontop ?obj ?board)
                           (not (sliced ?obj)))
        :effect (sliced ?obj)
    )


    (:action place_onfloor
        :parameters (?floor - floor.n.01 ?agent - agent.n.01 ?obj1 - object)
        :precondition (and (holding ?obj1) 
                            (nextto ?floor ?agent))
        :effect (and (onfloor ?obj1 ?floor) 
                        (not (holding ?obj1)) 
                        (not (handsfull ?agent)))
    )

    (:action place_nextto
        :parameters (?obj2 - object ?agent - agent.n.01 ?obj1 - object)
        :precondition (and (holding ?obj1) 
                            (nextto ?obj2 ?agent))
        :effect (and (nextto ?obj1 ?obj2) 
                        (not (holding ?obj1)) 
                        (not (handsfull ?agent)))
    )

    (:action place_touching
        :parameters (?obj2 - object ?agent - agent.n.01 ?obj1 - object)
        :precondition (and (holding ?obj1) 
                            (nextto ?obj2 ?agent))
        :effect (and (touching ?obj1 ?obj2) 
                        (not (holding ?obj1)) 
                        (not (handsfull ?agent)))
    )

    (:action clean-stained-brush
        :parameters (?scrub_brush - scrub_brush.n.01 ?obj - object ?agent - agent.n.01)
        :precondition (and (nextto ?obj ?agent) 
                            (stained ?obj)
                            (soaked ?scrub_brush)
                            (holding ?scrub_brush))
        :effect (not (stained ?obj))
    )

    (:action clean-stained-cloth
        :parameters (?rag - piece_of_cloth.n.01 ?obj - object ?agent - agent.n.01)
        :precondition (and (nextto ?obj ?agent) 
                            (stained ?obj)
                            (soaked ?rag)
                            (holding ?rag))
        :effect (not (stained ?obj))
    )

    (:action clean-stained-thandowel
        :parameters (?hand_towel - hand_towel.n.01 ?obj - object ?agent - agent.n.01)
        :precondition (and (nextto ?obj ?agent) 
                            (stained ?obj)
                            (soaked ?hand_towel)
                            (holding ?hand_towel))
        :effect (not (stained ?obj))
    )

    (:action clean-stained-towel
        :parameters (?hand_towel - towel.n.01 ?obj - object ?agent - agent.n.01)
        :precondition (and (nextto ?obj ?agent) 
                            (stained ?obj)
                            (soaked ?hand_towel)
                            (holding ?hand_towel))
        :effect (not (stained ?obj))
    )

    (:action clean-stained-dishtowel
        :parameters (?hand_towel - dishtowel.n.01 ?obj - object ?agent - agent.n.01)
        :precondition (and (nextto ?obj ?agent) 
                            (stained ?obj)
                            (soaked ?hand_towel)
                            (holding ?hand_towel))
        :effect (not (stained ?obj))
    )

    (:action clean-stained-dishwasher ; this should be a plan where objects are put in and then dishwasher is closed and toggled-on
        :parameters (?dishwasher - dishwasher.n.01 ?obj - object ?agent - agent.n.01)
        :precondition (and (holding ?obj)
                            (open ?dishwasher)
                            (nextto ?dishwasher ?agent))
        :effect (not (stained ?obj))
    )

    (:action clean-rag
        :parameters (?rag - rag.n.01 ?obj - object ?agent - agent.n.01)
        :precondition (and (nextto ?obj ?agent) 
                            (stained ?obj)
                            (soaked ?rag)
                            (holding ?rag))
        :effect (not (stained ?obj))
    )

    (:action soak
        :parameters (?obj1 - object ?agent - agent.n.01 ?sink - sink.n.01)
        :precondition (and (holding ?obj1) 
                            (nextto ?sink ?agent)
                            (toggled_on ?sink))
        :effect (soaked ?obj1)
    )

    (:action soak-teapot
        :parameters (?obj1 - object ?agent - agent.n.01 ?teapot - teapot.n.01)
        :precondition (and (holding ?obj1) 
                            (nextto ?teapot ?agent))
        :effect (soaked ?obj1)
    )

    (:action place_under ; place object 1 under object 2
        :parameters (?obj2 - object ?agent - agent.n.01 ?obj1 - object)
        :precondition (and (holding ?obj1) 
                            (nextto ?obj2 ?agent))
        :effect (and (under ?obj1 ?obj2) 
                        (not (holding ?obj1)) 
                        (not (handsfull ?agent)))
    )

    (:action toggle-on
        :parameters (?obj - object ?agent - agent.n.01)
        :precondition (and (nextto ?obj ?agent)
                            (not (handsfull ?agent)))
        :effect (toggled_on ?obj)
    )

    (:action clean-dusty
        :parameters (?rag - rag.n.01 ?obj - object ?agent - agent.n.01)
        :precondition (and (nextto ?obj ?agent) 
                            (dusty ?obj)
                            (holding ?rag))
        :effect (not (dusty ?obj))
    )

    (:action clean-dusty-towel
        :parameters (?towel - towel.n.01 ?obj - object ?agent - agent.n.01)
        :precondition (and (nextto ?obj ?agent) 
                            (dusty ?obj)
                            (holding ?towel))
        :effect (not (dusty ?obj))
    )


    (:action clean-inside-dusty
        :parameters (?rag - rag.n.01 ?obj1 - object ?agent - agent.n.01 ?obj2 - object)
        :precondition (and (inside ?obj1 ?obj2)
                            (nextto ?obj2 ?agent) 
                            (dusty ?obj1)
                            (holding ?rag))
        :effect (not (dusty ?obj1))
    )

    (:action clean-dusty-cloth
        :parameters (?rag - piece_of_cloth.n.01 ?obj - object ?agent - agent.n.01)
        :precondition (and (nextto ?obj ?agent) 
                            (dusty ?obj)
                            (holding ?rag))
        :effect (not (dusty ?obj))
    )

    (:action clean-dusty-brush
        :parameters (?scrub_brush - scrub_brush.n.01 ?obj - object ?agent - agent.n.01)
        :precondition (and (nextto ?obj ?agent) 
                            (dusty ?obj)
                            (holding ?scrub_brush))
        :effect (not (dusty ?obj))
    )

    (:action clean-dusty-vacuum
        :parameters (?vacuum - vacuum.n.04 ?obj - object ?agent - agent.n.01)
        :precondition (and (nextto ?obj ?agent) 
                            (dusty ?obj)
                            (holding ?vacuum))
        :effect (not (dusty ?obj))
    )

    (:action freeze
        :parameters (?obj - object ?fridge - electric_refrigerator.n.01)
        :precondition (and (inside ?obj ?fridge)
                           (not (frozen ?obj)))
        :effect (frozen ?obj)
    )

    (:action cook
        :parameters (?obj - object ?pan - pan.n.01)
        :precondition (and (ontop ?obj ?pan)
                           (not (cooked ?obj)))
        :effect (cooked ?obj)
    )

)