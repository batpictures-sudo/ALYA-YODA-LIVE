#!/usr/bin/env python3
"""Patch only the Android experiment, leaving the existing Windows/Szuhay systems intact."""
from pathlib import Path
import re

root = Path("android-one-icon/app/src/main")

def edit(path, old, new):
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Expected exactly one anchor in {path}: {old[:70]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")

manifest = root / "AndroidManifest.xml"
edit(manifest, '<application android:label="Alya–Yoda"', '<application android:icon="@drawable/alya_yoda_icon" android:label="Alya–Yoda"')

drawable = root / "res/drawable"
drawable.mkdir(parents=True, exist_ok=True)
(drawable / "alya_yoda_icon.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#0B211A" android:pathData="M0,0 L108,0 L108,108 L0,108 Z"/>
    <path android:fillColor="#B8DD8C" android:pathData="M54,9 A45,45 0,1 1,54 99 A45,45 0,1 1,54 9 Z"/>
    <path android:fillColor="#123323" android:pathData="M27,28 L45,28 L54,49 L63,28 L81,28 L62,62 L62,82 L46,82 L46,62 Z"/>
</vector>
""", encoding="utf-8")

java = root / "java/hu/alya/yoda/MainActivity.java"
edit(java, 'import android.content.pm.PackageManager;',
    'import android.content.pm.PackageManager;\nimport android.content.pm.ShortcutManager;\nimport android.content.pm.ShortcutInfo;\nimport android.graphics.drawable.Icon;\nimport android.os.Build;')
edit(java, '        setContentView(layout);',
    '        setContentView(layout);\n        offerHomeShortcutOnce();')
pin = """
    /**
     * An app cannot silently add an item to the Android home screen.
     * Request a one-time launcher-confirmed home shortcut when supported.
     * The regular LAUNCHER app icon is always available in the app drawer.
     */
    private void offerHomeShortcutOnce() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return;
        ShortcutManager manager = getSystemService(ShortcutManager.class);
        if (manager == null || !manager.isRequestPinShortcutSupported()) return;
        for (ShortcutInfo item : manager.getPinnedShortcuts()) {
            if ("alya-yoda-home".equals(item.getId())) return;
        }
        if (getPreferences(MODE_PRIVATE).getBoolean("pin_requested_v2", false)) return;
        Intent open = new Intent(this, MainActivity.class);
        open.setAction(Intent.ACTION_MAIN);
        open.addCategory(Intent.CATEGORY_LAUNCHER);
        open.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        ShortcutInfo info = new ShortcutInfo.Builder(this, "alya-yoda-home")
            .setShortLabel("Alya–Yoda")
            .setLongLabel("Alya–Yoda indítása")
            .setIcon(Icon.createWithResource(this, R.drawable.alya_yoda_icon))
            .setIntent(open)
            .build();
        boolean requested = manager.requestPinShortcut(info, null);
        if (requested) getPreferences(MODE_PRIVATE).edit().putBoolean("pin_requested_v2", true).apply();
    }

"""
edit(java, '    @Override protected void onPause(){', pin + '    @Override protected void onPause(){')

page = root / "assets/yodabridge/page.js"
src = page.read_text(encoding="utf-8")
pattern = re.compile(r"    root\.style\.cssText=.*?;\n    btn=document\.createElement\('button'\);", re.S)
replacement = """    root.style.cssText='position:fixed;z-index:2147483646;inset:0;'
      +'background:linear-gradient(160deg,#10281d,#06150f);'
      +'display:flex;flex-direction:column;justify-content:center;'
      +'align-items:center;gap:15px;padding:28px;box-sizing:border-box;'
      +'color:white;font:18px system-ui;overflow:auto;text-align:center;';
    btn=document.createElement('button');"""
src, n = pattern.subn(lambda m: replacement, src)
if n != 1:
    raise RuntimeError(f"Missing overlay CSS anchor: {n}")
old = "    root.append(btn,note);document.body.append(root);"
new = """    const heading=document.createElement('div');
    heading.textContent='ALYA · YODA';
    heading.style.cssText='font:bold 36px system-ui;color:#c6e89b;letter-spacing:2px';
    const description=document.createElement('div');
    description.textContent='Egy érintéses Yoda-híd · a valódi ChatGPT válaszával';
    description.style.cssText='font:16px system-ui;max-width:540px;line-height:1.5';
    const setup=document.createElement('button');
    setup.textContent='ChatGPT kapcsolat ellenőrzése (egyszeri beállítás)';
    setup.style.cssText='margin-top:22px;min-height:48px;background:transparent;'
      +'color:#b8dd8c;border:1px solid #688b5f;border-radius:9px;padding:8px 16px;font:15px system-ui';
    const back=document.createElement('button');
    back.textContent='Vissza az Alya–Yodához';
    back.style.cssText='display:none;position:fixed;z-index:2147483647;'
      +'right:12px;bottom:12px;background:#b8dd8c;color:#132a20;border:0;'
      +'border-radius:12px;padding:15px;font:bold 16px system-ui';
    setup.addEventListener('click',()=>{root.style.display='none';back.style.display='block';});
    back.addEventListener('click',()=>{root.style.display='flex';back.style.display='none';});
    root.append(heading,description,btn,note,setup);
    document.body.append(root,back);"""
if src.count(old)!=1: raise RuntimeError("Missing overlay insertion anchor")
src=src.replace(old,new)
old="    paired=!!e.data.paired;\n    label(paired?'Alya–Yoda kész. Egy érintés az indításhoz.':'Az egyszeri párosítólink hiányzik.');"
new="""    paired=!!e.data.paired;
    label(paired?'Alya–Yoda: Szuhay-híd elérhető.':'A Szuhay-híd biztonságos egyszeri párosítása még hiányzik.');"""
if src.count(old)!=1: raise RuntimeError("Pairing anchor mismatch")
src=src.replace(old,new)
# Cold-start attempts to activate the already-authorized session, without opening ChatGPT Voice.
# An AudioContext may require a user gesture: preserve the large manual Start button as fallback.
old="  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',overlay,{once:true});else overlay();"
new="""  let automaticStartAttempted=false;
  setInterval(()=>{
    if(!automaticStartAttempted && !running && paired && composer()){
      automaticStartAttempted=true;
      void begin();
    }
  },1500);
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',overlay,{once:true});else overlay();"""
if src.count(old)!=1: raise RuntimeError("Startup anchor mismatch")
src=src.replace(old,new)
page.write_text(src, encoding="utf-8")
print("ALYA-YODA UI/launcher patch applied successfully; auth/pairing security remains intact.")
