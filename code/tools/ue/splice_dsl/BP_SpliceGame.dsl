; Splice game state: inventory, edit bay, the Digger, Heat, hearts, fights, time of day,
; the memory ending and the HUD. Every tuning number comes from DA_Tuning (self.Tuning).

(event `self.ReceiveBeginPlay`
  (bind pc (`GameplayStatics.GetPlayerController` 0))
  (`Actor.EnableInput` self pc)
  (bind hud (`|CreateWidget` :`Class` "/Game/Splice/UI/WBP_HUD.WBP_HUD_C" :`OwningPlayer` pc))
  (set `self.HUD` hud)
  (`UserWidget.AddToViewport` :`self` hud)
  (set `self.Hearts` (`/Game/Splice/Data/BP_Tuning.MaxHearts` (`self.Tuning`)))
  (set `self.Objective` "Splice the Digger, drill the rubble")
  (`self.SetPhase` 1)
  (`self.ShowMessage` "Find the Digger's parts in the scrap room."))

; Heat cools only while the player is at the rover or a stash crate.
(event `self.ReceiveTick`
  (params (DeltaSeconds))
  (if (and (or (`self.NearRover`) (`self.NearCrate`)) (> (`self.Heat`) 0.0))
    (set `self.Heat` (`KismetMathLibrary.FMax` 0.0
      (- (`self.Heat`) (* (`/Game/Splice/Data/BP_Tuning.HeatCoolRate` (`self.Tuning`)) DeltaSeconds))))
    (`self.RefreshHUD`)))

; ---- Keys

; TAB opens or closes the edit bay at the rover or a stash crate. E does the same, in
; case a browser takes TAB for itself.
(event `Key|E`
  (params (Key))
  (:`Pressed` (`self.ToggleEditBay`))
  (:`Released`))

(event `Key|Tab`
  (params (Key))
  (:`Pressed` (`self.ToggleEditBay`))
  (:`Released`))

; F hits whoever is in reach, or stuns a boss weak point.
(event `Key|F`
  (params (Key))
  (:`Pressed` (`self.Attack`))
  (:`Released`))

; ---- Edit bay

(event `ToggleEditBay`
  (if (`self.BayOpen`)
    (`self.CloseEditBay`)
    (else
      (if (or (`self.NearRover`) (`self.NearCrate`))
        (`self.OpenEditBay`)))))

(event `OpenEditBay`
  (if (or (`self.BotRunning`) (`self.Busy`) (`self.MemoryPlaying`))
    (return))
  (bind pc (`GameplayStatics.GetPlayerController` 0))
  (bind bay (`|CreateWidget` :`Class` "/Game/Splice/UI/WBP_EditBay.WBP_EditBay_C" :`OwningPlayer` pc))
  (set `self.EditBay` bay)
  (`UserWidget.AddToViewport` :`self` bay)
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_EditBay.BtnArm` bay) (`|CreateDelegate` :!event `ClickArm`))
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_EditBay.BtnTreads` bay) (`|CreateDelegate` :!event `ClickTreads`))
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_EditBay.BtnBattery` bay) (`|CreateDelegate` :!event `ClickBattery`))
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_EditBay.BtnMove` bay) (`|CreateDelegate` :!event `ClickMove`))
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_EditBay.BtnDrill` bay) (`|CreateDelegate` :!event `ClickDrill`))
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_EditBay.BtnDrillPlus` bay) (`|CreateDelegate` :!event `ClickDrillPlus`))
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_EditBay.BtnClear` bay) (`|CreateDelegate` :!event `ClearStrip`))
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_EditBay.BtnDeploy` bay) (`|CreateDelegate` :!event `Deploy`))
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_EditBay.BtnSpliceCore` bay) (`|CreateDelegate` :!event `SpliceCore`))
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_EditBay.BtnClose` bay) (`|CreateDelegate` :!event `CloseEditBay`))
  (set `PlayerController.bShowMouseCursor` :`self` pc :`bShowMouseCursor` true)
  (`WidgetBlueprintLibrary.SetInputMode_GameAndUIEx` :`PlayerController` pc)
  (set `self.BayOpen` true)
  (`self.RefreshEditBay`)
  (`self.RefreshHUD`))

