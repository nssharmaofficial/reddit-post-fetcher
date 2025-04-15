"""
Reddit Post Fetcher

What this script does:
- Logs into Reddit
- Makes sure we don't hit Reddit's rate limits
- Grabs posts from subreddits
- Shows you the post title, author, and how many upvotes it got

How to use it:
    poetry run python reddit_fetcher.py [--subreddit SUBREDDIT] [--limit LIMIT]

    Examples:
    poetry run python reddit_fetcher.py
    poetry run python reddit_fetcher.py --subreddit AskReddit
    poetry run python reddit_fetcher.py --subreddit python --limit 10
"""

import asyncpraw
import asyncio
import os
import sys
import logging
import argparse
from aiolimiter import AsyncLimiter
from dotenv import load_dotenv
import time

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("reddit_fetcher")

# Reddit lets us make 60 requests per minute
# I'm setting it to 50 to be on the safe side 😊
rate_limiter = AsyncLimiter(50, 60)


def parse_arguments():
    """
    Grabs the command-line arguments you typed in.

    This sets up the parser so you can specify which subreddit you want
    and how many posts to get.

    Returns:
        The parsed arguments all nicely organized
    """
    parser = argparse.ArgumentParser(
        description="Fetch the latest posts from a specified subreddit",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--subreddit",
        type=str,
        default="python",
        help="Name of the subreddit to fetch posts from",
    )
    parser.add_argument(
        "--limit", type=int, default=5, help="Maximum number of posts to fetch"
    )
    return parser.parse_args()


async def load_reddit_credentials():
    """
    Gets your Reddit API credentials from your .env file.
    Returns:
        All your credentials in a neat little package

    Raises:
        SystemExit: If you forgot to add some credentials
    """
    load_dotenv()
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv(
        "REDDIT_USER_AGENT", f"python:reddit-fetcher:v0.1.0 (by /u/your_username)"
    )
    username = os.getenv("REDDIT_USERNAME")
    password = os.getenv("REDDIT_PASSWORD")

    if not all([client_id, client_secret, username, password]):
        logger.error("Reddit API credentials not found in .env file.")
        logger.error(
            "Please ensure REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, and REDDIT_PASSWORD are set."
        )
        sys.exit(1)

    return client_id, client_secret, user_agent, username, password


async def authenticate_reddit(client_id, client_secret, user_agent, username, password):
    """
    Logs into Reddit with your credentials.

    Args:
        client_id: Your Reddit app ID
        client_secret: Your Reddit app secret
        user_agent: What Reddit sees you as (like a browser fingerprint)
        username: Your Reddit username
        password: Your Reddit password

    Returns:
        A logged-in Reddit instance ready to use!

    Raises:
        SystemExit: If login fails (wrong password maybe?)
    """
    try:
        async with rate_limiter:
            reddit = asyncpraw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
                username=username,
                password=password,
            )
            # Double-check that we're actually logged in
            user = await reddit.user.me()
            logger.info(f"Yay! Successfully logged into Reddit as {user.name}.")
            return reddit
    except asyncpraw.exceptions.RedditAPIException as api_exception:
        for subexception in api_exception.items:
            logger.error(
                f"API Error: {subexception.error_type} - {subexception.message}"
            )
            if subexception.error_type in ["RATELIMIT", "QUOTA_FILLED"]:
                wait_time = extract_wait_time(subexception.message)
                logger.warning(
                    f"Oops, Reddit says we're going too fast! Wait for {wait_time} seconds and try again."
                )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Something went wrong logging into Reddit: {e}")
        sys.exit(1)


def extract_wait_time(message):
    """
    Figures out how long Reddit wants us to wait when we hit rate limits.

    Reddit's error messages usually tell you how long to wait before trying again.
    This function pulls that number out of the message.

    Args:
        message: The error message from Reddit

    Returns:
        How many seconds to wait. Defaults to 60 if we can't figure it out.
    """
    default_wait = 60
    try:
        # Reddit usually says something like "Try again in X minutes"
        if "minute" in message.lower():
            # Get the number before "minute"
            minutes = int(
                "".join(filter(str.isdigit, message.split("minute")[0].split()[-1]))
            )
            return minutes * 60
        elif "second" in message.lower():
            # Get the number before "second"
            seconds = int(
                "".join(filter(str.isdigit, message.split("second")[0].split()[-1]))
            )
            return seconds
        elif "hour" in message.lower():
            # Get the number before "hour"
            hours = int(
                "".join(filter(str.isdigit, message.split("hour")[0].split()[-1]))
            )
            return hours * 3600
    except (ValueError, IndexError):
        # If something goes wrong with parsing, just use the default
        pass
    return default_wait


