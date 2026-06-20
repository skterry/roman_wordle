import datetime
import json
import os
import random

import streamlit as st
from PIL import Image

KEYS = set(st.secrets["game"]["words"])

_icon_path = os.path.join(os.path.dirname(__file__), "icon", "RST_icon.png")
st.set_page_config(
    page_title="Roman Wordle",
    layout="centered",
    page_icon=Image.open(_icon_path),
)

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer     {visibility: hidden;}
    .wl-title {
        font-size: 2.8rem; font-weight: 800; letter-spacing: 4px;
        text-align: center; color: #0b3d91; margin-bottom: 0;
    }
    .wl-sub {
        text-align: center; color: #888; font-size: 1.05rem; margin-bottom: 0.5rem;
    }
    div[data-testid="stButton"] > button {
        font-size: 1.1rem; padding: 7px 18px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

for _k, _v in {"game_active": False, "secret_word": None}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# First day the dedup rotation took over from the old per-day random.choice scheme.
_ROTATION_EPOCH = datetime.date(2026, 6, 14)

# Words already shown 2026-06-04..-13 under the old scheme. Held out of the first
# rotation pass so the whole bank cycles once before any of them can recur.
_ALREADY_USED = frozenset(
    {"BULGE", "GALAXY", "FLUX", "STRAY", "DISK", "NOISE", "CHIEF", "SPIRAL", "COMET"}
)


def get_daily_word() -> str:
    _overrides = {
        "2026-06-04": "BULGE",
    }
    today = datetime.date.today()
    iso = today.isoformat()   # e.g. "2026-06-04"
    if iso in _overrides:
        return _overrides[iso]

    # Sort first so the list order is stable regardless of set iteration order.
    words = sorted(w.upper() for w in KEYS if isinstance(w, str) and w.isalpha())

    day_index = (today - _ROTATION_EPOCH).days
    if day_index < 0:
        # Dates before the rotation began: preserve the original behavior.
        return random.Random(iso).choice(words)

    # First pass: the words not yet shown, in a fixed shuffled order. Once these
    # are exhausted, every later pass cycles the full bank, reshuffled per cycle.
    # This guarantees all words appear once before any repeat.
    remaining = [w for w in words if w not in _ALREADY_USED]
    if day_index < len(remaining):
        order = remaining[:]
        random.Random("roman-wordle-cycle-0").shuffle(order)
        return order[day_index]

    cycle, pos = divmod(day_index - len(remaining), len(words))
    order = words[:]
    random.Random(f"roman-wordle-cycle-{cycle + 1}").shuffle(order)
    return order[pos]


def start_game() -> None:
    st.session_state.secret_word = get_daily_word()
    st.session_state.game_active = True


def build_game_html(secret_word: str) -> str:
    word_len = len(secret_word)
    max_guesses = 6

    # Curated allow-list: our themed words (GAIA, NASA, WEBB, …) are proper nouns
    # and acronyms the public dictionary API doesn't know, so accept them directly.
    allowed_words = json.dumps(
        sorted(w.upper() for w in KEYS if isinstance(w, str) and w.isalpha())
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

/* Tile and key sizes cap at their desktop values but shrink to fit narrow
   phone screens. The keyboard's top row (10 keys) is the widest element, so
   --key is sized off 10 columns and the board off WORD_LEN columns; whichever
   is the binding constraint, both stay inside the viewport. */
:root {{
  --tile: min(56px, calc((100vw - 24px) / {word_len} - 5px));
  --key:  min(42px, calc((100vw - 24px - 45px) / 10));
}}
body {{
  font-family: Arial, sans-serif;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  -webkit-text-size-adjust: 100%;
  /* Prevent this iframe's scroll from bleeding into the Streamlit parent. */
  overscroll-behavior: contain;
}}

/* ── message ── */
#message {{
  height: 36px; line-height: 36px;
  font-size: 1.1rem; font-weight: 700;
  text-align: center;
  color: #1a1a1b;
  margin-bottom: 10px;
  min-width: min(300px, 92vw);
}}
#message.win  {{ color: #6aaa64; }}
#message.lose {{ color: #c0392b; }}
#message.info {{ color: #555; }}