(event `CloseEditBay`
  (bind bay (`self.EditBay`))
  (if (`KismetSystemLibrary.IsValid` bay)
    (`Widget.RemoveFromParent` bay))
  (bind pc (`GameplayStatics.GetPlayerController` 0))
  (set `PlayerController.bShowMouseCursor` :`self` pc :`bShowMouseCursor` false)
  (`WidgetBlueprintLibrary.SetInputMode_GameOnly` pc)
  (set `self.BayOpen` false)
  (`self.RefreshHUD`))

(event `ClickArm` (`self.PlaceItem` "Drill Arm"))
(event `ClickTreads` (`self.PlaceItem` "Treads"))
(event `ClickBattery` (`self.PlaceItem` "Battery"))
(event `ClickMove` (`self.PlaceItem` "MOVE"))
(event `ClickDrill` (`self.PlaceItem` "DRILL"))
(event `ClickDrillPlus` (`self.PlaceItem` "DRILL+"))

; Pickups add to the inventory.
(event `PickUp`
  (params (Item :type String))
  (`KismetArrayLibrary.Array_AddUnique` (`self.Inventory`) Item)
  (`self.ShowMessage` (`KismetStringLibrary.Concat_StrStr` "Picked up: " Item))
  (`self.RefreshHUD`))

; Hardware fills its matching slot. Cards go into the next empty strip slot (3 at most).
; The moment all three hardware slots are full, the Digger wakes up and follows you.
(event `PlaceItem`
  (params (Item :type String))
  (if (not (`KismetArrayLibrary.Array_Contains` (`self.Inventory`) Item))
    (return))
  (if (== Item "Drill Arm")
    (set `self.SlotArm` Item)
    (elif (== Item "Treads")
      (set `self.SlotTreads` Item)
      (elif (== Item "Battery")
        (set `self.SlotBattery` Item)
        (else
          (if (< (`KismetArrayLibrary.Array_Length` (`self.Strip`)) 3)
            (`KismetArrayLibrary.Array_Add` (`self.Strip`) Item))))))
  (if (and
        (not (`KismetStringLibrary.IsEmpty` (`self.SlotArm`)))
        (not (`KismetStringLibrary.IsEmpty` (`self.SlotTreads`)))
        (not (`KismetStringLibrary.IsEmpty` (`self.SlotBattery`)))
        (not (`KismetSystemLibrary.IsValid` (`self.Bot`))))
    (`self.WakeDigger`))
  (`self.RefreshEditBay`))

(event `WakeDigger`
  (bind pawn (`GameplayStatics.GetPlayerPawn` 0))
  (bind bot (`|SpawnActorFromClass`
    :`Class` "/Game/Splice/Blueprints/BP_Bot.BP_Bot_C"
    :`SpawnTransform` (`KismetMathLibrary.MakeTransform`
      (+ (`Actor.K2_GetActorLocation` pawn) (`KismetMathLibrary.MakeVector` 0.0 130.0 -46.0))
      (`Actor.K2_GetActorRotation` pawn)
      (1 1 1))
    :`CollisionHandlingOverride` "AlwaysSpawn"))
  (set `self.Bot` bot)
  (set `/Game/Splice/Blueprints/BP_Bot.Game` :`self` bot :`Game` self)
  (`self.ShowMessage` "The Digger wakes up. It follows you now."))

(event `ClearStrip`
  (`KismetArrayLibrary.Array_Clear` (`self.Strip`))
  (`self.RefreshEditBay`))

