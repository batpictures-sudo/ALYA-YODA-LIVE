#!/usr/bin/env python3
"""V10: make the original Yoda GeckoView overlay non-obstructive.

Preserve the REAL ChatGPT browser, the existing voice command bridge, and
Szuhay300; do not replace the architecture with Custom Tabs.
"""
from pathlib import Path
base=Path("android-one-icon")
p=base/"app/src/main/assets/yodabridge/page.js"
s=p.read_text(encoding="utf-8")
def replace_once(old,new,desc):
    global s
    n=s.count(old)
    if n!=1: raise RuntimeError(f"V10 {desc}: expected 1 anchor, found {n}")
    s=s.replace(old,new)
old="""    root.style.cssText='position:fixed;z-index:2147483646;inset:0;'
      +'background:linear-gradient(160deg,#10281d,#06150f);'
      +'display:flex;flex-direction:column;justify-content:center;'
      +'align-items:center;gap:15px;padding:28px;box-sizing:border-box;'
      +'color:white;font:18px system-ui;overflow:auto;text-align:center;';"""
new="""    // Hidden by default: NEVER cover the ChatGPT composer or Read Aloud controls.
    // The little YODA chip is the only persistent UI, in the upper corner.
    root.style.cssText='position:fixed;z-index:2147483646;top:64px;right:8px;'
      +'left:auto;bottom:auto;width:min(390px,calc(100vw - 16px));'
      +'max-height:65dvh;overflow:auto;background:#122719;'
      +'border:2px solid #9fd28b;border-radius:12px;'
      +'display:none;flex-direction:column;align-items:stretch;gap:12px;'
      +'padding:14px;box-sizing:border-box;color:white;font:16px system-ui;'
      +'box-shadow:0 4px 14px #0007;text-align:left;';"""
replace_once(old,new,"no full-screen overlay")
old="""    const back=document.createElement('button');
    back.textContent='Vissza az Alya–Yodához';
    back.style.cssText='display:none;position:fixed;z-index:2147483647;'
      +'right:12px;bottom:12px;background:#b8dd8c;color:#132a20;border:0;'
      +'border-radius:12px;padding:15px;font:bold 16px system-ui';
    setup.addEventListener('click',()=>{root.style.display='none';back.style.display='block';});
    back.addEventListener('click',()=>{root.style.display='flex';back.style.display='none';});
    root.append(heading,description,btn,note,setup);
    document.body.append(root,back);"""
new="""    const chip=document.createElement('button');
    chip.id='alya-yoda-chip';
    chip.type='button';
    chip.textContent='YODA';
    chip.setAttribute('aria-label','Yoda vezérlő megnyitása');
    chip.style.cssText='position:fixed;z-index:2147483647;'
      +'top:12px;right:8px;left:auto;bottom:auto;min-width:92px;'
      +'min-height:44px;max-width:45vw;padding:6px 12px;'
      +'background:#b8dd8c;color:#122719;border:1px solid #5f8457;'
      +'border-radius:99px;font:bold 15px system-ui;';
    const close=document.createElement('button');
    close.textContent='Vezérlő összecsukása';
    close.type='button';
    close.style.cssText='min-height:44px;background:transparent;color:#b8dd8c;'
      +'border:1px solid #688b5f;border-radius:9px;font:14px system-ui;';
    const collapse=()=>{root.style.display='none';chip.setAttribute('aria-expanded','false');};
    chip.addEventListener('click',()=>{
      const open=root.style.display==='none';
      root.style.display=open?'flex':'none';
      chip.setAttribute('aria-expanded',String(open));
    });
    close.addEventListener('click',collapse);
    setup.addEventListener('click',collapse);
    const updateChip=()=>{
      const text=btn?.textContent||'';
      if(text.includes('FIGYEL')){chip.textContent='YODA FIGYEL';collapse();}
      else chip.textContent='YODA';
    };
    const observerChip=new MutationObserver(updateChip);
    observerChip.observe(btn,{childList:true,subtree:true,characterData:true});
    root.append(heading,description,btn,note,setup,close);
    document.body.append(root,chip);
    // Initial page load always leaves ChatGPT usable, including login.
    collapse();"""
replace_once(old,new,"collapsible corner controls")
# The primary Start remains full width INSIDE the optional panel. Smaller for tablets.
replace_once("""    btn.style.cssText='display:block;width:100%;min-height:68px;background:#b0d78d;'
      +'border:0;border-radius:12px;font:bold 24px system-ui;color:#122719';""",
"""    btn.style.cssText='display:block;width:100%;min-height:52px;background:#b0d78d;'
      +'border:0;border-radius:12px;font:bold 20px system-ui;color:#122719';""",
"start button height")
# Test realistic HTML layout properties instead of a screenshot-only claim.
p.write_text(s,encoding="utf-8")
tests=base/"test_project.py"
tests.write_text(tests.read_text(encoding="utf-8")+'''
v10=(base/'app/src/main/assets/yodabridge/page.js').read_text()
assert "chip.id='alya-yoda-chip'" in v10
assert "root.style.display='none'" in v10
assert 'top:64px;right:8px;' in v10
assert "left:auto;bottom:auto;" in v10
assert "min-height:44px" in v10
assert 'document.body.append(root,chip);' in v10
assert 'document.body.append(root,back)' not in v10
assert 'inset:0;' not in v10
assert "btn.textContent='YODA INDÍTÁSA'" in v10
''',encoding="utf-8")
print("PASS V10: compact collapsible top-right Yoda UI, ChatGPT composer unobstructed")
