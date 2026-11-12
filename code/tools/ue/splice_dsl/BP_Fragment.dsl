; Walking into a fragment adds its ItemName to the inventory and removes it.
(event `self.ReceiveActorBeginOverlap`
  (params (OtherActor))
  (if (!= OtherActor (`GameplayStatics.GetPlayerPawn` 0))
    (return))
  (bind game (cast `/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C`
    (`GameplayStatics.GetActorOfClass` "/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C")))
  (`/Game/Splice/Blueprints/BP_SpliceGame.PickUp` game (`self.ItemName`))
  (`Actor.K2_DestroyActor` self))
