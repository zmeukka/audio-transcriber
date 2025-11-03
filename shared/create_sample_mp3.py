from gtts import gTTS
import os

def create_sample_mp3(text, filename):
    tts = gTTS(text=text, lang='ru')
    tts.save(filename)
    print(f"Аудиофайл '{filename}' успешно создан.")

if __name__ == "__main__":
    create_sample_mp3("Ты сакс", "sample.mp3")

