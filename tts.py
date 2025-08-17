import os
import subprocess
import tempfile
import pygame
from gtts import gTTS
import io

# Initialize pygame mixer for audio playback
pygame.mixer.init()

def va_speak(text):
    """
    Text-to-speech function for macOS using multiple fallback methods
    """
    try:
        # Method 1: Try macOS built-in 'say' command (fastest, but English only for good quality)
        if is_english_text(text):
            subprocess.run(['say', text], check=True)
        else:
            # Method 2: Use Google TTS for Russian text
            speak_with_gtts(text)
    except Exception as e:
        print(f"TTS Error: {e}")
        try:
            # Fallback: Try 'say' command anyway
            subprocess.run(['say', text])
        except:
            print("All TTS methods failed")

def is_english_text(text):
    """
    Simple check if text is primarily English
    """
    english_chars = sum(1 for c in text if c.isascii() and c.isalpha())
    total_chars = sum(1 for c in text if c.isalpha())
    
    if total_chars == 0:
        return True
    
    return (english_chars / total_chars) > 0.7

def speak_with_gtts(text, lang='ru'):
    """
    Use Google Text-to-Speech for non-English text
    """
    try:
        # Create TTS object
        tts = gTTS(text=text, lang=lang, slow=False)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tmp_filename = tmp_file.name
            tts.save(tmp_filename)
        
        # Play the audio file
        pygame.mixer.music.load(tmp_filename)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
        
        # Clean up temporary file
        os.unlink(tmp_filename)
        
    except Exception as e:
        print(f"GTTS Error: {e}")
        # Final fallback to system 'say' command
        subprocess.run(['say', text])

def speak_with_silero_fallback(text):
    """
    Alternative Silero implementation with better error handling
    """
    try:
        import torch
        import soundfile as sf
        import tempfile
        
        # Try to load Silero with specific settings for macOS
        device = torch.device('cpu')  # Force CPU usage
        torch.set_num_threads(4)
        
        # Load model with explicit CPU device
        model, _ = torch.hub.load(
            repo_or_dir='snakers4/silero-models',
            model='silero_tts',
            language='ru',
            speaker='aidar',
            force_reload=False,
            device=device
        )
        
        # Generate audio
        audio = model.apply_tts(
            text=text,
            speaker='aidar',
            sample_rate=48000,
            put_accent=True,
            put_yo=True
        )
        
        # Save to temporary file and play
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_filename = tmp_file.name
            sf.write(tmp_filename, audio.numpy(), 48000)
        
        # Play with pygame
        sound = pygame.mixer.Sound(tmp_filename)
        sound.play()
        
        # Wait for playback to finish
        while pygame.mixer.get_busy():
            pygame.time.wait(100)
        
        # Clean up
        os.unlink(tmp_filename)
        
    except Exception as e:
        print(f"Silero fallback failed: {e}")
        # Fall back to GTTS
        speak_with_gtts(text)

# Alternative: Simple TTS using macOS 'say' with Russian voice
def speak_with_say_russian(text):
    """
    Use macOS 'say' command with Russian voice
    """
    try:
        # Try to use Russian voice if available
        result = subprocess.run(
            ['say', '-v', 'Milena', text],  # Milena is Russian voice on macOS
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # Fallback to default voice
            subprocess.run(['say', text])
            
    except Exception as e:
        print(f"Say command failed: {e}")

# Test function
def test_tts():
    """
    Test TTS functionality
    """
    print("Testing TTS...")
    va_speak("Привет, я Джарвис!")
    va_speak("Hello, I am Jarvis!")
    print("TTS test complete")

if __name__ == "__main__":
    test_tts()