"""
Reddit Post Fetcher API

- Grab the newest posts from any subreddit
- Let you choose how many posts to get
- Talk to the frontend through CORS (so your browser won't complain)
- Search for subreddits if you don't know the exact name
- Generate AI-powered summaries for posts
"""

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
import time
from datetime import datetime


import reddit_fetcher
import ai_services


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("reddit_api")

app = FastAPI(
    title="Reddit Post Fetcher API",
    description="API for fetching and serving the latest posts from Reddit with AI enhancements",
    version="1.0.0",
)

# Setting up CORS so the frontend can talk to us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Author(BaseModel):
    """
    Model for a Reddit post author

    """

    name: str = Field(..., description="Username of the post author")


class RedditPost(BaseModel):
    """
    This has everything you'd want to know about a post:
    the title, who wrote it, upvotes, when it was posted,
    links, text content, thumbnail, and comment count.
    """

    id: str = Field(..., description="Unique identifier of the post")
    title: str = Field(..., description="Title of the post")
    author: str = Field(..., description="Username of the post author")
    score: int = Field(..., description="Upvote count")
    created_utc: float = Field(..., description="Post creation timestamp (Unix time)")
    url: str = Field(..., description="URL of the post")
    permalink: str = Field(..., description="Permalink to the post on Reddit")
    is_self: bool = Field(..., description="Whether this is a self-post (text post)")
    selftext: Optional[str] = Field(
        None, description="Text content if this is a self post"
    )
    thumbnail: Optional[str] = Field(
        None, description="URL to the thumbnail image if available"
    )
    num_comments: int = Field(..., description="Number of comments on the post")
    tldr: Optional[str] = Field(None, description="AI-generated TL;DR summary")


class PostsResponse(BaseModel):
    """
    What we send back when someone asks for posts

    Includes the subreddit name, a list of posts,
    how many there are and when we fetched them
    """

    subreddit: str = Field(..., description="Name of the subreddit")
    posts: List[RedditPost] = Field(..., description="List of Reddit posts")
    count: int = Field(..., description="Number of posts returned")
    fetched_at: str = Field(..., description="Time when posts were fetched")
    ai_enhanced: bool = Field(False, description="Whether posts have AI enhancements")


class SearchResult(BaseModel):
    """
    What we send back for subreddit searches

    Shows what you searched for, what we found,
    and how many results we're giving you.
    """

    query: str = Field(..., description="Search query")
    results: List[str] = Field(..., description="List of matching subreddit names")
    count: int = Field(..., description="Number of results returned")


class AIResponse(BaseModel):
    """
    Response for individual AI enhancement requests
    """

    post_id: str = Field(..., description="ID of the post that was processed")
    tldr: Optional[str] = Field(None, description="TL;DR summary")
    success: bool = Field(True, description="Whether the AI processing was successful")
    message: Optional[str] = Field(
        None, description="Error message if processing failed"
    )


