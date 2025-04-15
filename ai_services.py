"""
AI Services for Reddit Post Fetcher

This module provides AI-powered features for Reddit posts:
- Post summarization (TL;DR generation)

It uses OpenAI's API to process and analyze post content.
"""

import os
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ai_services")

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

async def generate_tldr(title: str, text: str) -> str:
    """
    Generate a TL;DR summary of a Reddit post using OpenAI.

    Args:
        title: The post title
        text: The post text content

    Returns:
        A slightly verbose summary of the post
    """

    # Handle empty content
    if not text or text.strip() == "":
        return "No content to summarize."

    # Truncate text if it's too long
    if len(text) > 6000:
        text = text[:6000] + "..."

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that creates concise TL;DR summaries of Reddit posts. Keep your summary to 4 sentences.",
                },
                {
                    "role": "user",
                    "content": f"Title: {title}\n\nContent: {text}\n\nWrite a TL;DR:",
                },
            ],
            max_tokens=500,
            temperature=0.4,
        )

        summary = response.choices[0].message.content.strip()

        # Remove "TL;DR:" prefix if the model included it
        if summary.lower().startswith("tl;dr:"):
            summary = summary[6:].strip()

        return summary

    except Exception as e:
        logger.error(f"Error generating TL;DR: {e}")
        return "Unable to generate summary."


async def process_post_batch(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a batch of Reddit posts to add AI-enhanced data.

    Args:
        posts: List of post dictionaries

    Returns:
        The same list with added AI fields (tldr)
    """
    enhanced_posts = []

    for post in posts:
        # Skip processing if the post is already enhanced
        if "ai_processed" in post and post["ai_processed"]:
            enhanced_posts.append(post)
            continue

        # Get the text to analyze (use selftext if available, otherwise title)
        text_to_analyze = post.get("selftext", "") or post.get("title", "")
        title = post.get("title", "")

        # Generate TL;DR
        tldr = await generate_tldr(title, text_to_analyze)

        # Add AI data to the post
        post["tldr"] = tldr
        post["ai_processed"] = True

        enhanced_posts.append(post)

    return enhanced_posts
