; A raider. Wanders near its home spot. Notices the player up close (from further away
; at high Heat), chases, and hits for one heart on contact. Gives up when the player is
; far away or up on the catwalk. All numbers come from DA_Tuning.
(event `self.ReceiveBeginPlay`
  (set `self.Home` (`Actor.K2_GetActorLocation` self))
  (set `self.Target` (`Actor.K2_GetActorLocation` self))
  (bind game (cast `/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C`
    (`GameplayStatics.GetActorOfClass` "/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C")))
  (set `self.Game` game))

(event `self.ReceiveTick`
  (params (DeltaSeconds))
  (bind pawn (`GameplayStatics.GetPlayerPawn` 0))
  (bind game (`self.Game`))
  (if (not (and (`KismetSystemLibrary.IsValid` pawn) (`KismetSystemLibrary.IsValid` game)))
    (return))
  (bind tun (`/Game/Splice/Blueprints/BP_SpliceGame.Tuning` game))
  (bind dist (`Actor.GetHorizontalDistanceTo` self pawn))
  (bind climb (`Actor.GetVerticalDistanceTo` self pawn))
  (bind heat01 (/ (`/Game/Splice/Blueprints/BP_SpliceGame.Heat` game)
                  (`KismetMathLibrary.FMax` (`/Game/Splice/Data/BP_Tuning.MaxHeat` tun) 1.0)))
  (bind notice (* (`/Game/Splice/Data/BP_Tuning.NoticeRange` tun) (+ 1.0 heat01)))
  (bind onFloor (< climb (`/Game/Splice/Data/BP_Tuning.CatwalkSafeHeight` tun)))
  (bind busy (`/Game/Splice/Blueprints/BP_SpliceGame.Busy` game))
  (if (`self.Chasing`)
    (if (or (> dist (`/Game/Splice/Data/BP_Tuning.RaiderGiveUpDistance` tun)) (not onFloor) busy)
      (set `self.Chasing` false)
      (set `self.Target` (`self.Home`)))
    (else
      (if (and (< dist notice) onFloor (not busy))
        (set `self.Chasing` true))))
  (bind me (`Actor.K2_GetActorLocation` self))
  (bind ploc (`Actor.K2_GetActorLocation` pawn))
  (if (`self.Chasing`)
    (set `self.Target` (`KismetMathLibrary.MakeVector` (.x ploc) (.y ploc) (.z me)))
    (else
      (if (< (`KismetMathLibrary.Vector_Distance` me (`self.Target`)) 20.0)
        (set `self.Target` (+ (`self.Home`) (`KismetMathLibrary.MakeVector`
          (`KismetMathLibrary.RandomFloatInRange` -300.0 300.0)
          (`KismetMathLibrary.RandomFloatInRange` -300.0 300.0)
          0.0))))))
  (`self.K2_SetActorLocation` :`NewLocation`
    (`KismetMathLibrary.VInterpTo_Constant` me (`self.Target`) DeltaSeconds
      (select `bool` (`self.Chasing`)
        :`true` (`/Game/Splice/Data/BP_Tuning.RaiderSpeed` tun)
        :`false` (`/Game/Splice/Data/BP_Tuning.RaiderWanderSpeed` tun))))
  (bind now (`GameplayStatics.GetTimeSeconds`))
  (if (and (`self.Chasing`) onFloor
           (< dist (`/Game/Splice/Data/BP_Tuning.RaiderHitRange` tun))
           (> (- now (`self.LastHit`)) (`/Game/Splice/Data/BP_Tuning.RaiderHitCooldown` tun)))
    (set `self.LastHit` now)
    (`/Game/Splice/Blueprints/BP_SpliceGame.DamagePlayer` game)))
