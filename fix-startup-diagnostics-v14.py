#!/usr/bin/env python3
"""V14: native startup crash screen; avoid silent close for catchable Java faults.
The launcher stays the real Yoda activity. No new secrets or account changes.
"""
from pathlib import Path
base=Path("android-one-icon")
p=base/"app/src/main/java/hu/alya/yoda/MainActivity.java"
s=p.read_text(encoding="utf-8")
def rep(old,new,tag):
 global s
 n=s.count(old)
 if n!=1:raise RuntimeError(f"V14 {tag}: expected one match, saw {n}")
 s=s.replace(old,new)
rep("import android.widget.Toast;\n","import android.widget.Toast;\nimport android.widget.Button;\nimport android.widget.LinearLayout;\n","diagnostic imports")
rep("    @Override public void onCreate(Bundle state) {\n        super.onCreate(state);\n        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);\n",
"""    private static String failureReason(Throwable failure) {
        StringBuilder result=new StringBuilder(failure.getClass().getSimpleName());
        if(failure.getMessage()!=null) {
            // Android exception messages can contain local paths. Avoid
            // including account tokens or URI query strings in the UI.
            String msg=failure.getMessage().replaceAll("(?i)(token|pair|key|password)=[^\\\\s&]+","$1=[rejtve]");
            result.append(": ").append(msg.length()>300?msg.substring(0,300):msg);
        }
        StackTraceElement[] trace=failure.getStackTrace();
        if(trace.length>0)result.append("\\\\nHelye: ").append(trace[0].getClassName())
            .append(".").append(trace[0].getMethodName()).append(":").append(trace[0].getLineNumber());
        return result.toString();
    }
    private void showStartupFailure(String reason) {
        LinearLayout layout=new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setBackgroundColor(0xff10261b);
        layout.setPadding(30,60,30,30);
        TextView title=new TextView(this);
        title.setText("ALYA–YODA – INDÍTÁSI HIBA");
        title.setTextSize(21);title.setTextColor(0xffd6edc0);
        TextView detail=new TextView(this);
        detail.setText(reason+"\\\\n\\\\nAz alkalmazás nem párosítás miatt állt le. Ezt a hibaszöveget mondd el Alyának.");
        detail.setTextSize(17);detail.setTextColor(Color.WHITE);
        Button retry=new Button(this);
        retry.setText("ÚJRAPRÓBÁLÁS");
        retry.setOnClickListener(v->{
            getPreferences(MODE_PRIVATE).edit().remove("last_startup_fault").commit();
            recreate();
        });
        layout.addView(title);layout.addView(detail);layout.addView(retry);
        setContentView(layout);
    }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        // Persist uncaught Java exceptions to show a diagnostic on next launch.
        // It deliberately does not handle native signal crashes.
        final Thread.UncaughtExceptionHandler old=Thread.getDefaultUncaughtExceptionHandler();
        Thread.setDefaultUncaughtExceptionHandler((thread,crash)->{
            try{getPreferences(MODE_PRIVATE).edit()
                .putString("last_startup_fault",failureReason(crash)).commit();}
            catch(Throwable ignored){}
            if(old!=null)old.uncaughtException(thread,crash);
        });
        String last=getPreferences(MODE_PRIVATE).getString("last_startup_fault","");
        if(!last.isEmpty()){
            showStartupFailure("A korábbi indításkor az Android ezt jelezte:\\\\n"+last);
            return;
        }
        try {
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
""","startup trace")
rep("""        if(initialPairStatus.isEmpty())message.postDelayed(hidePairMessage,10000);
    }

    private GeckoResult<Object> process""",
"""        if(initialPairStatus.isEmpty())message.postDelayed(hidePairMessage,10000);
        } catch(Throwable failure) {
            Log.e(TAG,"Startup failure",failure);
            getPreferences(MODE_PRIVATE).edit().putString("last_startup_fault",failureReason(failure)).commit();
            showStartupFailure(failureReason(failure));
        }
    }

    private GeckoResult<Object> process""","show native diagnostic screen")
rep("""    @Override protected void onResume(){
        super.onResume();
        if(speech!=null)speech.setForeground(true);
    }""",
"""    @Override protected void onResume(){
        super.onResume();
        try {if(speech!=null)speech.setForeground(true);}
        catch(Throwable t){Log.e(TAG,"Voice resume failed",t);showStartupFailure(failureReason(t));}
    }""","resume guard")
rep("""    @Override protected void onPause(){
        super.onPause();
        if(speech!=null)speech.setForeground(false);
    }""",
"""    @Override protected void onPause(){
        super.onPause();
        try {if(speech!=null)speech.setForeground(false);}
        catch(Throwable t){Log.e(TAG,"Voice pause failed",t);}
    }""","pause guard")
p.write_text(s,encoding="utf-8")
# Name and version stable; native diagnostics only. Preserve baked pair build placeholder.
gradle=base/"app/build.gradle"
g=gradle.read_text(encoding="utf-8").replace("versionCode 13","versionCode 14").replace("versionName '1.0.0'","versionName '1.0.1'")
gradle.write_text(g,encoding="utf-8")
t=base/"test_project.py"
t.write_text(t.read_text(encoding="utf-8").replace("assert 'versionCode 13' in (base/'app/build.gradle').read_text()","assert 'versionCode 14' in (base/'app/build.gradle').read_text()")+'''
v14=(base/'app/src/main/java/hu/alya/yoda/MainActivity.java').read_text()
assert 'showStartupFailure(failureReason(failure));' in v14
assert 'last_startup_fault' in v14
assert 'getPreferences(MODE_PRIVATE)' in v14
assert 'Thread.setDefaultUncaughtExceptionHandler' in v14
assert 'android.intent.action.SEND' in (base/'app/src/main/AndroidManifest.xml').read_text()
''',encoding="utf-8")
print("PASS V14: Android exception capture and legible native crash view")
