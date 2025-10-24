from pydub.generators import Sine
from pydub import AudioSegment
import os

# === Απόλυτο path ===
base_dir = os.path.join(os.path.dirname(__file__), "static", "sounds")
os.makedirs(base_dir, exist_ok=True)

print(f"🎵 Δημιουργία αρχείων ήχου στον φάκελο: {base_dir}")

# alert.mp3 - σύντομο ping
alert = Sine(880).to_audio_segment(duration=250).fade_out(100)
alert.export(os.path.join(base_dir, "alert.mp3"), format="mp3")

# smartmoney.mp3 - βαθύς τόνος
smartmoney = Sine(440).to_audio_segment(duration=400).fade_out(200)
smartmoney.export(os.path.join(base_dir, "smartmoney.mp3"), format="mp3")

# goal.wav - ανεβοκατεβαίνει
goal = Sine(523).to_audio_segment(duration=200) + Sine(784).to_audio_segment(duration=300)
goal = goal.fade_out(150)
goal.export(os.path.join(base_dir, "goal.wav"), format="wav")

print("✅ 3 sound files created successfully!")