async def fetch_latest_posts(reddit, subreddit_name, limit=5):
    """
    Grabs the newest posts from a subreddit.

    Args:
        reddit: Your logged-in Reddit instance
        subreddit_name: Which subreddit to grab posts from
        limit: How many posts you want (default is 5)

    Returns:
        A list of post objects. Returns an empty list if something goes wrong.
    """
    try:
        async with rate_limiter:
            subreddit = await reddit.subreddit(subreddit_name)
            logger.info(f"Grabbing the {limit} newest posts from r/{subreddit_name}...")

            latest_posts = []
            async for post in subreddit.new(limit=limit):
                latest_posts.append(post)
                await asyncio.sleep(0.1)

            if not latest_posts:
                logger.warning(f"Hmm, couldn't find any posts in r/{subreddit_name}.")
                return []
            logger.info(f"Got {len(latest_posts)} posts from r/{subreddit_name}! 🎉")
            return latest_posts
    except asyncpraw.exceptions.RedditAPIException as api_exception:
        for subexception in api_exception.items:
            logger.error(
                f"Reddit API got mad at us: {subexception.error_type} - {subexception.message}"
            )
            if subexception.error_type in ["RATELIMIT", "QUOTA_FILLED"]:
                wait_time = extract_wait_time(subexception.message)
                logger.warning(
                    f"We need to slow down! Reddit says wait {wait_time} seconds."
                )
        return []
    except Exception as e:
        logger.error(
            f"Oops! Something went wrong getting posts from r/{subreddit_name}: {e}"
        )
        logger.error("Double-check that the subreddit name is correct and exists.")
        return []


async def print_post_details(posts):
    """
    This shows you the title, who posted it, and how many upvotes it got.
    It handles weird cases like if the author deleted their account.

    Args:
        posts: The list of posts we grabbed
    """
    if not posts:
        return

    print("\n--- Latest Posts ---")
    for i, post in enumerate(posts, 1):
        # Safely handle potential missing authors (deleted accounts)
        try:
            author_name = (
                post.author.name
                if hasattr(post, "author") and post.author
                else "[deleted]"
            )
        except AttributeError:
            author_name = "[deleted]"

        print(f"Post #{i}")
        print(f"Title: {post.title}")
        print(f"Author: u/{author_name}")
        print(f"Upvotes: {post.score}")
        print("---")


async def main():
    """
    Main async function that orchestrates the Reddit post fetching process.

    This function:
    1. Loads credentials from environment variables
    2. Authenticates with the Reddit API
    3. Fetches the latest posts from a specified subreddit
    4. Prints the details of each post
    5. Properly cleans up resources
    6. Logs execution time
    """
    start_time = time.time()

    # Parse command-line arguments
    args = parse_arguments()

    # Load credentials and authenticate
    client_id, client_secret, user_agent, username, password = (
        await load_reddit_credentials()
    )
    reddit = await authenticate_reddit(
        client_id, client_secret, user_agent, username, password
    )

    # Get subreddit name and post limit from command-line arguments
    subreddit_to_fetch = args.subreddit
    post_limit = args.limit

    # Fetch and display posts
    latest_posts = await fetch_latest_posts(
        reddit, subreddit_to_fetch, limit=post_limit
    )
    await print_post_details(latest_posts)

    # Clean up by closing the Reddit instance
    await reddit.close()

    # Calculate and display execution time
    execution_time = time.time() - start_time
    logger.info(f"Script completed in {execution_time:.2f} seconds.")


if __name__ == "__main__":
    """
        Script entry point.
    a
        Runs the main async function and handles unexpected errors and keyboard interrupts.
    """
    try:
        # Run the main async function
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
