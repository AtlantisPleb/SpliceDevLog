; Walking onto the exit pad shows the SCENE RESTORED screen.
(event `self.ReceiveActorBeginOverlap`
  (params (OtherActor))
  (if (!= OtherActor (`GameplayStatics.GetPlayerPawn` 0))
    (return))
  (bind game (cast `/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C`
    (`GameplayStatics.GetActorOfClass` "/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C")))
  (`/Game/Splice/Blueprints/BP_SpliceGame.ShowEnd` game))