; DEPLOY needs the Digger built and at least 2 cards. The Digger drives from your side
; to the job: the rubble when you deploy at the rover, the boss wall at a stash crate.
(event `Deploy`
  (bind bot (`self.Bot`))
  (if (not (and
             (`KismetSystemLibrary.IsValid` bot)
             (>= (`KismetArrayLibrary.Array_Length` (`self.Strip`)) 2)))
    (return))
  (bind atCrate (`self.NearCrate`))
  (set `self.DeployAtCrate` atCrate)
  (`self.CloseEditBay`)
  (set `self.BotRunning` true)
  (set `/Game/Splice/Blueprints/BP_Bot.Cards` :`self` bot :`Cards` (`self.Strip`))
  (set `/Game/Splice/Blueprints/BP_Bot.GoalWall` :`self` bot :`GoalWall` atCrate)
  (if atCrate
    (set `/Game/Splice/Blueprints/BP_Bot.Site` :`self` bot :`Site` (`self.BossSite`))
    (else
      (set `/Game/Splice/Blueprints/BP_Bot.Site` :`self` bot :`Site` (`self.BotSpawn`))))
  (`/Game/Splice/Blueprints/BP_Bot.Run` bot)
  (`self.ShowMessage` "Deploying the Digger...")
  (`self.RefreshHUD`))

(event `BotFinished`
  (params (Success :type Boolean))
  (set `self.BotRunning` false)
  (if Success
    (if (`self.DeployAtCrate`)
      (`self.SetObjective` "Stun the banned bot's 3 weak points  [F]")
      (`self.ShowMessage` "The wall is down.")
      (else
        (`self.SetObjective` "Go through the tunnel")
        (`self.ShowMessage` "Scene cut clean. The tunnel is open!")))
    (else
      (`self.ShowMessage` "Bad cut. Re-edit and deploy again.")))
  (`self.RefreshHUD`))

(event `ShowMessage`
  (params (Msg :type String))
  (bind msgText (`/Game/Splice/UI/WBP_HUD.MessageText` (`self.HUD`)))
  (`TextBlock.SetText` msgText (`KismetTextLibrary.Conv_StringToText` Msg))
  (`KismetSystemLibrary.Delay` 3.5)
  (`TextBlock.SetText` msgText ""))

; ---- Rover, stash crate and checkpoint

; Reaching the rover is the checkpoint: it saves what you carry.
(event `SetNearRover`
  (params (Near :type Boolean))
  (set `self.NearRover` Near)
  (if Near
    (`self.SaveCheckpoint`))
  (`self.RefreshHUD`))

(event `SetNearCrate`
  (params (Near :type Boolean))
  (set `self.NearCrate` Near)
  (`self.RefreshHUD`))

(event `SaveCheckpoint`
  (set `self.SavedInventory` (`self.Inventory`))
  (set `self.BannedSaved` (`self.BannedCarried`))
  (for frag (`GameplayStatics.GetAllActorsOfClass` "/Game/Splice/Blueprints/BP_Fragment.BP_Fragment_C")
    (`/Game/Splice/Blueprints/BP_Fragment.OnCheckpoint` frag)))

; ---- Pickups in the night zone

; The one blue piece: the banned DRILL+ part. It raises Heat.
(event `PickUpBanned`
  (params (Item :type String))
  (`KismetArrayLibrary.Array_AddUnique` (`self.Inventory`) Item)
  (set `self.BannedCarried` (+ (`self.BannedCarried`) 1))
  (`self.SetObjective` "Take DRILL+ to the stash crate past the corridor")
  (`self.AddHeat` (`/Game/Splice/Data/BP_Tuning.HeatPerBannedPiece` (`self.Tuning`)))
  (`self.ShowMessage` "You found the blue piece: DRILL+. Heat is rising."))

(event `PickUpCell`
  (set `self.Cells` (+ (`self.Cells`) 1))
  (`self.RefreshHUD`)
  (`self.ShowMessage` "Battery cell picked up"))

; ---- Heat, hearts and respawn

(event `AddHeat`
  (params (Amount :type "Float (double-precision)"))
  (bind maxHeat (`/Game/Splice/Data/BP_Tuning.MaxHeat` (`self.Tuning`)))
  (set `self.Heat` (`KismetMathLibrary.FMin` maxHeat (+ (`self.Heat`) Amount)))
  (`self.RefreshHUD`)
  (if (and (>= (`self.Heat`) maxHeat) (not (`self.Busy`)))
    (`self.Sweep`)))

