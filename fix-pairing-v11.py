#!/usr/bin/env python3
"""V11: true native pairing diagnostics + live state refresh for the EXISTING
GeckoView Yoda architecture. Does not embed pairing key in APK and does
not modify the cloud voice model, signer or production Windows bridge.
"""
from pathlib import Path
base=Path("android-one-icon")
p=base/"app/src/main/java/hu/alya/yoda/MainActivity.java"
s=p.read_text(encoding="utf-8")
def rep(old,new,name):
    global s
    n=s.count(old)
    if n!=1:raise RuntimeError(f"V11 {name}: expected 1 anchor, found {n}")
    s=s.replace(old,new)
rep("import android.widget.TextView;\n", "import android.widget.TextView;\nimport android.widget.Toast;\n", "Toast import")
rep("    private boolean startRecognitionAfterPermission = false;\n",
"""    private boolean startRecognitionAfterPermission = false;
    private String initialPairStatus = "";
    private void showPairStatus(String status) {
        // Explicit feedback survives the ChatGPT overlay and does not reveal
        // the token. Always visible for 9 seconds at the very TOP of the view.
        if(message!=null){
            message.setText("ALYA–YODA: "+status);
            message.setVisibility(android.view.View.VISIBLE);
            message.removeCallbacks(hidePairMessage);
            message.postDelayed(hidePairMessage,9000);
        }
        Toast.makeText(this,status,Toast.LENGTH_LONG).show();
        Log.i(TAG,"pairStatus: "+status);
    }
    private final Runnable hidePairMessage=()->{
        if(message!=null)message.setVisibility(android.view.View.GONE);
    };
""", "native visible pairing feedback")
rep("        acceptPairLink(getIntent());\n", "        initialPairStatus=acceptPairLink(getIntent());\n", "initial link state")
rep("        setContentView(layout);\n", """        setContentView(layout);
        if(!initialPairStatus.isEmpty())showPairStatus(initialPairStatus);
""", "startup status")
rep("""        message.postDelayed(()->message.setVisibility(android.view.View.GONE),10000);""",
"""        if(initialPairStatus.isEmpty())message.postDelayed(hidePairMessage,10000);""",
"do not overwrite pairing status")
rep("""    private void acceptPairLink(Intent i){
        Uri u=i==null?null:i.getData();
        if(u!=null && "alyayoda".equals(u.getScheme()) && "pair".equals(u.getHost())) {
            String candidate=u.getLastPathSegment();
            if(candidate!=null && candidate.matches("[A-Za-z0-9_-]{24,128}"))
                getPreferences(MODE_PRIVATE).edit().putString("pair",candidate).apply();
        }
    }
    @Override protected void onNewIntent(Intent intent){super.onNewIntent(intent);setIntent(intent);acceptPairLink(intent);if(session!=null)session.reload();}""",
"""    private String acceptPairLink(Intent i){
        Uri u=i==null?null:i.getData();
        if(u==null)return ""; // Normal launcher open is not a pairing attempt.
        if(!"alyayoda".equals(u.getScheme()) || !"pair".equals(u.getHost()))
            return "Nem megfelelő párosítási hivatkozás.";
        String candidate=u.getLastPathSegment();
        if(candidate==null || !candidate.matches("[A-Za-z0-9_-]{24,128}"))
            return "A párosítási hivatkozás nem tartalmaz érvényes kódot.";
        // commit(), not apply(): this must be persisted BEFORE returning, so
        // even an immediate Activity recreation sees the new pairing.
        boolean saved=getPreferences(MODE_PRIVATE).edit().putString("pair",candidate).commit();
        return saved?"Párosítókód eltárolva. Szerverellenőrzés még hátravan.":
                     "A párosítókód mentése nem sikerült.";
    }
    @Override protected void onNewIntent(Intent intent){
        super.onNewIntent(intent);
        setIntent(intent);
        String status=acceptPairLink(intent);
        if(!status.isEmpty())showPairStatus(status);
        if(session!=null && !status.isEmpty())session.reload();
    }""","pairing intent lifecycle")
p.write_text(s,encoding="utf-8")

page=base/"app/src/main/assets/yodabridge/page.js"
src=page.read_text(encoding="utf-8")
old="""    window.postMessage({type:'__ALYA_YODA_PAIR_CHECK_V1'},location.origin);
  }"""
if src.count(old)!=1:raise RuntimeError("V11 pair check anchor")
src=src.replace(old,"""    // The old application checked only ONCE. The native Activity can
    // receive an Android deeplink after the page has loaded, and the
    // extension listener may not yet have attached at document_start.
    // Polling refreshes stale state without reloading the ChatGPT login.
    window.postMessage({type:'__ALYA_YODA_PAIR_CHECK_V1'},location.origin);
    setInterval(()=>{
      if(document.visibilityState==='visible'){
        window.postMessage({type:'__ALYA_YODA_PAIR_CHECK_V1'},location.origin);
      }
    },1500);
  }""")
old="""    label(paired?'A Szuhay párosítóadata rögzítve (szerverkapcsolat még nem tesztelt).':
      'A Szuhay-híd biztonságos egyszeri párosítása még hiányzik.');"""
if src.count(old)!=1:raise RuntimeError("V11 V3 pair label expected")
src=src.replace(old,"""    const newText=paired?'A Szuhay párosítóadata rögzítve (szerverkapcsolat még nem tesztelt).':
      'A Szuhay-híd biztonságos egyszeri párosítása még hiányzik.';
    // Don't override more important voice status messages on every 1.5 sec tick.
    if((note?.textContent||'').includes('párosító')||
       (note?.textContent||'').includes('Szuhay-híd')||
       (note?.textContent||'').includes('Kapcsolódás')) label(newText);""")
page.write_text(src,encoding="utf-8")
tests=base/"test_project.py"
tests.write_text(tests.read_text(encoding="utf-8")+'''
v11=(base/'app/src/main/java/hu/alya/yoda/MainActivity.java').read_text()
assert 'initialPairStatus=acceptPairLink(getIntent());' in v11
assert 'String status=acceptPairLink(intent);' in v11
assert 'Párosítókód eltárolva. Szerverellenőrzés még hátravan.' in v11
assert '.putString("pair",candidate).commit()' in v11
assert 'message.setVisibility(android.view.View.VISIBLE)' in v11
assert 'getData()' in v11 and 'getLastPathSegment()' in v11
v11js=(base/'app/src/main/assets/yodabridge/page.js').read_text()
assert 'window.postMessage({type:\\'__ALYA_YODA_PAIR_CHECK_V1\\'}' in v11js
assert "    },1500);" in v11js
assert "chip.id='alya-yoda-chip'" in v11js
''',encoding="utf-8")
print("PASS V11: native pairing receipt status, durable storage and refresh")