/* ── board ── */
#board {{
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  margin-bottom: 14px;
}}
.row {{ display: flex; gap: 5px; }}
.tile {{
  width: var(--tile); height: var(--tile);
  border: 2px solid #d3d6da;
  display: flex; align-items: center; justify-content: center;
  font-size: calc(var(--tile) * 0.5); font-weight: bold;
  color: #1a1a1b;
  text-transform: uppercase;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}}
.tile.filled    {{ border-color: #878a8c; animation: pop 0.08s ease-in-out; }}
.tile.correct   {{ background: #6aaa64; color: #fff; border-color: #6aaa64; }}
.tile.present   {{ background: #d4762a; color: #fff; border-color: #d4762a; }}
.tile.absent    {{ background: #787c7e; color: #fff; border-color: #787c7e; }}
.tile.revealed  {{ background: #2e86de; color: #fff; border-color: #2e86de; }}

@keyframes pop {{
  0%   {{ transform: scale(1); }}
  50%  {{ transform: scale(1.12); }}
  100% {{ transform: scale(1); }}
}}
@keyframes shake {{
  0%, 100% {{ transform: translateX(0); }}
  20%       {{ transform: translateX(-5px); }}
  40%       {{ transform: translateX(5px); }}
  60%       {{ transform: translateX(-5px); }}
  80%       {{ transform: translateX(5px); }}
}}

/* ── keyboard ── */
#keyboard {{
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}}
.kb-row {{ display: flex; gap: 5px; }}
.key {{
  height: calc(var(--key) * 1.33); min-width: var(--key);
  padding: 0 calc(var(--key) * 0.14);
  border: none; border-radius: 4px;
  background: #d3d6da;
  font-size: calc(var(--key) * 0.34 + 4px); font-weight: 700;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  text-transform: uppercase;
  color: #1a1a1b;
  transition: background 0.2s, color 0.2s;
  user-select: none;
  /* Remove the 300ms tap delay and suppress the blue flash on mobile. */
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}}
.key.wide    {{ min-width: calc(var(--key) * 1.57); font-size: calc(var(--key) * 0.3 + 3px); }}
.key.correct {{ background: #6aaa64; color: #fff; }}
.key.present {{ background: #d4762a; color: #fff; }}
.key.absent  {{ background: #787c7e; color: #fff; }}

#giveup-btn {{
  margin-top: 14px;
  padding: 7px 22px;
  font-size: 0.9rem; font-weight: 700;
  color: #c0392b; background: #fff;
  border: 1.5px solid #c0392b; border-radius: 6px;
  cursor: pointer; transition: background 0.15s, color 0.15s;
}}
#giveup-btn:hover    {{ background: #c0392b; color: #fff; }}
#giveup-btn:disabled {{ opacity: 0.35; cursor: default; }}

.wl-title {{
  font-size: 2.2rem; font-weight: 800; letter-spacing: 4px;
  text-align: center; color: #0b3d91; margin-bottom: 2px;
}}
.wl-sub {{
  font-size: 0.95rem; color: #888;
  text-align: center; margin-bottom: 12px;
}}

.watermark {{
  margin-top: 10px;
  font-size: 0.65rem; color: rgba(0,0,0,0.25);
  letter-spacing: 0.5px; pointer-events: none; user-select: none;
}}

/* ── mobile native-keyboard support ── */
#kbd-hint {{
  font-size: 0.85rem; color: #0b3d91; font-weight: 600;
  text-align: center; margin-bottom: 10px;
  cursor: pointer; user-select: none;
  border: 1px dashed #b8c4e0; border-radius: 6px;
  padding: 6px 12px;
}}
#kbd-hint:active {{ background: #eef2fb; }}
/* Hide the hint on devices that have a real (hover-capable, fine) pointer. */
@media (hover: hover) and (pointer: fine) {{
  #kbd-hint {{ display: none; }}
}}
/* Off-screen input: focusing it summons the phone's native keyboard.
   position:fixed keeps iOS from scrolling the page when this gains focus
   (absolute at top:0 caused the outer Streamlit page to jump).
   font-size:16px prevents iOS auto-zoom on focus. */
#hidden-input {{
  position: fixed; top: -9999px; left: -9999px;
  height: 1px; width: 1px;
  opacity: 0; pointer-events: none;
  font-size: 16px; border: 0; padding: 0; background: transparent;
}}
</style>
</head>
<body>

<div class="wl-title">ROMAN WORDLE</div>
<div class="wl-sub">One Roman Space Telescope-themed word per day!</div>
<div id="kbd-hint">⌨️ Tap here to type with your keyboard</div>
<div id="message"></div>
<div id="board"></div>
<div id="keyboard"></div>
<button id="giveup-btn" onclick="giveUp()">Give Up</button>
<div class="watermark">Created by: S. K. Terry</div>
<input id="hidden-input" type="text" inputmode="text" enterkeyhint="go"
       maxlength="{word_len}" autocomplete="off" autocorrect="off"
       autocapitalize="characters" spellcheck="false"
       aria-hidden="true" tabindex="-1" />

<script>
const SECRET      = '{secret_word}';
const WORD_LEN    = {word_len};
const MAX_GUESSES = {max_guesses};
const ALLOWED     = new Set({allowed_words});   // our themed words, always valid

let guesses  = [];
let current  = '';
let gameOver = false;
let checking = false;   // true while a guess is being validated against the dictionary

const hiddenInput = document.getElementById('hidden-input');

// Returns true if `word` is a real English word (per the free Dictionary API).
// Fails open: if the API is unreachable, we allow the guess rather than block play.
async function isRealWord(word) {{
  if (ALLOWED.has(word.toUpperCase())) return true;   // curated themed words
  try {{
    const resp = await fetch(
      'https://api.dictionaryapi.dev/api/v2/entries/en/' + encodeURIComponent(word.toLowerCase())
    );
    if (resp.ok)            return true;   // 200 → word exists
    if (resp.status === 404) return false; // 404 → not a word
    return true;                           // other errors → don't penalize the player
  }} catch (e) {{
    return true;                           // network failure → fail open
  }}
}}

// ── DOM construction ──
function buildBoard() {{
  const board = document.getElementById('board');
  for (let r = 0; r < MAX_GUESSES; r++) {{
    const row = document.createElement('div');
    row.className = 'row';
    row.id = 'row-' + r;
    for (let c = 0; c < WORD_LEN; c++) {{
      const tile = document.createElement('div');
      tile.className = 'tile';
      tile.id = 'tile-' + r + '-' + c;
      row.appendChild(tile);
    }}
    board.appendChild(row);
  }}
}}

function buildKeyboard() {{
  const rows = [
    ['Q','W','E','R','T','Y','U','I','O','P'],
    ['A','S','D','F','G','H','J','K','L'],
    ['ENTER','Z','X','C','V','B','N','M','⌫']
  ];
  const kb = document.getElementById('keyboard');
  for (const row of rows) {{
    const div = document.createElement('div');
    div.className = 'kb-row';
    for (const k of row) {{
      const btn = document.createElement('button');
      btn.className = 'key' + (k.length > 1 ? ' wide' : '');
      btn.textContent = k;
      btn.id = 'key-' + k;
      // touchstart fires instantly (no 300ms delay) and preventDefault prevents
      // the touch from scrolling the page or propagating to the Streamlit parent.
      // A flag avoids double-firing when the browser also emits a synthetic click.
      let _touched = false;
      btn.addEventListener('touchstart', e => {{
        e.preventDefault();
        _touched = true;
        handleKey(k);
      }}, {{ passive: false }});
      btn.addEventListener('click', () => {{ if (!_touched) handleKey(k); _touched = false; }});
      div.appendChild(btn);
    }}
    kb.appendChild(div);
  }}
}}

// ── input handling ──
function handleKey(key) {{
  if (gameOver) return;
  if (key === '⌫' || key === 'Backspace') {{
    current = current.slice(0, -1);
    renderCurrent();
  }} else if (key === 'ENTER' || key === 'Enter') {{
    submitGuess();
  }} else if (/^[A-Za-z]$/.test(key) && current.length < WORD_LEN) {{
    current += key.toUpperCase();
    renderCurrent();
  }}
}}

document.addEventListener('keydown', e => {{
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  // When the off-screen input holds focus (mobile / native keyboard), its own
  // listeners handle typing — skip here to avoid registering each key twice.
  if (document.activeElement === hiddenInput) return;
  if      (e.key === 'Backspace')          handleKey('⌫');
  else if (e.key === 'Enter')              handleKey('Enter');
  else if (/^[A-Za-z]$/.test(e.key))      handleKey(e.key);
}});

function renderCurrent() {{
  // Keep the off-screen input in step with the model so switching between the
  // native keyboard, on-screen keyboard, and a physical keyboard never desyncs.
  if (hiddenInput.value !== current) hiddenInput.value = current;
  const r = guesses.length;
  for (let c = 0; c < WORD_LEN; c++) {{
    const tile = document.getElementById('tile-' + r + '-' + c);
    const letter = current[c] || '';
    tile.textContent = letter;
    if (letter) {{
      // Restart pop animation on each new letter
      tile.classList.remove('filled');
      void tile.offsetWidth;
      tile.classList.add('filled');
    }} else {{
      tile.className = 'tile';
    }}
  }}
}}

// ── guess evaluation ──
function evaluate(guess) {{
  const result = new Array(WORD_LEN).fill('absent');
  const pool   = {{}};
  // First pass: correct positions
  for (let i = 0; i < WORD_LEN; i++) {{
    if (guess[i] === SECRET[i]) {{
      result[i] = 'correct';
    }} else {{
      pool[SECRET[i]] = (pool[SECRET[i]] || 0) + 1;
    }}
  }}
  // Second pass: present letters
  for (let i = 0; i < WORD_LEN; i++) {{
    if (result[i] !== 'correct' && pool[guess[i]]) {{
      result[i] = 'present';
      pool[guess[i]]--;
    }}
  }}
  return result;
}}

// ── submission ──
async function submitGuess() {{
  if (checking) return;   // ignore re-entry while a dictionary check is in flight
  if (current.length < WORD_LEN) {{
    shakeRow(guesses.length);
    showMsg('Not enough letters', 'info');
    return;
  }}

  const guess = current;

  // Reject guesses that aren't real English words (does not consume a turn).
  checking = true;
  showMsg('Checking…', 'info');
  const valid = await isRealWord(guess);
  checking = false;
  if (gameOver) return;   // game may have ended while we were waiting
  if (!valid) {{
    shakeRow(guesses.length);
    showMsg('Not in word list', 'info');
    return;
  }}

  showMsg('', '');   // clear the "Checking…" notice
  const result = evaluate(guess);
  const rowIdx = guesses.length;

  guesses.push(guess);
  current = '';
  hiddenInput.value = '';

  // Reveal tiles one at a time with a squish animation
  const STEP = 280;
  for (let c = 0; c < WORD_LEN; c++) {{
    const tile = document.getElementById('tile-' + rowIdx + '-' + c);
    ;(function(t, cls, delay) {{
      setTimeout(() => {{
        t.style.transition = 'transform 0.12s ease-in';
        t.style.transform  = 'scaleY(0)';
        setTimeout(() => {{
          t.className       = 'tile ' + cls;
          t.style.transition = 'transform 0.12s ease-out';
          t.style.transform  = 'scaleY(1)';
        }}, 120);
      }}, delay);
    }})(tile, result[c], c * STEP);
  }}

  // After all tiles flip: update keyboard and check end conditions
  setTimeout(() => {{
    updateKeyboard(guess, result);
    if (guess === SECRET) {{
      gameOver = true;
      const msgs = ['Genius!', 'Magnificent!', 'Impressive!', 'Splendid!', 'Great!', 'Phew!'];
      showMsg(msgs[rowIdx] || 'Correct!', 'win');
    }} else if (guesses.length === MAX_GUESSES) {{
      gameOver = true;
      showMsg('The word was: ' + SECRET, 'lose');
    }}
  }}, WORD_LEN * STEP + 150);
}}

function updateKeyboard(guess, result) {{
  const pri = {{ correct: 3, present: 2, absent: 1 }};
  for (let i = 0; i < WORD_LEN; i++) {{
    const el = document.getElementById('key-' + guess[i]);
    if (!el) continue;
    const curPri = el.classList.contains('correct') ? 3
                 : el.classList.contains('present') ? 2
                 : el.classList.contains('absent')  ? 1 : 0;
    if (pri[result[i]] > curPri) {{
      el.className = 'key ' + result[i];
    }}
  }}
}}

function showMsg(text, cls) {{
  const el = document.getElementById('message');
  el.textContent = text;
  el.className   = cls || '';
  if (cls === 'info') {{
    setTimeout(() => {{
      if (el.textContent === text) {{ el.textContent = ''; el.className = ''; }}
    }}, 1400);
  }}
}}

function shakeRow(r) {{
  const row = document.getElementById('row-' + r);
  row.style.animation = 'shake 0.4s ease';
  setTimeout(() => {{ row.style.animation = ''; }}, 400);
}}

// ── give up ──
function giveUp() {{
  if (gameOver) return;
  if (!confirm('Give up and reveal the mystery word?')) return;
  gameOver = true;
  current  = '';
  hiddenInput.value = '';
  hiddenInput.blur();   // dismiss the native keyboard once the game ends

  const rowIdx = guesses.length;
  const STEP   = 200;
  for (let c = 0; c < WORD_LEN; c++) {{
    const tile = document.getElementById('tile-' + rowIdx + '-' + c);
    ;(function(t, letter, delay) {{
      setTimeout(() => {{
        t.textContent      = letter;
        t.style.transition = 'transform 0.12s ease-in';
        t.style.transform  = 'scaleY(0)';
        setTimeout(() => {{
          t.className        = 'tile revealed';
          t.style.transition = 'transform 0.12s ease-out';
          t.style.transform  = 'scaleY(1)';
        }}, 120);
      }}, delay);
    }})(tile, SECRET[c], c * STEP);
  }}

  setTimeout(() => {{
    showMsg('The word was: ' + SECRET, 'lose');
    document.getElementById('giveup-btn').disabled = true;
  }}, WORD_LEN * STEP + 150);
}}

// ── native (mobile) keyboard support ──
// The off-screen #hidden-input is the bridge to the phone's on-screen keyboard.
// iOS only opens that keyboard from inside a user gesture, so we focus the input
// when the player taps the hint banner or anywhere on the board.
function focusInput() {{
  if (gameOver) return;
  hiddenInput.focus({{ preventScroll: true }});
}}
document.getElementById('kbd-hint').addEventListener('click', focusInput);
document.getElementById('board').addEventListener('click', focusInput);

// Mirror whatever is in the input back into the in-progress guess. Driving the
// model from the input value (rather than per-keystroke) means typing AND
// deletes both work, even on Android keyboards that don't emit real keydowns.
hiddenInput.addEventListener('input', () => {{
  if (gameOver) {{ hiddenInput.value = ''; return; }}
  const cleaned = hiddenInput.value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, WORD_LEN);
  if (hiddenInput.value !== cleaned) hiddenInput.value = cleaned;
  current = cleaned;
  renderCurrent();
}});

// The native keyboard's "go"/return key submits the guess.
hiddenInput.addEventListener('keydown', e => {{
  if (e.key === 'Enter') {{ e.preventDefault(); submitGuess(); }}
}});

// ── init ──
buildBoard();
buildKeyboard();
</script>
</body>
</html>"""

    # Sizing is handled responsively inside the HTML (CSS derives tile/key sizes
    # from the viewport width), so the iframe is embedded fluidly with
    # width="stretch" / height="content" — no fixed pixel dimensions needed.
    return html


# ── Streamlit UI ──
if st.button("New Game", type="primary"):
    start_game()
    st.rerun()

if not st.session_state.game_active:
    st.info("Click **New Game** to start playing.")
    st.stop()

secret = st.session_state.secret_word
html_str = build_game_html(secret)
st.iframe(html_str, width="stretch", height="content")
