; An invisible box. The first time the player walks through it, the time of day and
; the objective change.
(event `self.ReceiveActorBeginOverlap`
  (params (OtherActor))
  (if (!= OtherActor (`GameplayStatics.GetPlayerPawn` 0))
    (return))
  (if (`self.Used`)
    (return))
  (set `self.Used` true)
  (bind game (cast `/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C`
    (`GameplayStatics.GetActorOfClass` "/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C")))
  (`/Game/Splice/Blueprints/BP_SpliceGame.SetPhase` game (`self.PhaseIndex`))
  (`/Game/Splice/Blueprints/BP_SpliceGame.SetObjective` game (`self.Objective`)))
