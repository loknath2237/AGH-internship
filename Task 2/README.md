# BoxBot

A talking cardboard-box avatar (face, FRAGILE sticker, criss-crossed tape) that answers
any question, shows 12 facial expressions and small animations, and speaks aloud.

- Agent: Claude (via the Anthropic API) answers and picks an emotion
- Whisper: speech to text (tap the mic)
- gTTS: text to speech, with the mouth lip-synced to the audio

## Setup

1. Install ffmpeg (Whisper needs it): `sudo apt install ffmpeg` or `brew install ffmpeg`
   (Windows: `choco install ffmpeg`)
2. Install packages: `pip install -r requirements.txt`
3. Set your key:
   - Mac/Linux: `export ANTHROPIC_API_KEY=your_key`
   - Windows (PowerShell): `$env:ANTHROPIC_API_KEY="your_key"`
4. Run: `python app.py`
5. Open http://127.0.0.1:8000 (use this address, so the browser allows the microphone)

Optional settings: `WHISPER_MODEL` (tiny, base, small), `CLAUDE_MODEL`.

## Using it

- Type a question and press Enter, or tap the mic, speak, and tap it again to stop.
- Click the box to poke it. Poke it many times and it gets angry.
- The small chips under the box preview each expression.
- Move the mouse and the eyes follow it. Leave it alone and it winks, then falls asleep.

## Expressions

neutral, happy, excited, laugh, sad, surprised, thinking, angry, sleepy, love, confused, wink
(plus "listening" while you record).

To change the look, edit the SVG in `static/index.html`. To add an expression, add a line
to the `EMO` table in the same file and add its name to `EMOTIONS` in `app.py`.

gTTS needs internet access. Without an API key, BoxBot only gives a few built-in replies.
