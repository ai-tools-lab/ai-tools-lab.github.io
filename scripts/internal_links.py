#!/usr/bin/env python3
"""Add related articles section to blog posts based on shared tags."""

import re
import sys
from pathlib import Path
from collections import defaultdict

POSTS_DIR = Path(__file__).parent.parent / "content" / "posts"
RELATED_HEADER = "## 関連記事"


def parse_frontmatter(text):
    """Extract frontmatter dict-like info and body."""
    m = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}, text, ""
    fm_text = m.group(1)
    body = text[m.end():]
    frontmatter_raw = m.group(0)

    # Extract tags
    tags_match = re.search(r'tags:\s*\[([^\]]*)\]', fm_text)
    tags = []
    if tags_match:
        tags = [t.strip().strip('"').strip("'") for t in tags_match.group(1).split(",") if t.strip()]

    # Extract title
    title_match = re.search(r'title:\s*"([^"]*)"', fm_text)
    title = title_match.group(1) if title_match else ""

    return {"tags": tags, "title": title}, body, frontmatter_raw


def build_index(posts_dir):
    """Build index of all posts with their tags and titles."""
    index = []
    for f in sorted(posts_dir.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        meta, body, fm_raw = parse_frontmatter(text)
        index.append({
            "path": f,
            "filename": f.name,
            "slug": f.stem,
            "tags": [t.lower() for t in meta.get("tags", [])],
            "title": meta.get("title", f.stem),
            "body": body,
            "fm_raw": fm_raw,
            "full_text": text,
        })
    return index


def find_related(current, all_posts, max_results=3):
    """Find related posts by shared tags."""
    current_tags = set(current["tags"])
    if not current_tags:
        return []

    scored = []
    for post in all_posts:
        if post["filename"] == current["filename"]:
            continue
        shared = current_tags & set(post["tags"])
        if shared:
            scored.append((len(shared), post))

    scored.sort(key=lambda x: -x[0])
    return [p for _, p in scored[:max_results]]


def has_related_section(body):
    return RELATED_HEADER in body or "## Related" in body or "## 関連記事" in body


def add_related_section(post, related):
    """Add related articles section to post."""
    lines = [f"\n\n{RELATED_HEADER}\n"]
    for r in related:
        slug = r["slug"]
        title = r["title"]
        lines.append(f"- [{title}](/posts/{slug}/)")
    return "\n".join(lines) + "\n"


def main():
    index = build_index(POSTS_DIR)
    if not index:
        print("No posts found.")
        return

    modified = 0
    for post in index:
        if has_related_section(post["body"]):
            print(f"  ⏭️  {post['filename']} (already has related section)")
            continue

        related = find_related(post, index)
        if not related:
            print(f"  ⏭️  {post['filename']} (no related posts found)")
            continue

        section = add_related_section(post, related)
        new_text = post["full_text"].rstrip() + section
        post["path"].write_text(new_text, encoding="utf-8")
        print(f"  ✅ {post['filename']} (+{len(related)} related)")
        modified += 1

    print(f"\nDone: {modified}/{len(index)} posts modified.")


if __name__ == "__main__":
    main()
