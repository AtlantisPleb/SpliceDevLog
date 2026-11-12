; The Digger. It follows the player (Mode 0). On Run it drives to the job site (Mode 1),
; runs its cards in order (Mode 2), reports back, and follows again.
(event `self.ReceiveTick`
  (params (DeltaSeconds))
  (if (!= (`self.Mode`) 0)
    (return))
  (bind pawn (`GameplayStatics.GetPlayerPawn` 0))
  (bind game (`self.Game`))
  (if (not (and (`KismetSystemLibrary.IsValid` pawn) (`KismetSystemLibrary.IsValid` game)))
    (return))
  (bind tun (`/Game/Splice/Blueprints/BP_SpliceGame.Tuning` game))
  (bind me (`Actor.K2_GetActorLocation` self))
  ; Its place is beside the player and a little behind.
  (bind goal (+ (`Actor.K2_GetActorLocation` pawn)
    (* (`Actor.GetActorRightVector` pawn) 120.0)
    (* (`Actor.GetActorForwardVector` pawn) -70.0)
    (`KismetMathLibrary.MakeVector` 0.0 0.0 -46.0)))
  (if (> (`KismetMathLibrary.Vector_Distance` me goal) (`/Game/Splice/Data/BP_Tuning.DiggerSnapDistance` tun))
    (`self.K2_SetActorLocation` :`NewLocation` goal)
    (return))
  (`self.K2_SetActorLocation` :`NewLocation`
    (`KismetMathLibrary.VInterpTo_Constant` me goal DeltaSeconds (`/Game/Splice/Data/BP_Tuning.DiggerFollowSpeed` tun)))
  (`self.K2_SetActorRotation` :`NewRotation`
    (`KismetMathLibrary.MakeRotator` 0.0 0.0 (.yaw (`Actor.K2_GetActorRotation` pawn)))))

(event `Run`
  (set `self.Mode` 1)
  (bind tun (`/Game/Splice/Blueprints/BP_SpliceGame.Tuning` (`self.Game`)))
  (bind site (`self.Site`))
  (if (`self.GoalWall`)
    (set `self.Obstacle` (`GameplayStatics.GetActorOfClass` "/Game/Splice/Blueprints/BP_BossWall.BP_BossWall_C"))
    (else
      (set `self.Obstacle` (`GameplayStatics.GetActorOfClass` "/Game/Splice/Blueprints/BP_Rubble.BP_Rubble_C"))))
  ; Drive from the player's side to the job site, so the player sees it go.
  (bind dest (`Actor.K2_GetActorLocation` site))
  (`KismetSystemLibrary.MoveComponentTo`
    :`Component` (`self.RootComponent`)
    :`TargetRelativeLocation` dest
    :`TargetRelativeRotation` (`Actor.K2_GetActorRotation` site)
    :`bEaseOut` true
    :`bEaseIn` true
    :`OverTime` (`KismetMathLibrary.FMax` 0.4
      (/ (`KismetMathLibrary.Vector_Distance` (`Actor.K2_GetActorLocation` self) dest)
         (`/Game/Splice/Data/BP_Tuning.DiggerTravelSpeed` tun))))
  (set `self.Mode` 2)
  (bind cards (`self.Cards`))
  (bind gap (`/Game/Splice/Data/BP_Tuning.DiggerCardInterval` tun))
  (`KismetSystemLibrary.Delay` 0.5)
  (`self.DoCard` (`KismetArrayLibrary.Array_Get` cards 0))
  (`KismetSystemLibrary.Delay` gap)
  (`self.DoCard` (`KismetArrayLibrary.Array_Get` cards 1))
  (`KismetSystemLibrary.Delay` gap)
  (if (> (`KismetArrayLibrary.Array_Length` cards) 2)
    (`self.DoCard` (`KismetArrayLibrary.Array_Get` cards 2))
    (`KismetSystemLibrary.Delay` gap))
  (`self.Finish`))

(event `DoCard`
  (params (Card :type String))
  (if (`KismetStringLibrary.EqualEqual_StrStr` Card "MOVE")
    (`self.DoMove`)
    (elif (`KismetStringLibrary.EqualEqual_StrStr` Card "DRILL+")
      (`self.DoDrill` true)
      (else
        (`self.DoDrill` false)))))

