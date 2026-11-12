; The banned bot's core. Walking into it picks it up.
(event `self.ReceiveActorBeginOverlap`
  (params (OtherActor))
  (if (!= OtherActor (`GameplayStatics.GetPlayerPawn` 0))
    (return))
  (bind game (cast `/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C`
    (`GameplayStatics.GetActorOfClass` "/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C")))
  (`/Game/Splice/Blueprints/BP_SpliceGame.SetObjective` game "Splice the core at the rover or a stash crate")
  (`/Game/Splice/Blueprints/BP_SpliceGame.PickUp` game "Banned core")
  (`Actor.K2_DestroyActor` self))
