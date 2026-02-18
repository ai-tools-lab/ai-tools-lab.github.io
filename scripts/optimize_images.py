#!/usr/bin/env python3
"""Convert PNG images to WebP and update markdown references."""

import os
import glob
import re

try:
    from PIL import Image
except ImportError:
    print("Installing Pillow...")
    os.system("pip3 install Pillow")
    from PIL import Image

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "images", "posts")
CONTENT_DIR = os.path.join(os.path.dirname(__file__), "..", "content")

def convert_images():
    png_files = glob.glob(os.path.join(IMAGES_DIR, "*.png"))
    print(f"Found {len(png_files)} PNG images to convert")
    
    total_saved = 0
    for png_path in png_files:
        webp_path = png_path.rsplit(".", 1)[0] + ".webp"
        
        img = Image.open(png_path)
        img.save(webp_path, "WEBP", quality=85)
        
        old_size = os.path.getsize(png_path)
        new_size = os.path.getsize(webp_path)
        saved = old_size - new_size
        total_saved += saved
        
        print(f"  {os.path.basename(png_path)}: {old_size//1024}KB → {new_size//1024}KB (saved {saved//1024}KB)")
        
        # Remove original PNG
        os.remove(png_path)
    
    print(f"\nTotal saved: {total_saved // 1024}KB ({total_saved // (1024*1024)}MB)")
    return len(png_files)

def update_markdown_refs():
    md_files = glob.glob(os.path.join(CONTENT_DIR, "**", "*.md"), recursive=True)
    updated = 0
    
    for md_path in md_files:
        with open(md_path, "r") as f:
            content = f.read()
        
        new_content = content.replace(".png", ".webp")
        
        if new_content != content:
            with open(md_path, "w") as f:
                f.write(new_content)
            updated += 1
            print(f"  Updated: {os.path.basename(md_path)}")
    
    print(f"Updated {updated} markdown files")

if __name__ == "__main__":
    print("=== Image Optimization ===")
    count = convert_images()
    print(f"\n=== Updating Markdown References ===")
    update_markdown_refs()
    print(f"\nDone! Converted {count} images to WebP.")
