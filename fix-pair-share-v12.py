#!/usr/bin/env python3
"""V12: native Android Share-sheet pairing as alternative to broken deep links.

Accepts only an Alya–Yoda URI or a HTTPS URL from our known pairing page,
with a valid pairing fragment, via Android ACTION_SEND text/plain.
No token or signing secret is embedded into the app or public source.
"""
from pathlib import Path
base=Path("android-one-icon")
manifest=base/"app/src/main/AndroidManifest.xml"
m=manifest.read_text(encoding="utf-8")
anchor="""      <intent-filter>
        <action android:name="android.intent.action.VIEW"/>
        <category android:name="android.intent.category.DEFAULT"/>
        <category android:name="android.intent.category.BROWSABLE"/>
        <data android:scheme="alyayoda" android:host="pair"/>
      </intent-filter>"""
assert m.count(anchor)==1
m=m.replace(anchor,anchor+'''
      <!-- Can receive a pairing URL from Chrome's normal Android Share sheet. -->
      <intent-filter>
        <action android:name="android.intent.action.SEND"/>
        <category android:name="android.intent.category.DEFAULT"/>
        <data android:mimeType="text/plain"/>
      </intent-filter>''')
manifest.write_text(m,encoding="utf-8")
p=base/"app/src/main/java/hu/alya/yoda/MainActivity.java"
s=p.read_text(encoding="utf-8")
old="""    private String acceptPairLink(Intent i){
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
    }"""
new="""    private String acceptPairLink(Intent i){
        if(i==null)return "";
        Uri u=i.getData();
        // Chrome/Android may open a VIEW intent without preserving the data.
        // Receiving a SEND share is a separate, reliable fallback pathway.
        if(Intent.ACTION_SEND.equals(i.getAction()) &&
                "text/plain".equals(i.getType())) {
            String content=i.getStringExtra(Intent.EXTRA_TEXT);
            if(content==null || content.length()>2048)
                return "A megosztott párosítási link hiányzik vagy túl hosszú.";
            // Android shares may include a title plus URL. Extract only a
            // complete URL, never a naked secret code from unrelated text.
            java.util.regex.Matcher match=java.util.regex.Pattern
                .compile("(?i)(alyayoda://pair/[A-Za-z0-9_-]{24,128}|https://[^\\\\s]+)")
                .matcher(content);
            u=null;
            while(match.find()){
                Uri found=Uri.parse(match.group(1));
                if("alyayoda".equals(found.getScheme()) && "pair".equals(found.getHost())){
                    u=found;break;
                }
                if("https".equals(found.getScheme()) &&
                        ("alya-yoda-cloud.vercel.app".equals(found.getHost()) ||
                         "alya-yoda-cloud-eaww110nh-batpictures-4242s-projects.vercel.app".equals(found.getHost())) &&
                         found.getFragment()!=null){
                    u=found;break;
                }
            }
            if(u==null)return "A megosztott hivatkozás nem Alya–Yoda párosítás.";
        }
        if(u==null)return ""; // Normal launcher open.
        String candidate;
        if("alyayoda".equals(u.getScheme()) && "pair".equals(u.getHost())){
            candidate=u.getLastPathSegment();
        } else if("https".equals(u.getScheme()) &&
                ("alya-yoda-cloud.vercel.app".equals(u.getHost()) ||
                 "alya-yoda-cloud-eaww110nh-batpictures-4242s-projects.vercel.app".equals(u.getHost()))) {
            candidate=u.getFragment();
        } else {
            return "Nem megfelelő párosítási hivatkozás.";
        }
        if(candidate==null || !candidate.matches("[A-Za-z0-9_-]{24,128}"))
            return "A párosítási hivatkozás nem tartalmaz érvényes kódot.";
        // commit(), not apply(): paired state is durable even after task changes.
        boolean saved=getPreferences(MODE_PRIVATE).edit().putString("pair",candidate).commit();
        return saved?"Párosítókód eltárolva. Szerverellenőrzés még hátravan.":
                     "A párosítókód mentése nem sikerült.";
    }"""
if s.count(old)!=1:raise RuntimeError("V12 V11 acceptPairLink not found")
s=s.replace(old,new)
p.write_text(s,encoding="utf-8")
tests=base/"test_project.py"
tests.write_text(tests.read_text(encoding="utf-8")+'''
v12=(base/'app/src/main/java/hu/alya/yoda/MainActivity.java').read_text()
m12=(base/'app/src/main/AndroidManifest.xml').read_text()
assert 'android.intent.action.SEND' in m12
assert 'android:mimeType="text/plain"' in m12
assert 'Intent.ACTION_SEND.equals(i.getAction())' in v12
assert 'getStringExtra(Intent.EXTRA_TEXT)' in v12
assert 'candidate=u.getFragment();' in v12
assert 'getPreferences(MODE_PRIVATE).edit().putString("pair",candidate).commit();' in v12
assert 'Párosítókód eltárolva.' in v12
''',encoding="utf-8")
print("PASS V12: Android native Share pairing, strict URI validation, durable storage")