; Max Heat: the Imperial Sweep banner, then back to the checkpoint.
(event `Sweep`
  (set `self.Busy` true)
  (bind pc (`GameplayStatics.GetPlayerController` 0))
  (bind banner (`|CreateWidget` :`Class` "/Game/Splice/UI/WBP_Sweep.WBP_Sweep_C" :`OwningPlayer` pc))
  (`UserWidget.AddToViewport` :`self` banner)
  (`KismetSystemLibrary.Delay` (`/Game/Splice/Data/BP_Tuning.SweepBannerTime` (`self.Tuning`)))
  (`Widget.RemoveFromParent` banner)
  (`self.Respawn`)
  (set `self.Busy` false))

; A hit from a raider, an Imperial robot or the boss costs one heart. After a hit the
; player can't be hit again for RaiderHitCooldown seconds, so a crowd can't take every
; heart at once.
(event `DamagePlayer`
  (bind now (`GameplayStatics.GetTimeSeconds`))
  (if (or (`self.Busy`) (`self.MemoryPlaying`)
          (< (- now (`self.LastDamage`)) (`/Game/Splice/Data/BP_Tuning.RaiderHitCooldown` (`self.Tuning`))))
    (return))
  (set `self.LastDamage` now)
  (set `self.Hearts` (- (`self.Hearts`) 1))
  (`self.RefreshHUD`)
  (if (<= (`self.Hearts`) 0)
    (`self.TakeTwo`)
    (else
      (`self.ShowMessage` "Hit!  You lost a heart"))))

; Out of hearts: "CUT. TAKE TWO.", then back to the checkpoint.
(event `TakeTwo`
  (set `self.Busy` true)
  (bind pc (`GameplayStatics.GetPlayerController` 0))
  (bind banner (`|CreateWidget` :`Class` "/Game/Splice/UI/WBP_TakeTwo.WBP_TakeTwo_C" :`OwningPlayer` pc))
  (`UserWidget.AddToViewport` :`self` banner)
  (`KismetSystemLibrary.Delay` (`/Game/Splice/Data/BP_Tuning.SweepBannerTime` (`self.Tuning`)))
  (`Widget.RemoveFromParent` banner)
  (`self.Respawn`)
  (set `self.Busy` false))

; Back at the checkpoint with the inventory saved there. A banned piece picked up since
; then is lost and reappears in the level.
(event `Respawn`
  (set `self.Hearts` (`/Game/Splice/Data/BP_Tuning.MaxHearts` (`self.Tuning`)))
  (set `self.Heat` 0.0)
  (set `self.Inventory` (`self.SavedInventory`))
  (set `self.BannedCarried` (`self.BannedSaved`))
  ; Move the player first: a piece that reappears under the player would be picked
  ; straight back up.
  (bind point (`self.RespawnPoint`))
  (bind pawn (`GameplayStatics.GetPlayerPawn` 0))
  (if (and (`KismetSystemLibrary.IsValid` point) (`KismetSystemLibrary.IsValid` pawn))
    (`Actor.K2_TeleportTo` pawn (`Actor.K2_GetActorLocation` point) (`Actor.K2_GetActorRotation` point)))
  (for frag (`GameplayStatics.GetAllActorsOfClass` "/Game/Splice/Blueprints/BP_Fragment.BP_Fragment_C")
    (`/Game/Splice/Blueprints/BP_Fragment.OnRespawn` frag))
  (`self.RefreshHUD`))

; ---- Fighting

