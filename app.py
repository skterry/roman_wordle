import datetime
import os
import random

import streamlit as st
from PIL import Image

from secret_words import KEYS

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


def get_daily_word() -> str:
    _overrides = {
        "2026-06-04": "BULGE",
    }
    today = datetime.date.today().isoformat()   # e.g. "2026-06-04"
    if today in _overrides:
        return _overrides[today]
    # Sort first so the list order is stable regardless of set iteration order.
    words = sorted(w.upper() for w in KEYS if isinstance(w, str) and w.isalpha())
    return random.Random(today).choice(words)


def start_game() -> None:
    st.session_state.secret_word = get_daily_word()
    st.session_state.game_active = True


def build_game_html(secret_word: str) -> tuple[str, int, int]:
    word_len = len(secret_word)
    max_guesses = 6

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: Arial, sans-serif;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
}}

/* ── message ── */
#message {{
  height: 36px; line-height: 36px;
  font-size: 1.1rem; font-weight: 700;
  text-align: center;
  color: #1a1a1b;
  margin-bottom: 10px;
  min-width: 300px;
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
  width: 56px; height: 56px;
  border: 2px solid #d3d6da;
  display: flex; align-items: center; justify-content: center;
  font-size: 2rem; font-weight: bold;
  color: #1a1a1b;
  text-transform: uppercase;
  user-select: none;
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
  height: 56px; min-width: 42px; padding: 0 6px;
  border: none; border-radius: 4px;
  background: #d3d6da;
  font-size: 0.85rem; font-weight: 700;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  text-transform: uppercase;
  color: #1a1a1b;
  transition: background 0.2s, color 0.2s;
  user-select: none;
}}
.key.wide    {{ min-width: 66px; font-size: 0.78rem; }}
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
</style>
</head>
<body>

<div class="wl-title">ROMAN WORDLE</div>
<div class="wl-sub">Guess words related to the Roman mission and the universe!</div>
<div id="message"></div>
<div id="board"></div>
<div id="keyboard"></div>
<button id="giveup-btn" onclick="giveUp()">Give Up</button>
<div class="watermark">Created by: S. K. Terry</div>

<script>
const SECRET      = '{secret_word}';
const WORD_LEN    = {word_len};
const MAX_GUESSES = {max_guesses};

let guesses  = [];
let current  = '';
let gameOver = false;

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
      btn.addEventListener('click', () => handleKey(k));
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
  if      (e.key === 'Backspace')          handleKey('⌫');
  else if (e.key === 'Enter')              handleKey('Enter');
  else if (/^[A-Za-z]$/.test(e.key))      handleKey(e.key);
}});

function renderCurrent() {{
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
function submitGuess() {{
  if (current.length < WORD_LEN) {{
    shakeRow(guesses.length);
    showMsg('Not enough letters', 'info');
    return;
  }}

  const guess  = current;
  const result = evaluate(guess);
  const rowIdx = guesses.length;

  guesses.push(guess);
  current = '';

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

// ── init ──
buildBoard();
buildKeyboard();
</script>
</body>
</html>"""

    # Keyboard is ~471px wide (row 3: 7×42 + 2×66 + 9×5 = 471)
    # Board width scales with word length
    board_w = word_len * (56 + 5) - 5
    total_w = max(board_w, 471) + 50

    # message + board + keyboard + watermark + padding
    total_h = (
        70                                       # title + subtitle
        + 36 + 10                                # message
        + max_guesses * (56 + 5) - 5 + 14       # board
        + 3 * 56 + 2 * 5                         # keyboard (3 rows)
        + 50                                     # give-up button
        + 40                                     # watermark + body padding
        + 30                                     # buffer
    )
    return html, total_w, total_h


# ── Streamlit UI ──
if st.button("New Game", type="primary"):
    start_game()
    st.rerun()

if not st.session_state.game_active:
    st.info("Click **New Game** to start playing.")
    st.stop()

secret = st.session_state.secret_word
html_str, w, h = build_game_html(secret)
st.iframe(html_str, width=w, height=h)
