; The camera for the memory scene. While Active it dollies slowly along +X.
(event `self.ReceiveTick`
  (params (DeltaSeconds))
  (if (`self.Active`)
    (`self.K2_AddActorWorldOffset` :`DeltaLocation`
      (`KismetMathLibrary.MakeVector` (* (`self.Speed`) DeltaSeconds) 0.0 0.0))))
