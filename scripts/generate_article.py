#!/usr/bin/env python3
"""
AI Tools Blog — Article Generator
Generates SEO-optimized blog posts using OpenAI API and saves as Hugo markdown.
"""

import os
import sys
import json
import re
import datetime
import subprocess
from pathlib import Path

try:
    import openai
except ImportError:
    print("Installing openai package...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openai", "-q"])
    import openai

BLOG_DIR = Path(__file__).parent.parent
CONTENT_DIR = BLOG_DIR / "content" / "posts"

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
"""

TOPIC_GENERATION_PROMPT = """Generate 5 blog post topics about AI tools and productivity that would rank well in search.
For each topic provide:
1. Title (SEO optimized, 50-60 chars)
2. Target keyword
3. Search intent (informational/commercial/transactional)

Format as JSON array:
[{"title": "...", "keyword": "...", "intent": "..."}]
Only output the JSON, nothing else."""

def get_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set")
        sys.exit(1)
    return openai.OpenAI(api_key=api_key)

def generate_topics(client) -> list:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You generate blog topic ideas as JSON."},
            {"role": "user", "content": TOPIC_GENERATION_PROMPT}
        ],
        temperature=0.8,
    )
    text = resp.choices[0].message.content.strip()
    # Extract JSON from response
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(text)

def generate_article(client, topic: dict) -> str:
    prompt = f"""Write a blog post with the following details:
Title: {topic['title']}
Target keyword: {topic['keyword']}
Search intent: {topic['intent']}

Write the full article body (no frontmatter). Start with an engaging intro paragraph."""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()

def save_article(topic: dict, content: str) -> Path:
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(topic['title'])
    date = datetime.date.today().isoformat()
    
    frontmatter = f"""---
title: "{topic['title']}"
date: {date}
draft: false
tags: ["ai-tools", "productivity", "{topic['keyword'].replace(' ', '-')}"]
keywords: ["{topic['keyword']}"]
description: "{topic['title']} — a comprehensive guide from AI Tools Lab."
---

"""
    filepath = CONTENT_DIR / f"{slug}.md"
    filepath.write_text(frontmatter + content, encoding="utf-8")
    return filepath

def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    client = get_client()
    
    print(f"Generating {count} topics...")
    topics = generate_topics(client)[:count]
    
    for i, topic in enumerate(topics, 1):
        print(f"\n[{i}/{count}] Writing: {topic['title']}")
        content = generate_article(client, topic)
        path = save_article(topic, content)
        print(f"  → Saved: {path.name}")
    
    print(f"\nDone! {count} articles generated in {CONTENT_DIR}")

if __name__ == "__main__":
    main()
