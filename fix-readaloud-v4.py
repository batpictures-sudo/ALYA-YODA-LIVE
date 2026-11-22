#!/usr/bin/env python3
"""V4: robust Read Aloud discovery in the live ChatGPT answer UI.

The menu/button probes are limited to the current assistant message.
No separate model or TTS fallback is introduced.
"""
from pathlib import Path
p=Path("android-one-icon/app/src/main/assets/yodabridge/page.js")
s=p.read_text(encoding="utf-8")
def rep(old,new,name):
    global s
    n=s.count(old)
    if n!=1: raise RuntimeError(f"{name}: expected one anchor, got {n}")
    s=s.replace(old,new)

rep("  let knownAssistants=new WeakSet(), autoReadAttempted=false, submitting=false;",
    "  let knownAssistants=new WeakSet(), autoReadAttempted=false, moreMenuAttempted=false, submitting=false;",
    "menu state")
rep("      currentAnswer=null;autoReadAttempted=false;answerChangedAt=Date.now();",
    "      currentAnswer=null;autoReadAttempted=false;moreMenuAttempted=false;answerChangedAt=Date.now();",
    "menu reset")
start=s.index("  function findReadAloud(message){")
end=s.index("  function stillGenerating(){",start)
original=s[start:end]
replacement="""  // Some ChatGPT UI variants put Felolvasás behind the response's overflow menu.
  // Search only the current assistant reply's action region; never click unrelated page controls.
  function findReadAloud(message){
    if(!message)return null;
    const root=message.closest('article') || message.parentElement?.parentElement?.parentElement || message;
    const readLabel=/read aloud|felolvasás|felolvas|listen to|hangos felolvasás/i;
    function tag(node){
      return [node?.getAttribute?.('aria-label'),node?.getAttribute?.('title'),
        node?.getAttribute?.('data-testid'),node?.textContent]
        .filter(Boolean).join(' ');
    }
    const local=[...root.querySelectorAll('button,[role="menuitem"]')];
    const direct=local.find(node=>readLabel.test(tag(node)));
    if(direct)return direct;
    // A menu is rendered in a portal outside the assistant's DOM tree.
    const menu=[...document.querySelectorAll('[role="menuitem"],[data-radix-menu-content] button')]
      .find(node=>readLabel.test(tag(node)) && node.getClientRects().length);
    if(menu)return menu;
    if(!moreMenuAttempted){
      const more=local.find(node=>{
        const text=tag(node).trim().toLowerCase();
        return /(?:^|\\\\s)(?:more|további|több|egyéb)(?:\\\\s|$)|overflow|ellipsis|additional actions/i.test(text);
      });
      if(more && more.getClientRects().length){
        moreMenuAttempted=true;
        more.click();
        label('A ChatGPT további műveletei közt keresem a Felolvasást…');
      }
    }
    return null;
  }
"""
if s.count(original)!=1: raise RuntimeError("findReadAloud block ambiguous")
s=s[:start]+replacement+s[end:]
# Restore regex whitespace escapes from the Python raw string; JS regex should use \s not \\s.
s=s.replace("(?:^|\\\\s)(?:more|további|több|egyéb)(?:\\\\s|$)","(?:^|\\s)(?:more|további|több|egyéb)(?:\\s|$)")
rep("  function followAnswer(){\n    if(!running||!waitingAnswer)return;",
"""  function followAnswer(){
    if(!running||!waitingAnswer)return;
    if(!currentAnswer && Date.now()-answerChangedAt>90000){
      waitingAnswer=false;
      label('A ChatGPT nem válaszolt időben; a kérdés nem lett újra elküldve.');
      nativeCommand('submitFailure','Nem érkezett ChatGPT-válasz 90 másodpercen belül.');
      return;
    }""","no response timeout")
p.write_text(s,encoding="utf-8")
checks=Path("android-one-icon/test_project.py")
checks.write_text(checks.read_text(encoding="utf-8")+"""
assert 'moreMenuAttempted=true;' in js
assert 'A ChatGPT nem válaszolt időben' in js
assert 'read aloud|felolvasás' in js
""",encoding="utf-8")
print("V4 automatic Read Aloud menu fallback and timeout patch applied")
