"""
Download test videos for Patient Monitoring System.
Provides sample videos for testing fall detection, activity monitoring, etc.
"""

import requests
import os
from pathlib import Path
from tqdm import tqdm


def download_file(url, filename):
    """Download file with progress bar"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as file, tqdm(
        desc=filename,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as progress_bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            progress_bar.update(size)


def download_test_videos():
    """Download test videos from public sources"""
    
    # Create test_videos directory
    test_dir = Path('test_videos')
    test_dir.mkdir(exist_ok=True)
    
    print("="*80)
    print("Downloading Test Videos for Patient Monitoring System")
    print("="*80)
    print()
    
    # List of test videos (using public domain / creative commons videos)
    test_videos = [
        {
            "name": "person_walking.mp4",
            "url": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
            "description": "Sample video for person detection and tracking",
        },
        # Add more test videos here
    ]
    
    print("Note: For best results, use your own test videos with:")
    print("  - Clear view of person(s)")
    print("  - Good lighting")
    print("  - Minimal camera movement")
    print("  - Activities: walking, sitting, lying down, etc.")
    print()
    
    # Recommended test video sources
    print("Recommended Test Video Sources:")
    print()
    print("1. Pexels (Free stock videos)")
    print("   https://www.pexels.com/search/videos/elderly%20care/")
    print("   https://www.pexels.com/search/videos/hospital%20patient/")
    print()
    print("2. Pixabay (Free videos)")
    print("   https://pixabay.com/videos/search/elderly/")
    print("   https://pixabay.com/videos/search/patient/")
    print()
    print("3. YouTube (with proper permissions)")
    print("   Search for: 'fall detection test video'")
    print("   Use youtube-dl to download: youtube-dl <video-url>")
    print()
    print("4. Create Your Own Test Videos:")
    print("   - Record yourself performing activities")
    print("   - Simulate fall scenarios (safely!)")
    print("   - Test different lighting conditions")
    print("   - Test different camera angles")
    print()
    
    # Specific test scenarios to record
    print("Recommended Test Scenarios:")
    print()
    print("✓ Fall Detection:")
    print("  - Person standing, then slowly lowering to ground")
    print("  - Person sitting on bed, then lying down")
    print("  - Person walking, then crouching")
    print()
    print("✓ Bed Exit Detection:")
    print("  - Person lying in bed")
    print("  - Person sitting up in bed")
    print("  - Person standing from bed")
    print("  - Person walking away from bed")
    print()
    print("✓ Vital Signs (rPPG):")
    print("  - Close-up of face (good lighting)")
    print("  - Person sitting still for 30+ seconds")
    print("  - Minimal head movement")
    print()
    print("✓ Emotion Detection:")
    print("  - Clear frontal face view")
    print("  - Various facial expressions")
    print("  - Good lighting on face")
    print()
    print("✓ Immobility Detection:")
    print("  - Person lying still for extended period")
    print("  - Occasional small movements")
    print()
    
    # Sample video download commands
    print("="*80)
    print("Quick Download Commands (requires youtube-dl):")
    print("="*80)
    print()
    print("# Install youtube-dl")
    print("pip install youtube-dl")
    print()
    print("# Download a video")
    print("youtube-dl -f 'best[height<=720]' -o 'test_videos/%(title)s.%(ext)s' <VIDEO_URL>")
    print()
    
    # Create sample video info file
    info_file = test_dir / "README.txt"
    with open(info_file, 'w') as f:
        f.write("Test Videos Directory\n")
        f.write("="*50 + "\n\n")
        f.write("Place your test videos here.\n\n")
        f.write("Recommended video specifications:\n")
        f.write("- Format: MP4, AVI, MOV\n")
        f.write("- Resolution: 720p or 1080p\n")
        f.write("- Duration: 30 seconds to 5 minutes\n")
        f.write("- FPS: 24-30\n\n")
        f.write("Test scenarios:\n")
        f.write("1. Fall detection\n")
        f.write("2. Bed exit monitoring\n")
        f.write("3. Vital signs extraction\n")
        f.write("4. Emotion detection\n")
        f.write("5. Immobility monitoring\n")
    
    print(f"✓ Created test_videos directory: {test_dir.absolute()}")
    print(f"✓ Created README: {info_file.absolute()}")
    print()
    print("="*80)
    print("Setup Complete!")
    print("="*80)
    print()
    print("Next steps:")
    print("1. Download or record test videos")
    print("2. Place videos in test_videos/ directory")
    print("3. Run: python main.py --input test_videos/your_video.mp4 --visualize")
    print()


if __name__ == "__main__":
    download_test_videos()
