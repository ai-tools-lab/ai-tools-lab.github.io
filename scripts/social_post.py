#!/usr/bin/env python3
"""
SNS Auto-Post Generator for AI Tools Lab Blog
Generates Twitter/X and Reddit post texts from article metadata.
Output: social_posts/<slug>.json per article + social_posts/all_posts.json combined.

Usage:
    python3 scripts/social_post.py
"""

import json
import os
import re
from pathlib import Path

BASE_URL = "https://ai-tools-lab.github.io/posts"

# Tag → subreddit mapping
SUBREDDIT_MAP = {
    "AI Agents": ["r/artificial", "r/ChatGPT", "r/productivity"],
    "AI Coding Tools": ["r/programming", "r/learnprogramming", "r/ChatGPTCoding"],
    "AI Automation": ["r/artificial", "r/automation", "r/smallbusiness"],
    "Business Productivity": ["r/productivity", "r/Entrepreneur", "r/smallbusiness"],
    "productivity": ["r/productivity", "r/getdisciplined"],
    "collaboration": ["r/productivity", "r/remotework"],
    "tool-reviews": ["r/artificial", "r/SaaS"],
    "comparison": ["r/artificial", "r/productivity"],
    "getting-started": ["r/learnprogramming", "r/ChatGPT"],
    "how-to": ["r/artificial", "r/productivity"],
    "remote-work": ["r/remotework", "r/digitalnomad"],
    "case-studies": ["r/artificial", "r/Entrepreneur"],
    "ROI": ["r/smallbusiness", "r/Entrepreneur"],
}

# Tag → hashtag mapping
HASHTAG_MAP = {
    "AI Agents": "#AIAgents",
    "AI Coding Tools": "#AICoding",
    "AI Automation": "#AIAutomation",
    "Business Productivity": "#Productivity",
    "productivity": "#Productivity",
    "collaboration": "#TeamWork",
    "tool-reviews": "#ToolReview",
    "comparison": "#AIvsTraditional",
    "getting-started": "#GettingStarted",
    "how-to": "#HowTo",
    "remote-work": "#RemoteWork",
    "meetings": "#Meetings",
    "pair-programming": "#PairProgramming",
    "CI-CD": "#CICD",
    "developer-experience": "#DevEx",
    "speed": "#ShipFaster",
    "strategies": "#Strategy",
    "tips": "#Tips",
    "overview": "#AITools",
    "new-releases": "#NewRelease",
    "industry-solutions": "#IndustryAI",
    "vertical-AI": "#VerticalAI",
    "workflow": "#Workflow",
    "operations": "#Operations",
    "leadership": "#Leadership",
    "team-efficiency": "#Efficiency",
    "tool-selection": "#ToolSelection",
    "strategy": "#Strategy",
    "project-management": "#ProjectManagement",
    "cross-functional": "#CrossFunctional",
    "async-work": "#AsyncWork",
    "personal-productivity": "#PersonalProductivity",
    "workplace": "#Workplace",
    "automation": "#Automation",
    "beginners": "#Beginners",
    "reviews": "#Review",
    "tools-guide": "#ToolsGuide",
    "business-productivity": "#BusinessAI",
}


def parse_articles(posts_dir: str) -> list[dict]:
    """Parse all markdown posts and extract frontmatter metadata."""
    articles = []
    for fname in sorted(os.listdir(posts_dir)):
        if not fname.endswith(".md"):
            continue
        with open(os.path.join(posts_dir, fname)) as f:
            text = f.read()

        title_m = re.search(r'title:\s*"(.+?)"', text)
        desc_m = re.search(r'description:\s*"(.+?)"', text)
        tags_m = re.search(r"tags:\s*\[(.+?)\]", text)

        title = title_m.group(1) if title_m else fname.replace(".md", "").replace("-", " ").title()
        description = desc_m.group(1) if desc_m else ""
        tags = [t.strip().strip('"') for t in tags_m.group(1).split(",")] if tags_m else []
        slug = fname.replace(".md", "")

        articles.append({
            "slug": slug,
            "title": title,
            "description": description,
            "tags": tags,
            "url": f"{BASE_URL}/{slug}/",
        })
    return articles


