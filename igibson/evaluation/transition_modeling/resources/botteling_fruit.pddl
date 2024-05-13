(define (problem bottling_fruit_0)
    (:domain igibson)

    (:objects
     	strawberry.n.01_1 - object
    	electric_refrigerator.n.01_1 - object
    	peach.n.03_1 - object
    	countertop.n.01_1 - object
    	jar.n.01_1 jar.n.01_2 - object
        carving_knife.n.01_1 - object
    	cabinet.n.01_1 - object
    	floor.n.01_1 - object
    	agent.n.01_1 - agent.n.01
    )
    
    (:init 
        (inside strawberry.n.01_1 electric_refrigerator.n.01_1) 
        (inside peach.n.03_1 electric_refrigerator.n.01_1) 
        (not 
            (sliced strawberry.n.01_1)
        ) 
        (not 
            (sliced peach.n.03_1)
        ) 
        (ontop jar.n.01_1 countertop.n.01_1) 
        (ontop jar.n.01_2 countertop.n.01_1) 
        (ontop carving_knife.n.01_1 countertop.n.01_1) 
        (inroom countertop.n.01_1 kitchen) 
        (inroom cabinet.n.01_1 kitchen) 
        (inroom electric_refrigerator.n.01_1 kitchen) 
        (inroom floor.n.01_1 kitchen) 
        (onfloor agent.n.01_1 floor.n.01_1)
        (strawberry_n_01 strawberry.n.01_1)
        (electric_refrigerator_n_01 electric_refrigerator.n.01_1)
        (peach_n_03 peach.n.03_1)
        (countertop_n_01 countertop.n.01_1)
        (jar_n_01 jar.n.01_1)
        (jar_n_01 jar.n.01_2)
        (carving_knife_n_01 carving_knife.n.01_1)
        (cabinet_n_01 cabinet.n.01_1)
        (floor_n_01 floor.n.01_1)
    )
    
    (:goal 
        (and 
            (exists 
                (?jar.n.01 - object) 
                (and 
                    (inside ?strawberry.n.01_1 ?jar.n.01) 
                    (not 
                        (inside ?peach.n.03_1 ?jar.n.01)
                    )
                    (jar_n_01 ?jar.n.01)
                )
            ) 
            (exists 
                (?jar.n.01 - object) 
                (and 
                    (inside ?peach.n.03_1 ?jar.n.01) 
                    (not 
                        (inside ?strawberry.n.01_1 ?jar.n.01)
                    )
                    (jar_n_01 ?jar.n.01)
                )
            ) 
            (forall 
                (?jar.n.01 - object) 
                (not 
                    (and 
                    (open ?jar.n.01)
                    (jar_n_01 ?jar.n.01)
                    )
                )
            ) 
            (sliced strawberry.n.01_1) 
            (sliced peach.n.03_1)
        )
    )
)