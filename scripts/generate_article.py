#!/usr/bin/env python3
"""
AI Tools Blog — Article Generator v2
Generates SEO-optimized blog posts with DALL-E images and Mermaid diagrams.
"""

import os
import sys
import json
import re
import datetime
import subprocess
import urllib.request
from pathlib import Path

try:
    import openai
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openai", "-q"])
    import openai

BLOG_DIR = Path(__file__).parent.parent
CONTENT_DIR = BLOG_DIR / "content" / "posts"
IMAGES_DIR = BLOG_DIR / "static" / "images" / "posts"

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:80].strip('-')

SYSTEM_PROMPT = """You are an expert tech blogger writing for "AI Tools Lab".
Write engaging, SEO-optimized blog posts about AI tools and productivity.

Rules:
- Write in a conversational but authoritative tone
- Include practical examples and use cases
- Add pros/cons when reviewing tools
- Include a clear call-to-action
- Use headers (H2, H3) for structure
- Aim for 1500-2000 words
- Include relevant keywords naturally
- Do NOT use markdown frontmatter — just the article body starting with intro paragraph
- Include ONE Mermaid diagram where appropriate (workflow, comparison, decision tree)
  Format: ```mermaid\\n...\\n```
- Include a comparison table in HTML format if reviewing multiple tools
- Write a compelling meta description (under 160 chars) as the FIRST line, prefixed with META:
"""

TOPIC_GENERATION_PROMPT = """Generate 10 unique blog post topics about AI tools and productivity that would rank well in search in 2026.
Focus on current trends: AI agents, AI coding tools, AI automation, AI for business.

For each topic provide:
1. Title (SEO optimized, 50-60 chars)
2. Target keyword
3. Search intent (informational/commercial/transactional)
4. Image prompt (for DALL-E, describe a clean tech illustration, flat design, no text)

Format as JSON array:
[{"title": "...", "keyword": "...", "intent": "...", "image_prompt": "..."}]
Only output the JSON, nothing else."""

def get_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set")
        sys.exit(1)
    return openai.OpenAI(api_key=api_key)

def generate_topics(client, count=5) -> list:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You generate blog topic ideas as JSON."},
            {"role": "user", "content": TOPIC_GENERATION_PROMPT}
        ],
        temperature=0.8,
    )
    text = resp.choices[0].message.content.strip()
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        return json.loads(match.group())[:count]
    return json.loads(text)[:count]

def generate_image(client, prompt: str, slug: str) -> str:
    """Generate a DALL-E image and save it. Returns the relative path for Hugo."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    try:
        resp = client.images.generate(
            model="dall-e-3",
            prompt=f"Clean, modern flat design tech illustration: {prompt}. Minimal, professional, no text, vibrant colors, white background.",
            size="1792x1024",
            quality="standard",
            n=1,
        )
        image_url = resp.data[0].url
        image_path = IMAGES_DIR / f"{slug}.png"
        urllib.request.urlretrieve(image_url, str(image_path))
        return f"/images/posts/{slug}.png"
    except Exception as e:
        print(f"  ⚠ Image generation failed: {e}")
        return ""

def generate_article(client, topic: dict) -> tuple:
    """Returns (meta_description, article_body)"""
    prompt = f"""Write a blog post with the following details:
Title: {topic['title']}
Target keyword: {topic['keyword']}
Search intent: {topic['intent']}

Requirements:
- Start with META: line (meta description, <160 chars)
- Then write the full article body
- Include one Mermaid diagram (```mermaid block)
- If comparing tools, include an HTML comparison table
- End with a strong call-to-action"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    content = resp.choices[0].message.content.strip()
    
    # Extract meta description
    meta = ""
    lines = content.split('\n')
    if lines[0].startswith('META:'):
        meta = lines[0].replace('META:', '').strip()
        content = '\n'.join(lines[1:]).strip()
    
    return meta, content

def save_article(topic: dict, meta: str, content: str, image_path: str) -> Path:
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(topic['title'])
    date = datetime.date.today().isoformat()
    
    description = meta if meta else f"{topic['title']} — a comprehensive guide from AI Tools Lab."
    
    cover = ""
    if image_path:
        cover = f"""
[params.cover]
  image = "{image_path}"
  alt = "{topic['title']}"
  caption = ""
  relative = false"""
    
    frontmatter = f"""---
title: "{topic['title']}"
date: {date}
draft: false
tags: ["ai-tools", "productivity", "{topic['keyword'].replace(' ', '-')}"]
keywords: ["{topic['keyword']}"]
description: "{description}"
{cover}
---

"""
    filepath = CONTENT_DIR / f"{slug}.md"
    filepath.write_text(frontmatter + content, encoding="utf-8")
    return filepath

def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    client = get_client()
    
    print(f"Generating {count} topics...")
    topics = generate_topics(client, count)
    
    for i, topic in enumerate(topics, 1):
        print(f"\n[{i}/{count}] Writing: {topic['title']}")
        
        # Generate image
        slug = slugify(topic['title'])
        image_prompt = topic.get('image_prompt', topic['title'])
        print(f"  → Generating image...")
        image_path = generate_image(client, image_prompt, slug)
        if image_path:
            print(f"  → Image saved: {image_path}")
        
        # Generate article
        print(f"  → Writing article...")
        meta, content = generate_article(client, topic)
        path = save_article(topic, meta, content, image_path)
        print(f"  → Article saved: {path.name}")
    
    print(f"\nDone! {count} articles with images generated in {CONTENT_DIR}")

if __name__ == "__main__":
    main()