def generate_twitter_post(article: dict) -> dict:
    """Generate a Twitter/X post (≤280 chars) with hashtags."""
    url = article["url"]
    tags = article["tags"]

    # Pick up to 3 hashtags
    hashtags_list = []
    seen = set()
    for tag in tags:
        ht = HASHTAG_MAP.get(tag)
        if ht and ht not in seen:
            hashtags_list.append(ht)
            seen.add(ht)
        if len(hashtags_list) >= 3:
            break
    # Always include #AI if not present
    if not any("AI" in h for h in hashtags_list):
        hashtags_list.append("#AI")
    hashtags = " ".join(hashtags_list)

    # Build tweet: title + description snippet + url + hashtags
    # Budget: 280 chars total. URL = ~23 chars (t.co). hashtags vary.
    suffix = f"\n\n{url}\n\n{hashtags}"
    max_body = 280 - len(suffix) - 2  # 2 for \n\n between title and desc

    body = article["title"]
    desc = article["description"]
    if desc and len(body) + 3 + len(desc) <= max_body:
        body = f"{body}\n\n{desc}"
    elif desc:
        # Truncate description to fit
        avail = max_body - len(body) - 5  # 5 for \n\n...
        if avail > 30:
            body = f"{body}\n\n{desc[:avail]}..."

    tweet = f"{body}{suffix}"

    # Safety truncate
    if len(tweet) > 280:
        tweet = tweet[:277] + "..."

    return {"text": tweet, "char_count": len(tweet)}


def generate_reddit_post(article: dict) -> dict:
    """Generate Reddit post data with subreddit suggestions."""
    tags = article["tags"]

    subreddits = []
    seen = set()
    for tag in tags:
        for sr in SUBREDDIT_MAP.get(tag, []):
            if sr not in seen:
                subreddits.append(sr)
                seen.add(sr)
    if not subreddits:
        subreddits = ["r/artificial", "r/productivity"]
    # Keep top 3 most relevant
    subreddits = subreddits[:3]

    return {
        "title": article["title"],
        "url": article["url"],
        "suggested_subreddits": subreddits,
        "body": f"I wrote about {article['description'].lower().rstrip('.')}\n\nFull article: {article['url']}",
    }


def main():
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent
    posts_dir = project_dir / "content" / "posts"
    output_dir = project_dir / "social_posts"
    output_dir.mkdir(exist_ok=True)

    articles = parse_articles(str(posts_dir))
    print(f"Found {len(articles)} articles")

    all_posts = []
    for article in articles:
        twitter = generate_twitter_post(article)
        reddit = generate_reddit_post(article)

        post_data = {
            "slug": article["slug"],
            "title": article["title"],
            "url": article["url"],
            "twitter": twitter,
            "reddit": reddit,
        }
        all_posts.append(post_data)

        # Save individual file
        out_file = output_dir / f"{article['slug']}.json"
        with open(out_file, "w") as f:
            json.dump(post_data, f, indent=2, ensure_ascii=False)

    # Save combined file
    combined_file = output_dir / "all_posts.json"
    with open(combined_file, "w") as f:
        json.dump(all_posts, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(all_posts)} social media posts in {output_dir}/")
    print(f"Combined output: {combined_file}")

    # Print sample
    if all_posts:
        sample = all_posts[0]
        print(f"\n--- Sample (Twitter) ---\n{sample['twitter']['text']}")
        print(f"\n--- Sample (Reddit) ---")
        print(f"Subreddits: {', '.join(sample['reddit']['suggested_subreddits'])}")
        print(f"Title: {sample['reddit']['title']}")


if __name__ == "__main__":
    main()