; F: stun a boss weak point if the boss is close, otherwise hit the first raider or
; Imperial robot in reach.
(event `Attack`
  (bind now (`GameplayStatics.GetTimeSeconds`))
  (bind tun (`self.Tuning`))
  (if (or (`self.Busy`) (`self.BayOpen`) (`self.MemoryPlaying`)
          (< (- now (`self.LastAttack`)) (`/Game/Splice/Data/BP_Tuning.AttackCooldown` tun)))
    (return))
  (set `self.LastAttack` now)
  (bind pawn (`GameplayStatics.GetPlayerPawn` 0))
  (bind reach (`/Game/Splice/Data/BP_Tuning.AttackRange` tun))
  (bind boss (`GameplayStatics.GetActorOfClass` "/Game/Splice/Blueprints/BP_Boss.BP_Boss_C"))
  (if (`KismetSystemLibrary.IsValid` boss)
    (if (< (`Actor.GetDistanceTo` pawn boss) 700.0)
      (`/Game/Splice/Blueprints/BP_Boss.TryStun` boss (`Actor.K2_GetActorLocation` pawn))
      (return)))
  ; One press hits one target. A loop keeps running after a hit, so a flag stops the rest.
  (set `self.HitDone` false)
  (for imp (`GameplayStatics.GetAllActorsOfClass` "/Game/Splice/Blueprints/BP_Imperial.BP_Imperial_C")
    (if (and (not (`self.HitDone`)) (< (`Actor.GetDistanceTo` pawn imp) reach))
      (set `self.HitDone` true)
      (`/Game/Splice/Blueprints/BP_Imperial.TakeHit` imp)))
  (for raider (`GameplayStatics.GetAllActorsOfClass` "/Game/Splice/Blueprints/BP_Raider.BP_Raider_C")
    (if (and (not (`self.HitDone`)) (< (`Actor.GetDistanceTo` pawn raider) reach))
      (set `self.HitDone` true)
      (`/Game/Splice/Blueprints/BP_Raider.TakeHit` raider))))

; Winning a fight adds a robot part to the inventory count, and raises Heat.
(event `NPCDefeated`
  (params (Drop :type String))
  (set `self.Parts` (+ (`self.Parts`) 1))
  (`self.AddHeat` (`/Game/Splice/Data/BP_Tuning.HeatPerFight` (`self.Tuning`)))
  (`self.ShowMessage` (`KismetStringLibrary.Concat_StrStr` "You won. Added to inventory: " Drop)))

; ---- Time of day and objective

; Phase: 0 dawn, 1 day, 2 dusk, 3 night.
(event `SetPhase`
  (params (Index :type Integer))
  (set `self.Phase` Index)
  (bind tod (`GameplayStatics.GetActorOfClass` "/Game/Splice/Blueprints/BP_TimeOfDay.BP_TimeOfDay_C"))
  (if (`KismetSystemLibrary.IsValid` tod)
    (`/Game/Splice/Blueprints/BP_TimeOfDay.Apply` tod Index))
  (`self.RefreshHUD`))

(event `SetObjective`
  (params (Text :type String))
  (set `self.Objective` Text)
  (`self.RefreshHUD`))

; ---- HUD

