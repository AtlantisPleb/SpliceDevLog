; The Digger. Runs its two cards in order, about 2 seconds each.
(event `Run`
  (bind cards (`self.Cards`))
  (`KismetSystemLibrary.Delay` 0.6)
  (`self.DoCard` (`KismetArrayLibrary.Array_Get` cards 0))
  (`KismetSystemLibrary.Delay` 2.4)
  (`self.DoCard` (`KismetArrayLibrary.Array_Get` cards 1))
  (`KismetSystemLibrary.Delay` 2.4)
  (`self.Finish`))

(event `DoCard`
  (params (Card :type String))
  (if (== Card "MOVE")
    (`self.DoMove`)
    (else
      (`self.DoDrill`))))

; MOVE: drive forward (+X) until 1 m from the rubble, or 5 m at most.
(event `DoMove`
  (bind loc (`Actor.K2_GetActorLocation` self))
  (bind rubble (`GameplayStatics.GetActorOfClass` "/Game/Splice/Blueprints/BP_Rubble.BP_Rubble_C"))
  (set `self.Travel` 500.0)
  (if (`KismetSystemLibrary.IsValid` rubble)
    (set `self.Travel`
      (`KismetMathLibrary.FClamp`
        (- (.x (`Actor.K2_GetActorLocation` rubble)) (.x loc) 190.0)
        0.0 500.0)))
  (bind travel (`self.Travel`))
  (`KismetSystemLibrary.MoveComponentTo`
    :`Component` (`self.RootComponent`)
    :`TargetRelativeLocation` (+ loc (`KismetMathLibrary.MakeVector` travel 0.0 0.0))
    :`TargetRelativeRotation` (`Actor.K2_GetActorRotation` self)
    :`bEaseOut` true
    :`bEaseIn` true
    :`OverTime` (+ 0.2 (/ travel 300.0))))

; DRILL: if rubble is within reach in front, destroy the whole wall. Otherwise drill air.
(event `DoDrill`
  (bind loc (`Actor.K2_GetActorLocation` self))
  (bind rubble (`GameplayStatics.GetActorOfClass` "/Game/Splice/Blueprints/BP_Rubble.BP_Rubble_C"))
  (set `self.CanDrill` false)
  (if (`KismetSystemLibrary.IsValid` rubble)
    (set `self.CanDrill` (< (- (.x (`Actor.K2_GetActorLocation` rubble)) (.x loc)) 260.0)))
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
  (bind wall (`GameplayStatics.GetAllActorsOfClass` "/Game/Splice/Blueprints/BP_Rubble.BP_Rubble_C"))
  (for piece wall
    (`Actor.K2_DestroyActor` piece))
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

; After both cards: success if the rubble is gone. On failure the bot is removed after 2 s.
(event `Finish`
  (bind ok (not (`KismetSystemLibrary.IsValid`
    (`GameplayStatics.GetActorOfClass` "/Game/Splice/Blueprints/BP_Rubble.BP_Rubble_C"))))
  (`/Game/Splice/Blueprints/BP_SpliceGame.BotFinished` (`self.Game`) ok)
  (if (not ok)
    (`KismetSystemLibrary.Delay` 2.0)
    (`Actor.K2_DestroyActor` self)))
