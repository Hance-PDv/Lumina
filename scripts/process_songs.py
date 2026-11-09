import os
import json
import shutil
from mutagen import File
from mutagen.id3 import ID3, APIC
from mutagen.flac import FLAC, Picture
from PIL import Image
import io

INPUT_DIR = "songs_input"
TRACKS_DIR = "tracks"
ARTWORK_DIR = "artwork"
JSON_FILE = "songs.json"

os.makedirs(TRACKS_DIR, exist_ok=True)
os.makedirs(ARTWORK_DIR, exist_ok=True)

def load_existing_songs():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_songs(songs_list):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(songs_list, f, ensure_ascii=False, indent=4)

def extract_cover_art(audio, base_filename):
    cover_bytes = None
    
    if hasattr(audio, 'tags') and audio.tags:
        for tag in audio.tags.values():
            if isinstance(tag, APIC):
                cover_bytes = tag.data
                break
                
    if not cover_bytes and isinstance(audio, FLAC) and audio.pictures:
        cover_bytes = audio.pictures[0].data

    if cover_bytes:
        try:
            image = Image.open(io.BytesIO(cover_bytes))
            image = image.convert("RGB")
            cover_filename = f"{base_filename}.jpg"
            cover_path = os.path.join(ARTWORK_DIR, cover_filename)
            image.save(cover_path, "JPEG", quality=85)
            return f"artwork/{cover_filename}"
        except Exception as e:
            print(f"Error processing image for {base_filename}: {e}")
            
    return ""

def process():
    if not os.path.exists(INPUT_DIR):
        print("Input directory does not exist.")
        return

    songs = load_existing_songs()
    input_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(('.mp3', '.flac', '.m4a', '.wav'))]

    if not input_files:
        print("No new audio files to process.")
        return

    for file_name in input_files:
        input_path = os.path.join(INPUT_DIR, file_name)
        base_name = os.path.splitext(file_name)[0]
        
        try:
            audio = File(input_path)
            
            title = base_name
            artist = "Unknown Artist"
            album = "Unknown Album"
            duration_ms = 0

            if audio is not None:
                if audio.info and hasattr(audio.info, 'length'):
                    duration_ms = int(audio.info.length * 1000)
                
                if hasattr(audio, 'tags') and audio.tags:
                    tags = audio.tags
                    if 'TIT2' in tags: title = str(tags['TIT2'])
                    elif 'title' in tags: title = str(tags['title'][0])
                    
                    if 'TPE1' in tags: artist = str(tags['TPE1'])
                    elif 'artist' in tags: artist = str(tags['artist'][0])
                    
                    if 'TALB' in tags: album = str(tags['TALB'])
                    elif 'album' in tags: album = str(tags['album'][0])

            artwork_url = extract_cover_art(audio, base_name)

            target_track_filename = f"{base_name}{os.path.splitext(file_name)[1]}"
            target_track_path = os.path.join(TRACKS_DIR, target_track_filename)
            shutil.move(input_path, target_track_path)
            track_url = f"tracks/{target_track_filename}"

            song_entry = {
                "id": str(len(songs) + 1),
                "title": title,
                "artist": artist,
                "album": album,
                "duration": duration_ms,
                "path": track_url,
                "artwork": artwork_url
            }

            existing_index = next((i for i, s in enumerate(songs) if s.get("path") == track_url), -1)
            if existing_index != -1:
                songs[existing_index] = song_entry
            else:
                songs.append(song_entry)

            print(f"Successfully processed: {title} - {artist}")

        except Exception as e:
            print(f"Error processing file {file_name}: {e}")

    save_songs(songs)

if __name__ == "__main__":
    process()