(event `RefreshHUD`
  (bind hud (`self.HUD`))
  (if (not (`KismetSystemLibrary.IsValid` hud))
    (return))
  (bind inv (`self.Inventory`))
  (bind cells (`self.Cells`))
  (bind parts (`self.Parts`))
  (`TextBlock.SetText` (`/Game/Splice/UI/WBP_HUD.CarryText` hud)
    (`KismetTextLibrary.Conv_StringToText`
      (`KismetStringLibrary.Concat_StrStr`
        (`KismetStringLibrary.Concat_StrStr`
          (`KismetStringLibrary.Concat_StrStr` "Carrying: "
            (select `bool` (== (`KismetArrayLibrary.Array_Length` inv) 0)
              :`true` "nothing"
              :`false` (`KismetStringLibrary.JoinStringArray` inv ", ")))
          (select `bool` (> cells 0)
            :`true` (`KismetStringLibrary.Concat_StrStr` "   ·   Battery cells: " (`KismetStringLibrary.Conv_IntToString` cells))
            :`false` ""))
        (select `bool` (> parts 0)
          :`true` (`KismetStringLibrary.Concat_StrStr` "   ·   Robot parts: " (`KismetStringLibrary.Conv_IntToString` parts))
          :`false` ""))))
  (`TextBlock.SetText` (`/Game/Splice/UI/WBP_HUD.PromptText` hud)
    (`KismetTextLibrary.Conv_StringToText`
      (select `bool` (and (or (`self.NearRover`) (`self.NearCrate`)) (not (`self.BayOpen`)) (not (`self.BotRunning`)))
        :`true` "[TAB] or [E]  ·  Open the edit bay"
        :`false` "")))
  ; Hearts: lost ones fade out.
  (bind hearts (`self.Hearts`))
  (`Widget.SetRenderOpacity` (`/Game/Splice/UI/WBP_HUD.Heart1` hud) (select `bool` (>= hearts 1) :`true` 1.0 :`false` 0.18))
  (`Widget.SetRenderOpacity` (`/Game/Splice/UI/WBP_HUD.Heart2` hud) (select `bool` (>= hearts 2) :`true` 1.0 :`false` 0.18))
  (`Widget.SetRenderOpacity` (`/Game/Splice/UI/WBP_HUD.Heart3` hud) (select `bool` (>= hearts 3) :`true` 1.0 :`false` 0.18))
  ; Heat meter: thirds are Cool, Warm, Wanted.
  (bind heat (`self.Heat`))
  (bind maxHeat (`/Game/Splice/Data/BP_Tuning.MaxHeat` (`self.Tuning`)))
  (bind heat01 (/ heat (`KismetMathLibrary.FMax` maxHeat 1.0)))
  (`ProgressBar.SetPercent` (`/Game/Splice/UI/WBP_HUD.HeatBar` hud) heat01)
  (`TextBlock.SetText` (`/Game/Splice/UI/WBP_HUD.HeatText` hud)
    (`KismetTextLibrary.Conv_StringToText`
      (`KismetStringLibrary.Concat_StrStr` "HEAT "
        (`KismetStringLibrary.Concat_StrStr` (`KismetStringLibrary.Conv_IntToString` (`KismetMathLibrary.Round` heat))
          (`KismetStringLibrary.Concat_StrStr` " / "
            (`KismetStringLibrary.Concat_StrStr` (`KismetStringLibrary.Conv_IntToString` (`KismetMathLibrary.Round` maxHeat))
              (select `bool` (< heat01 0.334)
                :`true` "  ·  COOL"
                :`false` (select `bool` (< heat01 0.667) :`true` "  ·  WARM" :`false` "  ·  WANTED"))))))))
  ; Phase chips: the current one is solid.
  (bind phase (`self.Phase`))
  (`Widget.SetRenderOpacity` (`/Game/Splice/UI/WBP_HUD.Phase0` hud) (select `bool` (== phase 0) :`true` 1.0 :`false` 0.45))
  (`Widget.SetRenderOpacity` (`/Game/Splice/UI/WBP_HUD.Phase1` hud) (select `bool` (== phase 1) :`true` 1.0 :`false` 0.45))
  (`Widget.SetRenderOpacity` (`/Game/Splice/UI/WBP_HUD.Phase2` hud) (select `bool` (== phase 2) :`true` 1.0 :`false` 0.45))
  (`Widget.SetRenderOpacity` (`/Game/Splice/UI/WBP_HUD.Phase3` hud) (select `bool` (== phase 3) :`true` 1.0 :`false` 0.45))
  (`TextBlock.SetText` (`/Game/Splice/UI/WBP_HUD.ObjectiveText` hud)
    (`KismetTextLibrary.Conv_StringToText` (`self.Objective`))))

