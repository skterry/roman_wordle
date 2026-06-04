# Roman Wordle

<a href="https://romanwordle.streamlit.app/" target="_blank">
  <img src="https://img.shields.io/badge/Play%20Now-brightgreen?style=for-the-badge" alt="Play Now!"/>
</a>

A daily word-guessing game themed around the [Nancy Grace Roman Space Telescope](https://roman.gsfc.nasa.gov/), built with [Streamlit](https://streamlit.io/).

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
├── app.py            # Main Streamlit app and game logic
├── secret_words.py   # Set of themed mystery words (4–6 letters)
├── requirements.txt
├── .gitignore
└── README.md
```

### `app.py`

Contains the Streamlit page configuration, the daily-word selection function, and the full self-contained HTML/CSS/JavaScript Wordle game rendered inside an iframe via `st.iframe`.

### `secret_words.py`

A Python `set` named `KEYS` containing all candidate mystery words. Every word is 4–6 letters long and related to the Roman Space Telescope mission, its instruments, science goals, or the broader astronomy context. To add or remove words, simply edit this set.

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