; MOVE: drive forward (+X) and stop just short of the obstacle.
(event `DoMove`
  (bind tun (`/Game/Splice/Blueprints/BP_SpliceGame.Tuning` (`self.Game`)))
  (bind loc (`Actor.K2_GetActorLocation` self))
  (bind obstacle (`self.Obstacle`))
  (bind maxMove (`/Game/Splice/Data/BP_Tuning.DiggerMaxMove` tun))
  (set `self.Travel` maxMove)
  (if (`KismetSystemLibrary.IsValid` obstacle)
    (set `self.Travel`
      (`KismetMathLibrary.FClamp`
        (- (.x (`Actor.K2_GetActorLocation` obstacle)) (.x loc) (`/Game/Splice/Data/BP_Tuning.DiggerStopShort` tun))
        0.0 maxMove)))
  (bind travel (`self.Travel`))
  (`KismetSystemLibrary.MoveComponentTo`
    :`Component` (`self.RootComponent`)
    :`TargetRelativeLocation` (+ loc (`KismetMathLibrary.MakeVector` travel 0.0 0.0))
    :`TargetRelativeRotation` (`Actor.K2_GetActorRotation` self)
    :`bEaseOut` true
    :`bEaseIn` true
    :`OverTime` (+ 0.2 (/ travel 300.0))))

; DRILL: breaks the obstacle if it is within reach. The boss wall only gives to DRILL+.
(event `DoDrill`
  (params (Plus :type Boolean))
  (bind tun (`/Game/Splice/Blueprints/BP_SpliceGame.Tuning` (`self.Game`)))
  (bind loc (`Actor.K2_GetActorLocation` self))
  (bind obstacle (`self.Obstacle`))
  (set `self.CanDrill` false)
  (if (`KismetSystemLibrary.IsValid` obstacle)
    (set `self.CanDrill` (< (- (.x (`Actor.K2_GetActorLocation` obstacle)) (.x loc))
                            (`/Game/Splice/Data/BP_Tuning.DiggerDrillReach` tun))))
  (if (and (`self.CanDrill`) (`self.GoalWall`) (not Plus))
    (`/Game/Splice/Blueprints/BP_SpliceGame.ShowMessage` (`self.Game`) "This wall is too hard. It needs DRILL+.")
    (`self.DrillAir`)
    (return))
  (if (`self.CanDrill`)
    (`self.DrillHit`)
    (else
      (`self.DrillAir`))))

(event `DrillHit`
  (bind loc (`Actor.K2_GetActorLocation` self))
  (bind root (`self.RootComponent`))
  (bind rot (`Actor.K2_GetActorRotation` self))
  (`KismetSystemLibrary.MoveComponentTo` :`Component` root
    :`TargetRelativeLocation` (+ loc (`KismetMathLibrary.MakeVector` 40.0 0.0 0.0))
    :`TargetRelativeRotation` rot :`OverTime` 0.15)
  (if (`self.GoalWall`)
    (`Actor.K2_DestroyActor` (`self.Obstacle`))
    (else
      (for piece (`GameplayStatics.GetAllActorsOfClass` "/Game/Splice/Blueprints/BP_Rubble.BP_Rubble_C")
        (`Actor.K2_DestroyActor` piece))))
  (`KismetSystemLibrary.MoveComponentTo` :`Component` root
    :`TargetRelativeLocation` loc
    :`TargetRelativeRotation` rot :`OverTime` 0.25))

; Drilling air: flash red and shake in place.
(event `DrillAir`
  (bind loc (`Actor.K2_GetActorLocation` self))
  (bind root (`self.RootComponent`))
  (bind rot (`Actor.K2_GetActorRotation` self))
  (bind body (`self.Body`))
  (`PrimitiveComponent.SetMaterial` body 0 "/Game/Splice/Materials/M_Red.M_Red")
  (`KismetSystemLibrary.MoveComponentTo` :`Component` root
    :`TargetRelativeLocation` (+ loc (`KismetMathLibrary.MakeVector` 0.0 18.0 0.0))
    :`TargetRelativeRotation` rot :`OverTime` 0.08)
  (`KismetSystemLibrary.MoveComponentTo` :`Component` root
    :`TargetRelativeLocation` (+ loc (`KismetMathLibrary.MakeVector` 0.0 -18.0 0.0))
    :`TargetRelativeRotation` rot :`OverTime` 0.12)
  (`KismetSystemLibrary.MoveComponentTo` :`Component` root
    :`TargetRelativeLocation` (+ loc (`KismetMathLibrary.MakeVector` 0.0 18.0 0.0))
    :`TargetRelativeRotation` rot :`OverTime` 0.12)
  (`KismetSystemLibrary.MoveComponentTo` :`Component` root
    :`TargetRelativeLocation` loc
    :`TargetRelativeRotation` rot :`OverTime` 0.08)
  (`KismetSystemLibrary.Delay` 0.4)
  (`PrimitiveComponent.SetMaterial` body 0 "/Game/Splice/Materials/M_Orange.M_Orange"))

; After the cards: success if the obstacle is gone. Either way the Digger goes back
; to following the player.
(event `Finish`
  (bind ok (not (`KismetSystemLibrary.IsValid` (`self.Obstacle`))))
  (`/Game/Splice/Blueprints/BP_SpliceGame.BotFinished` (`self.Game`) ok)
  (set `self.Mode` 0))
