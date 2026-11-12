; Walking into a fragment picks it up.
; A normal part joins the inventory and is removed.
; A banned piece raises Heat and hides, so it can come back if the player is sent to the checkpoint.
(event `self.ReceiveActorBeginOverlap`
  (params (OtherActor))
  (if (!= OtherActor (`GameplayStatics.GetPlayerPawn` 0))
    (return))
  (bind game (cast `/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C`
    (`GameplayStatics.GetActorOfClass` "/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C")))
  (if (`self.bIsBanned`)
    (if (`self.Taken`)
      (return))
    (set `self.Taken` true)
    (`self.SetActorHiddenInGame` true)
    (`self.SetActorEnableCollision` false)
    (`/Game/Splice/Blueprints/BP_SpliceGame.PickUpBanned` game)
    (return))
  (`/Game/Splice/Blueprints/BP_SpliceGame.PickUp` game (`self.ItemName`))
  (`Actor.K2_DestroyActor` self))

; The game calls this when the player reaches the checkpoint: a carried piece is now safe.
(event `OnCheckpoint`
  (if (`self.Taken`)
    (set `self.Banked` true)))

; The game calls this when the player is sent back: an unsaved piece reappears.
(event `OnRespawn`
  (if (and (`self.bIsBanned`) (`self.Taken`) (not (`self.Banked`)))
    (set `self.Taken` false)
    (`self.SetActorHiddenInGame` false)
    (`self.SetActorEnableCollision` true)))
