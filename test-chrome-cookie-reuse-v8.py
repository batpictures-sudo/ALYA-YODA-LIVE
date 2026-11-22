#!/usr/bin/env python3
"""Chrome Custom Tab feasibility probe on isolated experiment branch.

Important: CCT reuses Chrome cookies on the same Android profile, but app
cannot read CCT DOM/cookies/audio through CCT APIs. Never use this as a
replacement for an unverified ChatGPT -> Szuhay sound bridge.
"""
from pathlib import Path
base=Path("android-one-icon")
app=base/"app"
build=app/"build.gradle"
source=build.read_text(encoding="utf-8")
anchor="  implementation 'org.mozilla.geckoview:geckoview:143.0.20251003115653'\n"
assert source.count(anchor)==1, "Android Gecko dependency unexpected"
build.write_text(source.replace(anchor,anchor+"  implementation 'androidx.browser:browser:1.8.0'\n"),encoding="utf-8")

java=app/"src/main/java/hu/alya/yoda/MainActivity.java"
source=java.read_text(encoding="utf-8")
anchor="import android.content.Intent;\n"
assert source.count(anchor)==1
source=source.replace(anchor,anchor+"import android.content.ActivityNotFoundException;\nimport androidx.browser.customtabs.CustomTabsIntent;\n")
anchor='        if ("pairStatus".equals(type)) return GeckoResult.fromValue(reply("paired",paired()));'
assert source.count(anchor)==1
source=source.replace(anchor,'''        if ("openChromeSession".equals(type)) {
            runOnUiThread(()->openChromeSessionProbe());
            return GeckoResult.fromValue(reply("requested",true));
        }
'''+anchor)
anchor="    private JSONObject reply(String key,Object value){"
assert source.count(anchor)==1
method='''    /**
     * Proof of the Chrome shared-login path ONLY.
     * Never reads or exports a browser credential or cookie.
     * There is no CCT DOM or audio interception here.
     */
    private void openChromeSessionProbe() {
        try {
            CustomTabsIntent tab = new CustomTabsIntent.Builder().setShowTitle(true).build();
            // Do not select an ephemeral tab. Use the SAME Chrome profile where
            // Karesz has already signed into chatgpt.com.
            tab.intent.setPackage("com.android.chrome");
            tab.launchUrl(this,Uri.parse(HOME));
        } catch(ActivityNotFoundException ex) {
            message.setVisibility(android.view.View.VISIBLE);
            message.setText("A Chrome nem nyitható meg a tableten.");
        } catch(Exception ex) {
            message.setVisibility(android.view.View.VISIBLE);
            message.setText("A Chrome-bejelentkezés próbája nem indult.");
            Log.w(TAG,"Chrome shared-session probe failed",ex);
        }
    }

'''
source=source.replace(anchor,method+anchor)
java.write_text(source,encoding="utf-8")

bridge=app/"src/main/assets/yodabridge/bridge.js"
source=bridge.read_text(encoding="utf-8")
anchor="const allowed=['listenStart','listenStop','readAloudComplete','submitFailure'];"
assert source.count(anchor)==1
source=source.replace(anchor,"const allowed=['listenStart','listenStop','readAloudComplete','submitFailure','openChromeSession'];")
bridge.write_text(source,encoding="utf-8")

page=app/"src/main/assets/yodabridge/page.js"
source=page.read_text(encoding="utf-8")
anchor="    root.append(heading,description,btn,note,setup);"
assert source.count(anchor)==1
new='''    const chromeProbe=document.createElement('button');
    chromeProbe.textContent='Chrome-fiók ellenőrzése (külön teszt)';
    chromeProbe.style.cssText='min-height:48px;background:transparent;color:#d2e7c0;'
      +'border:1px solid #70836d;border-radius:9px;padding:10px 15px;font:15px system-ui';
    chromeProbe.addEventListener('click',()=>{
      // Login proof ONLY; do not claim this has activated Yoda audio capture.
      label('Megnyitom a Chrome meglévő ChatGPT-bejelentkezését. A hanghíd itt még NEM aktív.');
      nativeCommand('openChromeSession');
    });
    root.append(heading,description,btn,note,setup,chromeProbe);'''
source=source.replace(anchor,new)
page.write_text(source,encoding="utf-8")

test=base/"test_project.py"
test.write_text(test.read_text(encoding="utf-8")+'''
assert "'androidx.browser:browser:1.8.0'" in (base/'app/build.gradle').read_text()
java=(base/'app/src/main/java/hu/alya/yoda/MainActivity.java').read_text()
assert 'new CustomTabsIntent.Builder()' in java
assert 'setPackage("com.android.chrome")' in java
assert 'openChromeSessionProbe' in java
assert 'openChromeSession' in (base/'app/src/main/assets/yodabridge/bridge.js').read_text()
assert 'Chrome-fiók ellenőrzése (külön teszt)' in (base/'app/src/main/assets/yodabridge/page.js').read_text()
''',encoding="utf-8")
print("PASS: Chrome Custom Tabs shared-session probe ready (NO audio integration claimed)")
