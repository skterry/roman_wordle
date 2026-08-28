# Roman Wordle

<p>
  Hosted on Streamlit
  <a href="https://streamlit.io/" target="_blank">
    <img src="icon/streamlit_icon.png" alt="Streamlit" height="22" align="top"/>
  </a>
</p>

<a href="https://romanwordle.streamlit.app/" target="_blank">
  <img src="https://img.shields.io/badge/Play%20Now-brightgreen?style=for-the-badge" alt="Play Now!"/>
</a>

A daily word-guessing game themed around the [Nancy Grace Roman Space Telescope](https://roman.gsfc.nasa.gov/).

---

## About the Game

Roman Wordle is a browser-based take on the classic Wordle format, where players have **6 attempts** to guess a hidden mystery word. All mystery words are drawn from the vocabulary of the Roman Space Telescope mission — instruments, science targets, mission concepts, and related astronomy terms.

### Tile colors

| Color | Meaning |
|-------|---------|
| 🟩 Green | Correct letter, correct position |
| 🟧 Orange | Letter is in the word, but wrong position |
| ⬜ Gray | Letter is not in the word |

### Daily word

A new mystery word is automatically selected each calendar day. All players see the same word on the same day - the word rotates at midnight based on the current date.

### Give Up

If you're stuck, the **Give Up** button ends the current game and reveals the mystery word in blue tiles.

---

## Project Structure

```
roman_wordle/
├── app.py            # Main Streamlit app and daily-word selection
├── build_words.py    # Regenerates frontend/words.js
├── frontend/
│   ├── index.html    # The game (HTML/CSS/JS custom component)
│   └── words.js      # Generated guess-validation dictionary
├── requirements.txt
├── .gitignore
└── README.md
```

### `app.py`

Contains the Streamlit page configuration, the daily-word selection function, and the full self-contained HTML/CSS/JavaScript Wordle game rendered inside an iframe via `st.iframe`.

### `secret_words.py`

A Python `set` named `KEYS` containing all candidate mystery words. Every word is 4–6 letters long and related to the Roman Space Telescope mission, its instruments, science goals, or the broader astronomy context. To add or remove words, simply edit this set.

---

## Guess validation

A guess is accepted if it appears in `frontend/words.js`, a generated set of
~28,000 four-to-six letter words. Validation is entirely local, so submitting a
guess makes no network request.

This replaced a lookup against `api.dictionaryapi.dev`. That service began
returning HTTP 522 after ~20 seconds for any word its CDN had not cached —
including ordinary words like VENUS, METEOR and CRATER — which froze the game on
each guess and, because the error path failed open, silently accepted gibberish.

To rebuild the list, or after editing the `ASTRO_NAMES` supplement:

```bash
python3 build_words.py
```

The base corpus is `/usr/share/dict/words` (the `web2` list on macOS/BSD). It
contains no proper nouns, so `ASTRO_NAMES` in `build_words.py` supplies the
astronomy names — planets, moons, constellations, stars, missions, astronomers —
that players reasonably guess. The daily-word bank is merged in automatically.

---

## Installation & Running

**Requirements:** Python 3.9+

1. Clone the repository:

   ```bash
   git clone https://github.com/<your-username>/roman_wordle.git
   cd roman_wordle
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Launch the app:

   ```bash
   streamlit run app.py
   ```

   The app will open automatically in your browser at `http://localhost:8501`.

---

## Customizing the Word List

Open `secret_words.py` and add or remove entries from the `KEYS` set. Words must be:
- **Alphabetic only** (no numbers, hyphens, or spaces)
- **4–6 letters long** (shorter or longer words are silently ignored by the app)

---