#!/usr/bin/env python3
"""
computer_agent.py — סוכן "עם עיניים" שמפעיל פיזית את שולחן העבודה (כולל CapCut).

לולאה: צילום מסך → Claude מנתח ומחזיר פעולה (קליק/הקלדה/גלילה) → הסוכן מבצע →
צילום מסך חדש חוזר ל-Claude → חוזר חלילה עד שהמשימה הושלמה.

⚠️ זהו בסיס לעבודה, לא מוצר מוגמר. הריצי בפיקוח בהתחלה. כל צעד = קריאת API.
דרישות: pip install -r requirements.txt  |  משתנה סביבה ANTHROPIC_API_KEY.

הרצה:
    setx ANTHROPIC_API_KEY "sk-ant-..."   (פעם אחת, ואז חלון חדש)
    python computer_agent.py --goal "פתח את CapCut, צור פרויקט 1080x1920, ייבא את הקליפים מהתיקייה ambiance, החל תבנית, וייצא"

עצירת חירום: הזיזי את העכבר לפינה השמאלית-עליונה (pyautogui failsafe) או Ctrl+C.
"""
import argparse
import base64
import getpass
import io
import os
import sys
import time
import traceback

import pyautogui
from PIL import Image
import anthropic
try:
    import pyperclip   # הקלדה דרך clipboard — חסינה לפריסת מקלדת עברית
except Exception:
    pyperclip = None


class Tee:
    """כותב כל פלט גם למסך וגם לקובץ לוג — כדי שגם אם החלון נסגר, נשאר תיעוד."""
    def __init__(self, *streams):
        self.streams = streams
    def write(self, data):
        for s in self.streams:
            try:
                s.write(data)
                s.flush()
            except Exception:
                pass
    def flush(self):
        for s in self.streams:
            try:
                s.flush()
            except Exception:
                pass

# --- מפרט הכלי computer-use (Opus 4.8/4.7/4.6, Sonnet 4.6, Opus 4.5) ---
TOOL_TYPE = "computer_20251124"
BETA_HEADER = "computer-use-2025-11-24"
MODEL = os.environ.get("AGENT_MODEL", "claude-opus-4-8")

# רזולוציית יעד שנשלחת למודל (דיוק טוב יותר ברזולוציה בינונית). הקואורדינטות מומרות חזרה למסך האמיתי.
TARGET_W = 1024
MAX_STEPS = 120
KEEP_IMAGES = 2   # כמה צילומי מסך אחרונים לשמור בהיסטוריה (חיסכון בטוקנים)

# הערה: ה-failsafe של פינת-מסך כבוי, כי הסוכן לוחץ לגיטימית על כפתורים בפינות.
# עצירת חירום: Ctrl+C בחלון ה-PowerShell.
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.3

SCREEN_W, SCREEN_H = pyautogui.size()
SCALE = TARGET_W / SCREEN_W
SEND_W, SEND_H = int(SCREEN_W * SCALE), int(SCREEN_H * SCALE)

# מיפוי בסיסי של מקשים (xdotool-style מ-Claude → pyautogui)
KEYMAP = {
    "Return": "enter", "KP_Enter": "enter", "Escape": "esc", "BackSpace": "backspace",
    "Delete": "delete", "Tab": "tab", "space": "space", "Up": "up", "Down": "down",
    "Left": "left", "Right": "right", "Home": "home", "End": "end",
    "Page_Up": "pageup", "Page_Down": "pagedown", "ctrl": "ctrl", "alt": "alt",
    "shift": "shift", "super": "win", "cmd": "win",
}


