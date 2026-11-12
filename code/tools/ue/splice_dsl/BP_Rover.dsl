; Tells the game when the player is close enough to open the edit bay.
(event `self.ReceiveTick`
  (params (DeltaSeconds))
  (bind pawn (`GameplayStatics.GetPlayerPawn` 0))
  (if (not (`KismetSystemLibrary.IsValid` pawn))
    (return))
  (bind near (< (`Actor.GetDistanceTo` self pawn) 450.0))
  (if (== near (`self.WasNear`))
    (return))
  (set `self.WasNear` near)
  (bind game (cast `/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C`
    (`GameplayStatics.GetActorOfClass` "/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C")))
  (`/Game/Splice/Blueprints/BP_SpliceGame.SetNearRover` game near))
