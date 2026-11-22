#!/usr/bin/env python3
"""V13 one-icon install: build-time pairing placeholder (replace OFF GitHub)
and automatic voice standby after login. NO user token in public source.

The compiled placeholder MUST be replaced in local/private APK packaging,
DEX checksums and APK signature updated before delivering to the user.
Do not distribute an APK that still contains PREINSTALLED_PAIR placeholder.
"""
from pathlib import Path
base=Path("android-one-icon")
p=base/"app/src/main/java/hu/alya/yoda/MainActivity.java"
s=p.read_text(encoding="utf-8")
def once(old,new,why):
 global s
 if s.count(old)!=1:raise RuntimeError("V13 "+why+f" anchor count: {s.count(old)}")
 s=s.replace(old,new)
once('    private static final String TAG="AlyaYoda";\n',
'''    private static final String TAG="AlyaYoda";
    // Placeholder is replaced ONLY during offline/private final APK packaging.
    // Keep the real Szuhay token OUT of the publicly readable Git repository.
    private static final String PREINSTALLED_PAIR="ALYA_YODA_PAIR_TOKEN_REPLACE_WITH_PRIVATE_VALUE_";
''',"placeholder")
once('        initialPairStatus=acceptPairLink(getIntent());\n',
'''        // A fresh installation is paired before ChatGPT's GeckoView starts.
        // No pairing links, browser sharing, or manual secret entry are needed.
        if(!getPreferences(MODE_PRIVATE).getString("pair","")
                .matches("[A-Za-z0-9_-]{24,128}")) {
            if(PREINSTALLED_PAIR.matches("[A-Za-z0-9_-]{24,128}"))
                getPreferences(MODE_PRIVATE).edit()
                    .putString("pair",PREINSTALLED_PAIR).commit();
        }
        initialPairStatus=acceptPairLink(getIntent());
''',"initial pairing")
p.write_text(s,encoding="utf-8")
page=base/"app/src/main/assets/yodabridge/page.js"
js=page.read_text(encoding="utf-8")
anchor='  let controlId=0;\n'
assert js.count(anchor)==1
js=js.replace(anchor,anchor+'''  let autoStartAttempted=false;
  let lastAutoStartCheck=0;
''')
anchor='''  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',overlay,{once:true});else overlay();
'''
assert js.count(anchor)==1
js=js.replace(anchor,'''  // One home-screen icon is enough after the one-time ChatGPT login.
  // Auto-arm YODA wake listening as soon as chatgpt.com has a usable composer.
  // Never auto-open login flows; show the built-in ChatGPT login unchanged.
  setInterval(()=>{
    if(autoStartAttempted || !paired || running || !btn || !composer())return;
    autoStartAttempted=true;
    void begin();
  },1600);
'''+anchor)
page.write_text(js,encoding="utf-8")
gradle=base/"app/build.gradle"
g=gradle.read_text(encoding="utf-8")
assert "versionCode 2" in g and "versionName '0.2.0'" in g
g=g.replace("versionCode 2","versionCode 13").replace("versionName '0.2.0'","versionName '1.0.0'")
gradle.write_text(g,encoding="utf-8")
tests=base/"test_project.py"
tests.write_text(tests.read_text(encoding="utf-8")+'''
v13=(base/'app/src/main/java/hu/alya/yoda/MainActivity.java').read_text()
assert v13.count('ALYA_YODA_PAIR_TOKEN_REPLACE_WITH_PRIVATE_VALUE_')==1
assert '.putString("pair",PREINSTALLED_PAIR).commit();' in v13
assert v13.index('.putString("pair",PREINSTALLED_PAIR).commit();')<v13.index('initialPairStatus=acceptPairLink(getIntent());')
v13js=(base/'app/src/main/assets/yodabridge/page.js').read_text()
assert 'autoStartAttempted=true;' in v13js and 'void begin();' in v13js
assert '|| !btn || !composer()' in v13js
assert 'chip.id=\\'alya-yoda-chip\\'' in v13js
assert 'versionCode 13' in (base/'app/build.gradle').read_text()
''',encoding="utf-8")
print("PASS V13: private packaging placeholder, no manual pairing, one-icon auto-start")