(event `RefreshEditBay`
  (bind bay (`self.EditBay`))
  (if (not (`KismetSystemLibrary.IsValid` bay))
    (return))
  (bind inv (`self.Inventory`))
  (bind arm (`self.SlotArm`))
  (bind treads (`self.SlotTreads`))
  (bind battery (`self.SlotBattery`))
  (bind strip (`self.Strip`))
  (bind ready (and
    (`KismetSystemLibrary.IsValid` (`self.Bot`))
    (>= (`KismetArrayLibrary.Array_Length` strip) 2)))
  (`TextBlock.SetText` (`/Game/Splice/UI/WBP_EditBay.SlotsText` bay)
    (`KismetTextLibrary.Conv_StringToText`
      (`KismetStringLibrary.Concat_StrStr` "ARM: "
        (`KismetStringLibrary.Concat_StrStr` (select `bool` (`KismetStringLibrary.IsEmpty` arm) :`true` "-" :`false` arm)
          (`KismetStringLibrary.Concat_StrStr` "     TREADS: "
            (`KismetStringLibrary.Concat_StrStr` (select `bool` (`KismetStringLibrary.IsEmpty` treads) :`true` "-" :`false` treads)
              (`KismetStringLibrary.Concat_StrStr` "     BATTERY: "
                (select `bool` (`KismetStringLibrary.IsEmpty` battery) :`true` "-" :`false` battery))))))))
  (`TextBlock.SetText` (`/Game/Splice/UI/WBP_EditBay.StripText` bay)
    (`KismetTextLibrary.Conv_StringToText`
      (`KismetStringLibrary.Concat_StrStr` "FILM STRIP:  "
        (select `bool` (== (`KismetArrayLibrary.Array_Length` strip) 0)
          :`true` "(empty)  - click cards in the order the Digger should run them"
          :`false` (`KismetStringLibrary.JoinStringArray` strip "  ->  ")))))
  (`Widget.SetIsEnabled` (`/Game/Splice/UI/WBP_EditBay.BtnArm` bay) (`KismetArrayLibrary.Array_Contains` inv "Drill Arm"))
  (`Widget.SetIsEnabled` (`/Game/Splice/UI/WBP_EditBay.BtnTreads` bay) (`KismetArrayLibrary.Array_Contains` inv "Treads"))
  (`Widget.SetIsEnabled` (`/Game/Splice/UI/WBP_EditBay.BtnBattery` bay) (`KismetArrayLibrary.Array_Contains` inv "Battery"))
  (`Widget.SetIsEnabled` (`/Game/Splice/UI/WBP_EditBay.BtnMove` bay) (`KismetArrayLibrary.Array_Contains` inv "MOVE"))
  (`Widget.SetIsEnabled` (`/Game/Splice/UI/WBP_EditBay.BtnDrill` bay) (`KismetArrayLibrary.Array_Contains` inv "DRILL"))
  (`Widget.SetIsEnabled` (`/Game/Splice/UI/WBP_EditBay.BtnDrillPlus` bay) (`KismetArrayLibrary.Array_Contains` inv "DRILL+"))
  (`Widget.SetIsEnabled` (`/Game/Splice/UI/WBP_EditBay.BtnSpliceCore` bay) (`KismetArrayLibrary.Array_Contains` inv "Banned core"))
  (`Widget.SetIsEnabled` (`/Game/Splice/UI/WBP_EditBay.BtnDeploy` bay) ready)
  (`TextBlock.SetText` (`/Game/Splice/UI/WBP_EditBay.StatusText` bay)
    (`KismetTextLibrary.Conv_StringToText`
      (select `bool` ready
        :`true` "Ready. Press DEPLOY."
        :`false` (select `bool` (`KismetSystemLibrary.IsValid` (`self.Bot`))
          :`true` "Put at least 2 cards on the strip."
          :`false` "Fill ARM, TREADS and BATTERY to wake the Digger.")))))

; ---- The memory ending

