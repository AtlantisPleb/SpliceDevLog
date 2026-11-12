; A stash crate: the edit bay opens here too, and Heat cools near it.
(event `self.ReceiveTick`
  (params (DeltaSeconds))
  (bind pawn (`GameplayStatics.GetPlayerPawn` 0))
  (bind game (cast `/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C`
    (`GameplayStatics.GetActorOfClass` "/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C") :!pure true))
  (if (not (and (`KismetSystemLibrary.IsValid` pawn) (`KismetSystemLibrary.IsValid` game)))
    (return))
  (bind near (< (`Actor.GetDistanceTo` self pawn)
                (`/Game/Splice/Data/BP_Tuning.CrateRange` (`/Game/Splice/Blueprints/BP_SpliceGame.Tuning` game))))
  (if (== near (`self.WasNear`))
    (return))
  (set `self.WasNear` near)
  (`/Game/Splice/Blueprints/BP_SpliceGame.SetNearCrate` game near))