def grab_screenshot_b64():
    """צילום מסך → מוקטן ל-SEND_W×SEND_H → PNG base64."""
    img = pyautogui.screenshot().resize((SEND_W, SEND_H), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def to_screen(x, y):
    """המרת קואורדינטות מהמודל (מרחב SEND) למסך האמיתי."""
    return int(x / SCALE), int(y / SCALE)


def press_key(combo):
    parts = [KEYMAP.get(p, p.lower()) for p in combo.split("+")]
    if len(parts) == 1:
        pyautogui.press(parts[0])
    else:
        pyautogui.hotkey(*parts)


def run_action(action, inp):
    """מבצע פעולת computer-use אחת. מחזיר True אם צריך להחזיר צילום מסך."""
    if action == "screenshot":
        return True
    if action in ("mouse_move", "left_click", "right_click", "middle_click",
                  "double_click", "triple_click", "left_mouse_down", "left_mouse_up"):
        if inp.get("coordinate"):
            x, y = to_screen(*inp["coordinate"])
            pyautogui.moveTo(x, y)
        if action == "left_click":
            pyautogui.click()
        elif action == "right_click":
            pyautogui.click(button="right")
        elif action == "middle_click":
            pyautogui.click(button="middle")
        elif action == "double_click":
            pyautogui.doubleClick()
        elif action == "triple_click":
            pyautogui.click(clicks=3)
        elif action == "left_mouse_down":
            pyautogui.mouseDown()
        elif action == "left_mouse_up":
            pyautogui.mouseUp()
        return True
    if action == "left_click_drag" and inp.get("coordinate"):
        x, y = to_screen(*inp["coordinate"])
        pyautogui.dragTo(x, y, duration=0.4)
        return True
    if action == "type":
        text = inp.get("text", "")
        if pyperclip is not None:           # הדבקה מה-clipboard (חסין לעברית/autocomplete)
            pyperclip.copy(text)
            pyautogui.hotkey("ctrl", "v")
        else:
            pyautogui.write(text, interval=0.03)
        return True
    if action == "key":
        press_key(inp.get("text", ""))
        return True
    if action == "scroll":
        if inp.get("coordinate"):
            x, y = to_screen(*inp["coordinate"])
            pyautogui.moveTo(x, y)
        amt = int(inp.get("scroll_amount", 3)) * 100
        if inp.get("scroll_direction") == "down":
            amt = -amt
        pyautogui.scroll(amt)
        return True
    if action in ("wait", "cursor_position"):
        time.sleep(float(inp.get("duration", 1)) if action == "wait" else 0)
        return True
    print(f"[!] פעולה לא נתמכת: {action}")
    return True


def prune_images(messages, keep=KEEP_IMAGES):
    """משאיר רק את `keep` צילומי המסך האחרונים בהיסטוריה; מחליף ישנים בטקסט — חיסכון בטוקנים."""
    locs = []
    for m in messages:
        if isinstance(m.get("content"), list):
            for b in m["content"]:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    for ci, c in enumerate(b.get("content", [])):
                        if isinstance(c, dict) and c.get("type") == "image":
                            locs.append((b, ci))
    for b, ci in locs[:-keep] if keep > 0 else locs:
        b["content"][ci] = {"type": "text", "text": "[צילום מסך קודם הוסר לחיסכון]"}
    return messages


def tool_result(tool_use_id, screenshot=True, text=None):
    content = []
    if text:
        content.append({"type": "text", "text": text})
    if screenshot:
        content.append({"type": "image", "source": {
            "type": "base64", "media_type": "image/png", "data": grab_screenshot_b64()}})
    return {"type": "tool_result", "tool_use_id": tool_use_id, "content": content}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--goal", required=True, help="המשימה בשפה חופשית")
    ap.add_argument("--max-steps", type=int, default=MAX_STEPS)
    args = ap.parse_args()

    # מפתח ה-API: מהסביבה אם קיים, אחרת מבקשים להדביק (ההקלדה מוסתרת, לא נשמר בשום מקום)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key or api_key.startswith("sk-ant-...") or api_key == "sk-ant-...":
        api_key = getpass.getpass("הדבק כאן את מפתח ה-Anthropic API (sk-ant-...) ו-Enter: ").strip()
    if not api_key.startswith("sk-ant-"):
        sys.exit("המפתח לא תקין (אמור להתחיל ב-sk-ant-).")

    client = anthropic.Anthropic(api_key=api_key)
    tools = [{"type": TOOL_TYPE, "name": "computer",
              "display_width_px": SEND_W, "display_height_px": SEND_H, "display_number": 1}]
    base = ("את סוכן שמפעיל מחשב Windows כדי לערוך וידאו ב-CapCut. "
              "הנח ש-CapCut כבר פתוח ובפוקוס. אם את רואה אפליקציה אחרת (Chrome, הגדרות, וואטסאפ) — "
              "אל תתעסקי איתה; הביאי את CapCut לפוקוס בלחיצה על האייקון שלו בשורת המשימות התחתונה, ואז המשיכי. "
              "אל תפתחי תפריט התחל, אל תשתמשי בחיפוש של Windows, ואל תיבהלי מפופ-אפים — סגרי/התעלמי והמשיכי במשימה. "
              "הקלדה (action 'type') מתבצעת דרך הדבקה מ-clipboard, אז היא חסינה לפריסת מקלדת עברית — אל תבזבזי צעדים על החלפת שפה. "
              "כדי לנקות שדה: Ctrl+A ואז הקלידי (ההדבקה תחליף את הנבחר). "
              "לייבוא קבצים בחלון פתיחה: לחצי על שורת הכתובת למעלה, הקלידי את נתיב התיקייה ו-Enter, ואז Ctrl+A לבחירת כל הקבצים ו-Enter. "
              "פעלי צעד-צעד, צלמי מסך לפני כל פעולה כדי לוודא מה רואים, ואל תניחי הנחות.")

    here = os.path.dirname(os.path.abspath(__file__))

    def _read(name):
        p = os.path.join(here, name)
        return open(p, encoding="utf-8").read().strip() if os.path.exists(p) else ""

    knowledge = _read("capcut_knowledge.md")
    memory = _read("capcut_memory.md")
    system = base
    if knowledge:
        system += "\n\n=== ידע מקצועי על CapCut ===\n" + knowledge
    if memory:
        system += "\n\n=== מה שלמדת בסשנים קודמים (זיכרון) ===\n" + memory

    messages = [{"role": "user", "content": args.goal}]
    transcript = []   # נצבר טקסט של הסוכן ללמידה בסוף

    print(f"מסך {SCREEN_W}x{SCREEN_H} → נשלח {SEND_W}x{SEND_H} | מודל {MODEL}")
    print("⚠️ עצירת חירום: Ctrl+C בחלון הזה.")
    for s in (3, 2, 1):
        print(f"   מתחיל בעוד {s}... (הביאי את CapCut לפוקוס)")
        time.sleep(1)
    print()

    # Prompt caching: בסיס הידע (~2000 טוקנים) נשלח פעם אחת ונקרא מקאש בכל הצעדים הבאים → 90% חיסכון.
    system_blocks = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]

    for step in range(args.max_steps):
        prune_images(messages)   # שומר רק צילומי מסך אחרונים — חיסכון בעלות
        resp = client.beta.messages.create(
            model=MODEL, max_tokens=4096, system=system_blocks,
            tools=tools, messages=messages, betas=[BETA_HEADER],
        )
        messages.append({"role": "assistant", "content": resp.content})

        for block in resp.content:
            if block.type == "text" and block.text.strip():
                print(f"[Claude] {block.text.strip()}")
                transcript.append(block.text.strip())

        if resp.stop_reason != "tool_use":
            print("\n✅ הסוכן סיים.")
            break

        results = []
        for block in resp.content:
            if block.type == "tool_use":
                action = block.input.get("action", "")
                print(f"  → {action} {block.input.get('coordinate', '')}")
                run_action(action, block.input)
                time.sleep(0.4)
                results.append(tool_result(block.id, screenshot=True))
        messages.append({"role": "user", "content": results})
    else:
        print("\n[!] הגענו למקסימום צעדים. אפשר להעלות עם --max-steps.")

    # למידה: סיכום תמציתי של ידע ממשק לשימוש חוזר → נוסף ל-capcut_memory.md
    try:
        if transcript:
            note = client.messages.create(
                model=MODEL, max_tokens=600,
                messages=[{"role": "user", "content":
                    "להלן יומן פעולות של סוכן שעבד ב-CapCut. כתוב 4-8 בולטים תמציתיים בעברית "
                    "של ידע ממשק לשימוש חוזר (מיקומי כפתורים/תפריטים שראית, זרימות שעבדו, מכשולים שנתקלת בהם ואיך לעקוף). "
                    "רק בולטים מעשיים, בלי הקדמות:\n\n" + "\n".join(transcript)[:12000]}],
            )
            text = "".join(b.text for b in note.content if b.type == "text").strip()
            if text:
                with open(os.path.join(here, "capcut_memory.md"), "a", encoding="utf-8") as f:
                    f.write(f"\n## {time.strftime('%Y-%m-%d %H:%M')} — מטרה: {args.goal[:80]}\n{text}\n")
                print("\n🧠 נשמרו תובנות ל-capcut_memory.md")
    except Exception as e:
        print(f"[הערה: שמירת זיכרון נכשלה — {e}]")


if __name__ == "__main__":
    # לוג לקובץ: כל פלט ושגיאה נשמרים ל-agent_log.txt ליד הסקריפט — לאבחון גם אם החלון נסגר.
    _here = os.path.dirname(os.path.abspath(__file__))
    _logf = open(os.path.join(_here, "agent_log.txt"), "w", encoding="utf-8")
    _logf.write(f"=== הרצה חדשה {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    sys.stdout = Tee(sys.__stdout__, _logf)
    sys.stderr = Tee(sys.__stderr__, _logf)
    try:
        main()
    except KeyboardInterrupt:
        print("\n[עצירה ידנית — Ctrl+C]")
    except Exception:
        print("\n[!] שגיאה — הפרטים המלאים:")
        traceback.print_exc()
    finally:
        try:
            _logf.flush(); _logf.close()
        except Exception:
            pass
        # משאיר את החלון פתוח כדי שאפשר לקרוא את הפלט (גם אם קרסה ההרצה).
        try:
            input("\n--- ההרצה הסתיימה. הלוג נשמר ב-agent_log.txt. Enter לסגירה ---")
        except Exception:
            pass