; Splicing the banned core plays the memory: the camera cuts to the old-world diorama
; and three caption lines play. Click to skip. Then SCENE RESTORED.
(event `SpliceCore`
  (if (not (`KismetArrayLibrary.Array_Contains` (`self.Inventory`) "Banned core"))
    (return))
  (`self.CloseEditBay`)
  (set `self.MemoryPlaying` true)
  (`self.SetPhase` 3)
  (bind pc (`GameplayStatics.GetPlayerController` 0))
  (bind cam (`self.MemoryCam`))
  (if (`KismetSystemLibrary.IsValid` cam)
    (set `/Game/Splice/Blueprints/BP_MemoryCam.Active` :`self` cam :`Active` true)
    (`PlayerController.SetViewTargetWithBlend` :`self` pc :`NewViewTarget` cam :`BlendTime` 1.0))
  (`Widget.SetVisibility` (`self.HUD`) "Collapsed")
  (bind mem (`|CreateWidget` :`Class` "/Game/Splice/UI/WBP_Memory.WBP_Memory_C" :`OwningPlayer` pc))
  (set `self.MemoryWidget` mem)
  (`UserWidget.AddToViewport` :`self` mem)
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_Memory.BtnSkip` mem) (`|CreateDelegate` :!event `EndMemory`))
  (set `PlayerController.bShowMouseCursor` :`self` pc :`bShowMouseCursor` true)
  (`WidgetBlueprintLibrary.SetInputMode_GameAndUIEx` :`PlayerController` pc)
  (bind hold (`/Game/Splice/Data/BP_Tuning.MemoryCaptionTime` (`self.Tuning`)))
  (`self.ShowCaption` 0)
  (`KismetSystemLibrary.Delay` hold)
  (`self.ShowCaption` 1)
  (`KismetSystemLibrary.Delay` hold)
  (`self.ShowCaption` 2)
  (`KismetSystemLibrary.Delay` hold)
  (`self.EndMemory`))

(event `ShowCaption`
  (params (Index :type Integer))
  (bind mem (`self.MemoryWidget`))
  (bind lines (`self.MemoryCaptions`))
  (if (and (`self.MemoryPlaying`) (`KismetSystemLibrary.IsValid` mem) (< Index (`KismetArrayLibrary.Array_Length` lines)))
    (`TextBlock.SetText` (`/Game/Splice/UI/WBP_Memory.Caption` mem)
      (`KismetTextLibrary.Conv_StringToText` (`KismetArrayLibrary.Array_Get` lines Index)))))

(event `EndMemory`
  (if (not (`self.MemoryPlaying`))
    (return))
  (set `self.MemoryPlaying` false)
  (bind mem (`self.MemoryWidget`))
  (if (`KismetSystemLibrary.IsValid` mem)
    (`Widget.RemoveFromParent` mem))
  (`self.ShowEnd`))

(event `ShowEnd`
  (bind pc (`GameplayStatics.GetPlayerController` 0))
  (bind endw (`|CreateWidget` :`Class` "/Game/Splice/UI/WBP_End.WBP_End_C" :`OwningPlayer` pc))
  (set `self.EndScreen` endw)
  (`UserWidget.AddToViewport` :`self` endw)
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_End.BtnRestart` endw) (`|CreateDelegate` :!event `ClickRestart`))
  (set `PlayerController.bShowMouseCursor` :`self` pc :`bShowMouseCursor` true)
  (`WidgetBlueprintLibrary.SetInputMode_UIOnlyEx` :`PlayerController` pc))

(event `ClickRestart`
  (`GameplayStatics.OpenLevel` :`LevelName` "L_Mine"))

; Test aids for the browser test, called from the console ("ke * DebugTeleport 4300 0 100").
; Console commands are off in Shipping builds.
(event `DebugTeleport`
  (params (X :type "Float (double-precision)") (Y :type "Float (double-precision)") (Z :type "Float (double-precision)"))
  (bind pawn (`GameplayStatics.GetPlayerPawn` 0))
  (`Actor.K2_TeleportTo` pawn (`KismetMathLibrary.MakeVector` X Y Z) (`Actor.K2_GetActorRotation` pawn)))

; Point the camera: yaw and pitch in degrees. The test page captures the mouse, so the
; camera drifts with the real mouse unless the test sets it just before a screenshot.
(event `DebugLook`
  (params (Yaw :type "Float (double-precision)") (Pitch :type "Float (double-precision)"))
  (`Controller.SetControlRotation` (`GameplayStatics.GetPlayerController` 0)
    (`KismetMathLibrary.MakeRotator` 0.0 Pitch Yaw)))