# This runs before each request to track timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Add processing time to response headers
    """
    start_time = time.time()
    response = await call_next(request)
    processing_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(processing_time)
    return response


@app.get("/api/search/subreddits", response_model=SearchResult)
async def search_subreddits(
    query: str = Query(..., min_length=1, description="Search query for subreddits"),
    limit: int = Query(
        5, ge=1, le=25, description="Maximum number of results to return"
    ),
):
    """
    Search for subreddits matching a query string

    Args:
        query: Search term to find subreddits
        limit: Maximum number of results to return (1-25)

    Returns:
        Matching subreddit names and search metadata
    """
    try:
        # Load Reddit credentials
        client_id, client_secret, user_agent, username, password = (
            await reddit_fetcher.load_reddit_credentials()
        )

        # Authenticate with Reddit
        reddit = await reddit_fetcher.authenticate_reddit(
            client_id, client_secret, user_agent, username, password
        )

        # Search for subreddits
        subreddits = []
        async for subreddit in reddit.subreddits.search(query, limit=limit):
            subreddits.append(subreddit.display_name)

        # Clean up Reddit resources
        await reddit.close()

        # Return the search results
        return {"query": query, "results": subreddits, "count": len(subreddits)}

    except Exception as e:
        logger.error(f"Error searching for subreddits: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to search for subreddits: {str(e)}"
        )


@app.get("/api/posts/{subreddit}", response_model=PostsResponse)
async def get_posts(
    subreddit: str,
    limit: int = Query(5, ge=1, le=25, description="Number of posts to fetch (1-25)"),
    use_ai: bool = Query(
        False, description="Enable AI enhancements (summaries and sentiment)"
    ),
):
    """
    Fetch the latest posts from a specified subreddit

    Args:
        subreddit: Name of the subreddit to fetch posts from
        limit: Number of posts to return (1-25)
        use_ai: Apply AI enhancements (summaries and sentiment analysis)

    Returns:
        The latest posts from the subreddit with optional AI enhancements
    """

    try:
        # Load Reddit credentials and authenticate
        client_id, client_secret, user_agent, username, password = (
            await reddit_fetcher.load_reddit_credentials()
        )
        reddit = await reddit_fetcher.authenticate_reddit(
            client_id, client_secret, user_agent, username, password
        )

        # Fetch posts
        posts = await reddit_fetcher.fetch_latest_posts(reddit, subreddit, limit=limit)

        # Close the Reddit instance to free resources
        await reddit.close()

        if not posts:
            raise HTTPException(
                status_code=404, detail=f"No posts found in r/{subreddit}"
            )

        # Convert posts to our API format
        formatted_posts = []
        for post in posts:
            # Handle deleted/removed authors
            author_name = "[deleted]"
            if hasattr(post, "author") and post.author:
                author_name = post.author.name

            # Extract relevant post data
            formatted_post = {
                "id": post.id,
                "title": post.title,
                "author": author_name,
                "score": post.score,
                "created_utc": post.created_utc,
                "url": post.url,
                "permalink": f"https://www.reddit.com{post.permalink}",
                "is_self": post.is_self,
                "selftext": post.selftext if post.is_self else None,
                "thumbnail": (
                    post.thumbnail
                    if post.thumbnail not in ["self", "default", "nsfw"]
                    else None
                ),
                "num_comments": post.num_comments,
            }
            formatted_posts.append(formatted_post)

        # Apply AI enhancements if requested
        ai_enhanced = False
        if use_ai:
            logger.info(
                f"Applying AI enhancements to {len(formatted_posts)} posts from r/{subreddit}"
            )
            formatted_posts = await ai_services.process_post_batch(formatted_posts)
            ai_enhanced = True

        # Prepare the response
        response_data = {
            "subreddit": subreddit,
            "posts": formatted_posts,
            "count": len(formatted_posts),
            "fetched_at": datetime.now().isoformat(),
            "ai_enhanced": ai_enhanced,
        }

        return response_data

    except reddit_fetcher.asyncpraw.exceptions.RedditAPIException as api_exception:
        for subexception in api_exception.items:
            logger.error(
                f"Reddit API Error: {subexception.error_type} - {subexception.message}"
            )

            if subexception.error_type in ["SUBREDDIT_NOEXIST", "SUBREDDIT_NOTALLOWED"]:
                raise HTTPException(
                    status_code=404,
                    detail=f"Subreddit 'r/{subreddit}' does not exist or is private",
                )

            elif subexception.error_type in ["RATELIMIT", "QUOTA_FILLED"]:
                wait_time = reddit_fetcher.extract_wait_time(subexception.message)
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limited by Reddit. Try again in {wait_time} seconds.",
                )

        raise HTTPException(
            status_code=500, detail=f"Reddit API error: {str(api_exception)}"
        )

    except Exception as e:
        logger.error(f"Error fetching posts from r/{subreddit}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch posts: {str(e)}")


@app.post("/api/ai/enhance/{post_id}", response_model=AIResponse)
async def enhance_post(
    post_id: str,
    title: str = Query(..., description="Post title"),
    text: str = Query(..., description="Post text content"),
):
    """
    Apply AI enhancements to a single post

    Args:
        post_id: Reddit post ID
        title: Post title
        text: Post content

    Returns:
        AI-generated enhancements for the post
    """
    try:
        # Generate TL;DR
        tldr = await ai_services.generate_tldr(title, text)

        return {"post_id": post_id, "tldr": tldr, "success": True}

    except Exception as e:
        logger.error(f"Error enhancing post {post_id}: {e}")
        return {"post_id": post_id, "success": False, "message": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
