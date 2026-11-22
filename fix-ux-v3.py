#!/usr/bin/env python3
"""V3 UX/runtime guards for the experimental Android build.

Only patches unpacked Android app; never edits the production Windows bridge,
Unikraft engine, or Vercel infrastructure.
"""
from pathlib import Path
root = Path("android-one-icon")
page = root / "app/src/main/assets/yodabridge/page.js"
source = page.read_text(encoding="utf-8")

def replace_once(old,new,tag):
    global source
    n = source.count(old)
    if n != 1: raise RuntimeError(f"{tag}: anchor count = {n}")
    source = source.replace(old,new)

replace_once("  function label(s){if(note)note.textContent=s;}",
"""  function label(s){if(note)note.textContent=s;}

  // In a private GeckoView profile the Chrome login is NOT shared.
  // A chat prompt visible to guests is not proof of account authentication.
  function loginRequired(){
    const re=/^(?:bejelentkezés|bejelentkezem|regisztráció ingyenesen|regisztráció|log in|sign up|sign in|continue with google)$/i;
    return [...document.querySelectorAll('a,button,[role="button"]')]
      .some(n=>re.test((n.textContent||'').trim()) || re.test((n.getAttribute('aria-label')||'').trim()));
  }
  function chatReady(){return !!composer()&&!loginRequired();}
""","login detector")
replace_once("""    if(!paired){label('Először az egyszeri párosítás szükséges.');return;}
    if(!composer()){
      label('Előbb a ChatGPT-be kell bejelentkezni ugyanebben az alkalmazásban.');return;
    }""",
"""    if(!paired){
      label('A Szuhay-híd biztonságos párosítása hiányzik. Nem indítom el hibásan.');
      return;
    }
    if(!chatReady()){
      label('A ChatGPT-fiók ebben az alkalmazásban még nem elérhető. Az egyérintéses működés nincs kész.');
      return;
    }""","startup checks")
replace_once("""      ctx=new (window.AudioContext||window.webkitAudioContext)({sampleRate:rate,latencyHint:'interactive'});
      await ctx.resume();running=true;
      btn.textContent='YODA FIGYEL';btn.disabled=true;""",
"""      ctx=new (window.AudioContext||window.webkitAudioContext)({sampleRate:rate,latencyHint:'interactive'});
      // A WebAudio unlock may require a real user gesture on Android.
      // Never hang forever silently after the app icon was tapped.
      const resumed=await Promise.race([
        ctx.resume().then(()=>true,()=>false),
        new Promise(resolve=>setTimeout(()=>resolve(false),3500))
      ]);
      if(!resumed || ctx.state!=='running'){
        try{void ctx.close().catch(()=>{});}catch(e){}
        ctx=null;
        throw Error('Az Android nem engedte automatikusan indítani a hangot. Érintsd meg a YODA INDÍTÁSA gombot.');
      }
      running=true;
      btn.textContent='YODA FIGYEL';btn.disabled=true;""","audio unlock")
replace_once("""    }catch(e){running=false;label('Nem indul a hang: '+e.message);}""",
"""    }catch(e){
      running=false;
      btn.textContent='YODA INDÍTÁSA';btn.disabled=false;
      label('Nem indult el: '+e.message);
    }""","audio error feedback")
replace_once("""        label('A ChatGPT Felolvasás gombja nem található. A kérdés nem lett eldobva.');
        autoReadAttempted=true;
        // Do not invent a replacement voice or prematurely reopen the microphone.""",
"""        label('A ChatGPT Felolvasás gombja nem található. A kérdés elküldve, hang nincs.');
        autoReadAttempted=true;
        waitingAnswer=false;
        nativeCommand('submitFailure','A ChatGPT Felolvasás gombja nem elérhető.');""","read aloud recovery")
replace_once("""    label(paired?'Alya–Yoda: Szuhay-híd elérhető.':'A Szuhay-híd biztonságos egyszeri párosítása még hiányzik.');""",
"""    label(paired?'A Szuhay párosítóadata rögzítve (szerverkapcsolat még nem tesztelt).':
      'A Szuhay-híd biztonságos egyszeri párosítása még hiányzik.');""","pair display truthfulness")
replace_once("""    if(!automaticStartAttempted && !running && paired && composer()){""",
"""    if(!automaticStartAttempted && !running && paired && chatReady()){""","autostart account readiness")
page.write_text(source,encoding="utf-8")

# Keep the same Activity on repeated launcher and deeplink open.
manifest = root / "app/src/main/AndroidManifest.xml"
m = manifest.read_text(encoding="utf-8")
anchor='android:name=".MainActivity" android:exported="true"'
if m.count(anchor)!=1: raise RuntimeError("MainActivity manifest anchor missing")
manifest.write_text(m.replace(anchor,anchor+' android:launchMode="singleTask"'),encoding="utf-8")

# Explicitly test that this experiment has a visible native app launcher.
spec = root / "test_project.py"
checks = '''
assert 'android.intent.category.LAUNCHER' in (base/'app/src/main/AndroidManifest.xml').read_text()
assert 'android:icon="@drawable/alya_yoda_icon"' in (base/'app/src/main/AndroidManifest.xml').read_text()
assert (base/'app/src/main/res/drawable/alya_yoda_icon.xml').exists()
assert 'loginRequired()' in js
assert 'A Szuhay-híd biztonságos párosítása hiányzik' in js
assert 'setTimeout(()=>resolve(false),3500)' in js
'''
spec.write_text(spec.read_text(encoding="utf-8")+checks,encoding="utf-8")
print("V3 startup, account and sound guards OK")
