; The banned bot. It wakes when its wall is down and the player is near. Every
; BossSweepTime seconds its arm glows red, then sweeps: a player in range loses a heart.
; F next to a weak point stuns it (it turns gray). All 3 stunned: it powers down and
; drops the banned core.
(event `self.ReceiveBeginPlay`
  (bind game (cast `/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C`
    (`GameplayStatics.GetActorOfClass` "/Game/Splice/Blueprints/BP_SpliceGame.BP_SpliceGame_C")))
  (set `self.Game` game))

(event `self.ReceiveTick`
  (params (DeltaSeconds))
  (if (`self.Dead`)
    (return))
  (bind pawn (`GameplayStatics.GetPlayerPawn` 0))
  (bind game (`self.Game`))
  (if (not (and (`KismetSystemLibrary.IsValid` pawn) (`KismetSystemLibrary.IsValid` game)))
    (return))
  (bind tun (`/Game/Splice/Blueprints/BP_SpliceGame.Tuning` game))
  (bind now (`GameplayStatics.GetTimeSeconds`))
  (bind every (`/Game/Splice/Data/BP_Tuning.BossSweepTime` tun))
  (if (not (`self.Active`))
    (if (and (< (`Actor.GetDistanceTo` self pawn) (`/Game/Splice/Data/BP_Tuning.BossWakeRange` tun))
             (not (`KismetSystemLibrary.IsValid`
               (`GameplayStatics.GetActorOfClass` "/Game/Splice/Blueprints/BP_BossWall.BP_BossWall_C"))))
      (set `self.Active` true)
      (set `self.NextSweep` (+ now every)))
    (return))
  ; The arm spins for half a second after each sweep starts.
  (if (< now (`self.SpinUntil`))
    (`SceneComponent.K2_AddRelativeRotation` :`self` (`self.Arm`)
      :`DeltaRotation` (`KismetMathLibrary.MakeRotator` 0.0 0.0 (* 720.0 DeltaSeconds))))
  ; Warning: the arm turns red shortly before it sweeps.
  (if (and (not (`self.Raised`)) (> now (- (`self.NextSweep`) 0.9)))
    (set `self.Raised` true)
    (`PrimitiveComponent.SetMaterial` (`self.Arm`) 0 "/Game/Splice/Materials/M_Red.M_Red"))
  (if (> now (`self.NextSweep`))
    (set `self.NextSweep` (+ now every))
    (set `self.Raised` false)
    (set `self.SpinUntil` (+ now 0.5))
    (`PrimitiveComponent.SetMaterial` (`self.Arm`) 0 "/Game/Splice/Materials/M_Dark.M_Dark")
    (if (< (`Actor.GetDistanceTo` self pawn) (`/Game/Splice/Data/BP_Tuning.BossSweepRange` tun))
      (`/Game/Splice/Blueprints/BP_SpliceGame.DamagePlayer` game))))

; The game calls this when the player presses F near the boss.
(event `TryStun`
  (params (From :type "Vector Structure"))
  (if (or (`self.Dead`) (not (`self.Active`)))
    (return))
  (bind reach (`/Game/Splice/Data/BP_Tuning.BossStunReach` (`/Game/Splice/Blueprints/BP_SpliceGame.Tuning` (`self.Game`))))
  (if (and (not (`self.Stun1`))
           (< (`KismetMathLibrary.Vector_Distance` From (`SceneComponent.K2_GetComponentLocation` (`self.WP1`))) reach))
    (set `self.Stun1` true)
    (`PrimitiveComponent.SetMaterial` (`self.WP1`) 0 "/Game/Splice/Materials/M_Gray.M_Gray")
    (`self.CheckDown`)
    (return))
  (if (and (not (`self.Stun2`))
           (< (`KismetMathLibrary.Vector_Distance` From (`SceneComponent.K2_GetComponentLocation` (`self.WP2`))) reach))
    (set `self.Stun2` true)
    (`PrimitiveComponent.SetMaterial` (`self.WP2`) 0 "/Game/Splice/Materials/M_Gray.M_Gray")
    (`self.CheckDown`)
    (return))
  (if (and (not (`self.Stun3`))
           (< (`KismetMathLibrary.Vector_Distance` From (`SceneComponent.K2_GetComponentLocation` (`self.WP3`))) reach))
    (set `self.Stun3` true)
    (`PrimitiveComponent.SetMaterial` (`self.WP3`) 0 "/Game/Splice/Materials/M_Gray.M_Gray")
    (`self.CheckDown`)))

(event `CheckDown`
  (bind game (`self.Game`))
  (if (not (and (`self.Stun1`) (`self.Stun2`) (`self.Stun3`)))
    (`/Game/Splice/Blueprints/BP_SpliceGame.ShowMessage` game "Weak point stunned")
    (return))
  (set `self.Dead` true)
  (`PrimitiveComponent.SetMaterial` (`self.Arm`) 0 "/Game/Splice/Materials/M_Gray.M_Gray")
  (`PrimitiveComponent.SetMaterial` (`self.Band`) 0 "/Game/Splice/Materials/M_Gray.M_Gray")
  (`|SpawnActorFromClass`
    :`Class` "/Game/Splice/Blueprints/BP_BannedCore.BP_BannedCore_C"
    :`SpawnTransform` (`KismetMathLibrary.MakeTransform`
      (+ (`Actor.K2_GetActorLocation` self) (`KismetMathLibrary.MakeVector` -360.0 0.0 -130.0))
      (`Actor.K2_GetActorRotation` self)
      (1 1 1))
    :`CollisionHandlingOverride` "AlwaysSpawn")
  (`/Game/Splice/Blueprints/BP_SpliceGame.SetObjective` game "Take the banned core")
  (`/Game/Splice/Blueprints/BP_SpliceGame.ShowMessage` game "The banned bot powers down. Its core is yours."))
