#!/usr/bin/env python3
"""Insert affiliate links for AI tool names in blog posts.

- Detects AI tool names in markdown content
- Links only the first occurrence per article
- Skips text already inside a markdown link
- Config driven via affiliate_config.json
"""

import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "affiliate_config.json"
POSTS_DIR = SCRIPT_DIR.parent / "content" / "posts"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def split_frontmatter(text):
    """Split markdown into (frontmatter, body). Frontmatter includes delimiters."""
    m = re.match(r"(---\n.*?\n---\n)", text, re.DOTALL)
    if m:
        return m.group(1), text[m.end():]
    return "", text


def insert_links(body, tools):
    """Insert affiliate links for first occurrence of each tool name."""
    linked = set()

    for tool_name in sorted(tools.keys(), key=len, reverse=True):
        if tool_name in linked:
            continue

        url = tools[tool_name]
        # Pattern: match tool_name that is NOT already inside []() markdown link
        # We look for the tool name not preceded by [ and not inside [...](...) 
        pattern = re.compile(
            r'(?<!\[)'           # not preceded by [
            + re.escape(tool_name)
            + r'(?!\]\()'        # not followed by ](
            + r'(?![^[]*\]\()'   # not inside a [...] that's followed by (
        )

        # More robust: skip if inside any markdown link
        def replace_first(match):
            start = match.start()
            # Check if this occurrence is inside a markdown link [text](url)
            # Look backwards for an unmatched [
            before = body[:start]
            # Count unmatched [ that might contain us
            bracket_depth = 0
            for i in range(len(before) - 1, -1, -1):
                if before[i] == ']':
                    bracket_depth += 1
                elif before[i] == '[':
                    if bracket_depth > 0:
                        bracket_depth -= 1
                    else:
                        # We're inside a [ without matching ] -> inside a link text
                        return match.group(0)
                elif before[i] == '\n':
                    break
            return match.group(0)  # placeholder, actual replacement below

        # Simpler approach: find all occurrences, pick first one not inside a link
        found = False
        for match in pattern.finditer(body):
            start, end = match.start(), match.end()
            # Check not inside markdown link: look for pattern [...](...) encompassing this position
            line_start = body.rfind('\n', 0, start) + 1
            line_end = body.find('\n', end)
            if line_end == -1:
                line_end = len(body)
            line = body[line_start:line_end]
            offset_in_line = start - line_start

            # Check if tool name is already inside a markdown link in this line
            inside_link = False
            for lm in re.finditer(r'\[([^\]]*)\]\([^)]*\)', line):
                if lm.start() <= offset_in_line < lm.end():
                    inside_link = True
                    break

            # Also skip if inside an HTML <a> tag
            for lm in re.finditer(r'<a\s[^>]*>.*?</a>', line, re.IGNORECASE):
                if lm.start() <= offset_in_line < lm.end():
                    inside_link = True
                    break

            # Skip headings (lines starting with #)
            stripped_line = line.lstrip()
            if stripped_line.startswith('#'):
                continue

            if not inside_link:
                replacement = f"[{tool_name}]({url})"
                body = body[:start] + replacement + body[end:]
                linked.add(tool_name)
                found = True
                break

    return body


def process_file(filepath, tools):
    text = filepath.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    new_body = insert_links(body, tools)
    if new_body != body:
        filepath.write_text(frontmatter + new_body, encoding="utf-8")
        return True
    return False


def main():
    config = load_config()
    tools = config["tools"]

    posts = sorted(POSTS_DIR.glob("*.md"))
    if not posts:
        print("No posts found.")
        return

    modified = 0
    for post in posts:
        if process_file(post, tools):
            print(f"  ✅ {post.name}")
            modified += 1
        else:
            print(f"  ⏭️  {post.name} (no changes)")

    print(f"\nDone: {modified}/{len(posts)} posts modified.")


if __name__ == "__main__":
    main()
