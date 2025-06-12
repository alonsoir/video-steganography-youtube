import sys
print("Python path:", sys.path)
print("Trying imports...")

try:
    import moviepy
    print("✓ moviepy imported")
    print("moviepy version:", moviepy.__version__)
    print("moviepy location:", moviepy.__file__)
except Exception as e:
    print("✗ moviepy failed:", e)

try:
    from moviepy.editor import VideoFileClip
    print("✓ VideoFileClip imported")
except Exception as e:
    print("✗ VideoFileClip failed:", e)