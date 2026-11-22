#!/usr/bin/env python3
"""V5: scoped browser autoplay permission for chatgpt.com only.
GeckoView PermissionDelegate is documented by Mozilla to control audible autoplay.
No auth bypass, no additional AI/TTS, no alteration of the protected server.
"""
from pathlib import Path
root=Path("android-one-icon")
p=root/"app/src/main/java/hu/alya/yoda/MainActivity.java"
s=p.read_text(encoding="utf-8")
anchor='        session.setPermissionDelegate(new GeckoSession.PermissionDelegate() {\n'
if s.count(anchor)!=1:raise RuntimeError("Could not find Gecko permission delegate")
addition='''        session.setPermissionDelegate(new GeckoSession.PermissionDelegate() {
            // Allow the app's OWN ChatGPT answer audio to start without a second tap.
            // Other sites (including external OAuth hosts) retain default policy.
            @Override public GeckoResult<Integer> onContentPermissionRequest(
                    GeckoSession current, ContentPermission perm) {
                final String host;
                try {host=Uri.parse(perm.uri).getHost();}
                catch(Exception ex) {return null;}
                if ("chatgpt.com".equals(host) &&
                        (perm.permission==PERMISSION_AUTOPLAY_AUDIBLE ||
                         perm.permission==PERMISSION_AUTOPLAY_INAUDIBLE))
                    return GeckoResult.fromValue(ContentPermission.VALUE_ALLOW);
                return null;
            }
'''
s=s.replace(anchor,addition)
p.write_text(s,encoding="utf-8")
test=root/"test_project.py"
test.write_text(test.read_text(encoding="utf-8")+'''
v5=(base/'app/src/main/java/hu/alya/yoda/MainActivity.java').read_text()
assert 'onContentPermissionRequest(' in v5
assert 'PERMISSION_AUTOPLAY_AUDIBLE' in v5
assert '"chatgpt.com".equals(host)' in v5
assert 'ContentPermission.VALUE_ALLOW' in v5
''',encoding="utf-8")
print("V5 ChatGPT-only Gecko audible autoplay permission added")
