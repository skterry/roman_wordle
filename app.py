import datetime
import os
import random

import streamlit as st
import streamlit.components.v1 as components
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
    .block-container {padding-top: 0.5rem; padding-bottom: 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

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
    iso = today.isoformat()
    if iso in _overrides:
        return _overrides[iso]

    words = sorted(w.upper() for w in KEYS if isinstance(w, str) and w.isalpha())

    day_index = (today - _ROTATION_EPOCH).days
    if day_index < 0:
        return random.Random(iso).choice(words)

    remaining = [w for w in words if w not in _ALREADY_USED]
    if day_index < len(remaining):
        order = remaining[:]
        random.Random("roman-wordle-cycle-0").shuffle(order)
        return order[day_index]

    cycle, pos = divmod(day_index - len(remaining), len(words))
    order = words[:]
    random.Random(f"roman-wordle-cycle-{cycle + 1}").shuffle(order)
    return order[pos]


_FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
_game_component = components.declare_component("roman_wordle", path=_FRONTEND_DIR)

secret  = get_daily_word()
allowed = sorted(w.upper() for w in KEYS if isinstance(w, str) and w.isalpha())

_game_component(
    secret=secret,
    allowed=allowed,
    default=None,
    key="wordle_game",
)
