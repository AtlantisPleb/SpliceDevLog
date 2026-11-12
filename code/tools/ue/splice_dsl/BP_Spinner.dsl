; Set dressing that moves: spins (yaw and roll, degrees per second) and can bob up and
; down. Used for the light bars over the dance floor and the memory diorama.
(event `self.ReceiveBeginPlay`
  (set `self.Home` (`Actor.K2_GetActorLocation` self)))

(event `self.ReceiveTick`
  (params (DeltaSeconds))
  (`self.K2_AddActorLocalRotation` :`DeltaRotation`
    (`KismetMathLibrary.MakeRotator` (* (`self.RollRate`) DeltaSeconds) 0.0 (* (`self.Rate`) DeltaSeconds)))
  (if (> (`self.Bob`) 0.0)
    (`self.K2_SetActorLocation` :`NewLocation`
      (+ (`self.Home`) (`KismetMathLibrary.MakeVector` 0.0 0.0
        (* (`KismetMathLibrary.Sin` (* (`GameplayStatics.GetTimeSeconds`) 2.0)) (`self.Bob`)))))))
