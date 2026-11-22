#!/usr/bin/env python3
"""Android V6: fail safely when native recognition or remote audio fails.

Only the genuine ChatGPT Read Aloud audio is eligible for Szuhay conversion.
Do not forward audio from unrelated UI activity. Do not pretend Yoda is armed if
the native recognizer is unavailable or the mic permission was denied.
"""
from pathlib import Path

base = Path("android-one-icon")
page = base / "app/src/main/assets/yodabridge/page.js"
native = base / "app/src/main/java/hu/alya/yoda/MainActivity.java"
voice = base / "app/src/main/java/hu/alya/yoda/VoiceCommands.java"

src = page.read_text(encoding="utf-8")

def rep(old,new,name):
    global src
    n=src.count(old)
    if n!=1: raise RuntimeError(f"V6 {name} expected one anchor, got {n}")
    src=src.replace(old,new)

rep(
"  let waitingAnswer=false, readingStarted=false, playedParts=0;",
"  let waitingAnswer=false, readingStarted=false, playedParts=0, readStartedAt=0;",
"Read Aloud timer")
rep("  function inspect(samples){\n    // Only original ChatGPT playback is tapped, never the audience microphone.",
"""  function inspect(samples){
    // Never transmit audio from sign-in, browsing, idle wake-word standby or
    // ambient sounds. Only our own READ ALOUD request may be converted.
    if(!running || !waitingAnswer || !autoReadAttempted) return;
    // Only original ChatGPT playback is tapped, never the audience microphone.""",
"audio conversion gate")
rep("""    if(queue.length>=maxQueue){label('A beszéd túl hosszú, a hanghíd megtelt.');return;}""",
"""    if(queue.length>=maxQueue){
      stopWithError('A Szuhay-híd nem győzi a beszédet, hangszakasz maradt ki.');
      return;
    }""",
"queue exhaustion")
rep("""    }catch(e){label('Hanghídhiba: '+e.message);console.warn('[ALYA–YODA]',e);}
    finally{processing=false;if(queue.length&&running)void pump();}""",
"""    }catch(e){
      console.warn('[ALYA–YODA] audio conversion/playback failure',e);
      stopWithError('A Szuhay-hangút megszakadt: '+e.message);
    }finally{processing=false;if(queue.length&&running)void pump();}""",
"RVC error recovery")

# Keep a shared fail-closed helper close to the existing UI status function.
rep("  function label(s){if(note)note.textContent=s;}",
"""  function label(s){if(note)note.textContent=s;}
  function stopWithError(reason){
    // Stop listening on bridge failure; do not re-arm the room microphone
    // while unknown/original audio may still be playing.
    running=false;
    waitingAnswer=false;readingStarted=false;
    buffer=[];pre=[];queue=[];gotVoice=false;length=0;readStartedAt=0;
    if(btn){btn.textContent='YODA INDÍTÁSA';btn.disabled=false;}
    nativeCommand('listenStop',reason);
    label(reason);
  }""",
"fail-closed helper")
rep("""      currentAnswer=null;autoReadAttempted=false;moreMenuAttempted=false;answerChangedAt=Date.now();""",
"""      currentAnswer=null;autoReadAttempted=false;moreMenuAttempted=false;answerChangedAt=Date.now();
      // No PCM from a previous answer may contaminate the next question.
      buffer=[];pre=[];queue=[];gotVoice=false;length=0;
      lastVoiceAt=0;readStartedAt=0;playedParts=0;""",
"reset at next answer")
rep("""        autoReadAttempted=true;button.click();
        label('A ChatGPT eredeti felolvasását indítottam…');""",
"""        autoReadAttempted=true;
        readStartedAt=Date.now();
        button.click();
        label('A ChatGPT eredeti felolvasását indítottam…');""",
"read aloud start")
rep("""    // Do NOT reopen question recognition during audio playback or in short pauses.
    if(readingStarted&&playedParts>0""",
"""    // A changed DOM or an inaccessible audio stream must not leave an
    // unattended puppet waiting forever or accidentally playing raw audio.
    if(autoReadAttempted && readStartedAt>0 && !readingStarted &&
       Date.now()-readStartedAt>30000){
      stopWithError('A ChatGPT Felolvasás indult, de a hangot nem sikerült biztonságosan átvenni.');
      return;
    }
    // Do NOT reopen question recognition during audio playback or in short pauses.
    if(readingStarted&&playedParts>0""",
"timeout for no captured audio")
rep("""    if(e.source!==window||e.origin!==location.origin||e.data?.type!==nativeEvents)return;
    for(const item of e.data.events||[]){""",
"""    if(e.source!==window||e.origin!==location.origin||e.data?.type!==nativeEvents)return;
    if(e.data.state==='OFF' && running){
      stopWithError('A tableten nem működik a hívószófigyelés. Ellenőrizd a mikrofonengedélyt.');
      return;
    }
    for(const item of e.data.events||[]){""",
"native recognizer state")
page.write_text(src,encoding="utf-8")

s=voice.read_text(encoding="utf-8")
old='    void stop(){\n'
if s.count(old)!=1:raise RuntimeError("V6 voice stop anchor")
s=s.replace(old,"""    void permissionDenied(){
        event("error","A mikrofonengedély hiányzik, Yoda nem figyel.");
        stop();
    }
    void stop(){
""")
voice.write_text(s,encoding="utf-8")
s=native.read_text(encoding="utf-8")
old='            else Log.w(TAG,"A mikrofonengedélyt nem adták meg; hívószó nem figyelhető.");'
if s.count(old)!=1:raise RuntimeError("V6 native permission anchor")
s=s.replace(old,'            else speech.permissionDenied();')
native.write_text(s,encoding="utf-8")

# Structural invariants complement Node syntax and Java compilation.
tests=base/"test_project.py"
tests.write_text(tests.read_text(encoding="utf-8")+"""
v6=(base/'app/src/main/assets/yodabridge/page.js').read_text()
assert 'if(!running || !waitingAnswer || !autoReadAttempted) return;' in v6
assert 'if(e.data.state===\\'OFF\\' && running)' in v6
assert 'stopWithError(\\'A Szuhay-hangút megszakadt:' in v6
assert 'Date.now()-readStartedAt>30000' in v6
assert 'speech.permissionDenied();' in (base/'app/src/main/java/hu/alya/yoda/MainActivity.java').read_text()
assert 'void permissionDenied(){' in (base/'app/src/main/java/hu/alya/yoda/VoiceCommands.java').read_text()
""",encoding="utf-8")
print("V6 conversion safety, native state and microphone recovery tests prepared")
