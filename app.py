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
    /* display:none fully removes the header from layout so its fixed-position
       stacking context no longer overlays the top of the component iframe. */
    header[data-testid="stHeader"] { display: none !important; }
    footer { visibility: hidden; }
    .block-container { padding-top: 0.5rem; padding-bottom: 0; }
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

# Second epoch. Adding 50 words to the bank on 2026-08-02 changed the contents of
# the cycle-0 `remaining` list, which reshuffles it and destroys the no-repeat
# guarantee. Rather than reshuffle, freeze everything served to date and deal the
# never-used words from a fresh seed starting here.
_ROTATION_EPOCH_2 = datetime.date(2026, 8, 3)

# Every word shown 2026-06-04..-08-02 under the 63-word bank. Held out of the
# epoch-2 pass so the 55 unseen words all appear before anything recurs.
_SERVED = frozenset(
    {
        "ARRAY", "BAND", "BULGE", "CHIEF", "COMET", "CORONA", "COSMOS",
        "DISK", "DITHER", "EARTH", "EPOCH", "EUCLID", "FIELD", "FILTER",
        "FLUX", "FOCAL", "GAIA", "GALAXY", "GIANT", "GRACE", "GRISM",
        "GUIDE", "HUBBLE", "IMAGE", "IMAGER", "LAUNCH", "LENS", "LIGHT",
        "MAST", "MIRROR", "MOSAIC", "NANCY", "NASA", "NEBULA", "NEXUS",
        "NOISE", "NOVA", "OPTIC", "ORBIT", "PHASE", "PHOTON", "PIXEL",
        "PRISM", "PROBE", "QUASAR", "RADIAL", "ROCKY", "ROMAN", "RUBIN",
        "SCOPE", "SENSOR", "SIGNAL", "SPIRAL", "STAR", "STRAY", "SURVEY",
        "WEBB", "WIDE",
    }
)


def get_daily_word() -> str:
    _overrides = {
        "2026-06-04": "BULGE",
        "2026-06-22": "GRISM",
        "2026-06-24": "SURVEY",
        # Pin the last pre-expansion day so the bank edit can't change it mid-play.
        "2026-08-02": "BAND",
    }
    today = datetime.date.today()
    iso = today.isoformat()
    if iso in _overrides:
        return _overrides[iso]

    words = sorted(w.upper() for w in KEYS if isinstance(w, str) and w.isalpha())

    if today >= _ROTATION_EPOCH_2:
        day_index = (today - _ROTATION_EPOCH_2).days
        fresh = [w for w in words if w not in _SERVED]
        if day_index < len(fresh):
            order = fresh[:]
            random.Random("roman-wordle-cycle-1").shuffle(order)
            return order[day_index]
        cycle, pos = divmod(day_index - len(fresh), len(words))
        order = words[:]
        random.Random(f"roman-wordle-cycle-{cycle + 2}").shuffle(order)
        return order[pos]

    # Legacy path, dead for any real "today" now that epoch 2 has opened. It no
    # longer reproduces 2026-06-14..-08-01 either, since those words were dealt
    # from the pre-expansion 63-word bank; _SERVED is the record of what ran.
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
