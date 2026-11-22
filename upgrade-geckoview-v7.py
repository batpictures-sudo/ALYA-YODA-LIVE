#!/usr/bin/env python3
"""V7: use a current stable GeckoView in the experimental Android APK.
GeckoView 143 was the 2025 build used by the initial source. This tests
Mozilla's newer 160 stable release, without touching Windows/Unikraft/Vercel.
"""
from pathlib import Path
p=Path("android-one-icon/app/build.gradle")
s=p.read_text(encoding="utf-8")
old="org.mozilla.geckoview:geckoview:143.0.20251003115653"
new="org.mozilla.geckoview:geckoview:160.0.20261116130455"
assert s.count(old)==1, "Unexpected GeckoView dependency"
p.write_text(s.replace(old,new),encoding="utf-8")
test=Path("android-one-icon/test_project.py")
test.write_text(test.read_text(encoding="utf-8")+"""
assert 'org.mozilla.geckoview:geckoview:160.0.20261116130455' in (base/'app/build.gradle').read_text()
""",encoding="utf-8")
print("V7 GeckoView stable 160 dependency verified")
