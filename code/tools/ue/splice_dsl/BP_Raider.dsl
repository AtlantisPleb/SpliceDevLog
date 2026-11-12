; A party-goer or a patrol robot. The same logic runs in BP_Raider and BP_Imperial;
; bImperial picks the behaviour.
; - Raider: dances in place. Leaves the player alone unless hit, then chases.
; - Imperial robot: walks its Route. Ignores a player whose Heat is cool; the hotter the
;   player, the further away it notices and chases.
; Both hit for one heart on contact and give up when the player is far away or up on a
; catwalk. F hits them: each hit stuns them briefly; at 0 HP they drop a robot part.
(event `self.ReceiveBeginPlay`
  (set `self.Home` (`Actor.K2_GetActorLocation` self))
  (set `self.Target` (`Actor.K2_GetActorLocation` self))
  (set `self.DancePhase` (`KismetMathLibrary.RandomFloatInRange` 0.0 6.28))
  (bind game (cast `/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C`
    (`GameplayStatics.GetActorOfClass` "/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C")))
  (set `self.Game` game)
  (if (<= (`self.HP`) 0)
    (if (`self.bImperial`)
      (set `self.HP` (`/Game/Splice/Data/BP_Tuning.ImperialHP` (`/Game/Splice/Blueprints/BP_SpliceGame.Tuning` game)))
      (else
        (set `self.HP` (`/Game/Splice/Data/BP_Tuning.RaiderHP` (`/Game/Splice/Blueprints/BP_SpliceGame.Tuning` game)))))))

(event `self.ReceiveTick`
  (params (DeltaSeconds))
  (bind pawn (`GameplayStatics.GetPlayerPawn` 0))
  (bind game (`self.Game`))
  (if (not (and (`KismetSystemLibrary.IsValid` pawn) (`KismetSystemLibrary.IsValid` game)))
    (return))
  (bind now (`GameplayStatics.GetTimeSeconds`))
  (if (< now (`self.StunnedUntil`))
    (return))
  (bind tun (`/Game/Splice/Blueprints/BP_SpliceGame.Tuning` game))
  (bind imperial (`self.bImperial`))
  (bind me (`Actor.K2_GetActorLocation` self))
  (bind ploc (`Actor.K2_GetActorLocation` pawn))
  (bind dist (`Actor.GetHorizontalDistanceTo` self pawn))
  (bind onFloor (< (`Actor.GetVerticalDistanceTo` self pawn) (`/Game/Splice/Data/BP_Tuning.CatwalkSafeHeight` tun)))
  (bind busy (`/Game/Splice/Blueprints/BP_SpliceGame.Busy` game))
  (bind heat01 (/ (`/Game/Splice/Blueprints/BP_SpliceGame.Heat` game)
                  (`KismetMathLibrary.FMax` (`/Game/Splice/Data/BP_Tuning.MaxHeat` tun) 1.0)))
  (bind giveUp (`/Game/Splice/Data/BP_Tuning.RaiderGiveUpDistance` tun))
  ; An Imperial robot hunts by Heat. A raider only reacts to being hit.
  (bind wants (select `bool` imperial
    :`true` (< dist (* (`/Game/Splice/Data/BP_Tuning.ImperialNoticeRange` tun) heat01 2.0))
    :`false` (`self.Provoked`)))
  (if (`self.Chasing`)
    (if (or (> dist giveUp) (not onFloor) busy)
      (set `self.Chasing` false)
      (set `self.Provoked` false))
    (else
      (if (and wants onFloor (not busy) (< dist giveUp))
        (set `self.Chasing` true))))
  (if (`self.Chasing`)
    (`self.K2_SetActorLocation` :`NewLocation`
      (`KismetMathLibrary.VInterpTo_Constant` me
        (`KismetMathLibrary.MakeVector` (.x ploc) (.y ploc) (.z me)) DeltaSeconds
        (select `bool` imperial
          :`true` (`/Game/Splice/Data/BP_Tuning.ImperialSpeed` tun)
          :`false` (`/Game/Splice/Data/BP_Tuning.RaiderSpeed` tun))))
    (if (and (< dist (`/Game/Splice/Data/BP_Tuning.RaiderHitRange` tun))
             (> (- now (`self.LastHit`)) (`/Game/Splice/Data/BP_Tuning.RaiderHitCooldown` tun)))
      (set `self.LastHit` now)
      (`/Game/Splice/Blueprints/BP_SpliceGame.DamagePlayer` game))
    (return))
  (if imperial
    (`self.Patrol` DeltaSeconds)
    (else
      (`self.Dance` DeltaSeconds))))

; Walk the Route, waypoint to waypoint, in a loop.
(event `Patrol`
  (params (DeltaSeconds :type "Float (single-precision)"))
  (bind route (`self.Route`))
  (bind count (`KismetArrayLibrary.Array_Length` route))
  (if (<= count 0)
    (return))
  (bind me (`Actor.K2_GetActorLocation` self))
  (bind wp (`Actor.K2_GetActorLocation` (`KismetArrayLibrary.Array_Get` route (`self.RouteIndex`))))
  (bind dest (`KismetMathLibrary.MakeVector` (.x wp) (.y wp) (.z me)))
  (if (< (`KismetMathLibrary.Vector_Distance` me dest) 30.0)
    (set `self.RouteIndex` (mod (+ (`self.RouteIndex`) 1) count)))
  (`self.K2_SetActorLocation` :`NewLocation`
    (`KismetMathLibrary.VInterpTo_Constant` me dest DeltaSeconds
      (`/Game/Splice/Data/BP_Tuning.ImperialPatrolSpeed` (`/Game/Splice/Blueprints/BP_SpliceGame.Tuning` (`self.Game`))))))

; Walk back to the home spot if away from it; once there, bob and sway in place.
(event `Dance`
  (params (DeltaSeconds :type "Float (single-precision)"))
  (bind me (`Actor.K2_GetActorLocation` self))
  (bind home (`self.Home`))
  (bind now (`GameplayStatics.GetTimeSeconds`))
  (bind phase (`self.DancePhase`))
  (if (> (`KismetMathLibrary.Vector_Distance2D` me home) 30.0)
    (`self.K2_SetActorLocation` :`NewLocation`
      (`KismetMathLibrary.VInterpTo_Constant` me home DeltaSeconds
        (`/Game/Splice/Data/BP_Tuning.RaiderWanderSpeed` (`/Game/Splice/Blueprints/BP_SpliceGame.Tuning` (`self.Game`)))))
    (return))
  (`self.K2_SetActorLocation` :`NewLocation`
    (+ home (`KismetMathLibrary.MakeVector` 0.0 0.0
      (* (`KismetMathLibrary.Abs` (`KismetMathLibrary.Sin` (+ (* now 6.0) phase))) 24.0))))
  (`self.K2_SetActorRotation` :`NewRotation`
    (`KismetMathLibrary.MakeRotator` 0.0 0.0 (* (`KismetMathLibrary.Sin` (+ (* now 2.2) phase)) 55.0))))

; The player hit this one with F.
(event `TakeHit`
  (bind game (`self.Game`))
  (set `self.HP` (- (`self.HP`) 1))
  (set `self.Provoked` true)
  (set `self.StunnedUntil` (+ (`GameplayStatics.GetTimeSeconds`)
    (`/Game/Splice/Data/BP_Tuning.StunDuration` (`/Game/Splice/Blueprints/BP_SpliceGame.Tuning` game))))
  (if (<= (`self.HP`) 0)
    (`/Game/Splice/Blueprints/BP_SpliceGame.NPCDefeated` game (`self.DropName`))
    (`Actor.K2_DestroyActor` self)))
