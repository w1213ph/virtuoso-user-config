; Load this in a dedicated NEW test session after the installed profile.
; Checks loaded parameters only; it does not prove GUI behavior.
vucVerificationFailures=0
procedure(vucAssert(actual expected label)
 if(equal(actual expected) then
  printf("PASS %s\n" label)
 else
  printf("FAIL %s actual=%L expected=%L\n" label actual expected)
  vucVerificationFailures=vucVerificationFailures+1
 )
)
vucAssert(boundp('vucLoaded) && vucLoaded t "profile loaded")
printf("CIW_FONT=%L\n" hiGetFontInfo("ciw"))
printf("LABEL_FONT=%L\n" hiGetFontInfo("label"))
printf("TEXT_FONT=%L\n" hiGetFontInfo("text"))
printf("QT_SCALE_FACTOR=%L\n" getShellEnvVar("QT_SCALE_FACTOR"))
