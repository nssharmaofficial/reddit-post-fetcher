"use client";

import { useState, useEffect } from "react";
import { PostCard } from "@/components/PostCard";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Search, RefreshCw, Sparkles } from "lucide-react";

export default function Home() {
  // State for the subreddit input
  const [subreddit, setSubreddit] = useState<string>("programming");
  const [inputValue, setInputValue] = useState<string>("programming");
  
  // State for the post count slider
  const [postLimit, setPostLimit] = useState<number>(5);
  
  // AI features always enabled
  const enableAI = true;
  
  // State for posts and loading
  const [posts, setPosts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch posts on initial load and when subreddit changes
  useEffect(() => {
    fetchPosts();
  }, []);

  // Function to fetch posts from the API
  const fetchPosts = async (forceRefresh = false) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `/api/posts/${subreddit}?limit=${postLimit}&force_refresh=${forceRefresh}&use_ai=${enableAI}`
      );
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch posts');
      }
      
      const data = await response.json();
      setPosts(data.posts);
    } catch (error) {
      console.error('Error fetching posts:', error);
      setError(error instanceof Error ? error.message : 'An unknown error occurred');
      setPosts([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubreddit(inputValue);
    fetchPosts(true);
  };

  // Handle refresh button click
  const handleRefresh = () => {
    fetchPosts(true);
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-4 sm:p-24">
      <h1 className="text-4xl font-bold mb-8 text-center">Reddit Post Fetcher</h1>
      
      {/* Search form */}
      <div className="w-full max-w-3xl mb-8">
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-grow">
              <div className="flex">
                <span className="inline-flex items-center px-3 text-sm bg-gray-200 border border-r-0 border-gray-300 rounded-l-md">
                  r/
                </span>
                <Input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Enter subreddit name"
                  className="rounded-l-none"
                  required
                />
              </div>
            </div>
            <Button type="submit" className="w-full sm:w-auto">
              <Search className="h-4 w-4 mr-2" />
              Search
            </Button>
            <Button 
              type="button" 
              variant="outline" 
              onClick={handleRefresh}
              disabled={isLoading}
              className="w-full sm:w-auto"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="post-count">Number of posts: {postLimit}</Label>
            </div>
            <Slider
              id="post-count"
              min={1}
              max={25}
              step={1}
              value={[postLimit]}
              onValueChange={(value: number[]) => setPostLimit(value[0])}
            />
          </div>
        </form>
      </div>
      
      {/* Display current subreddit */}
      <div className="w-full max-w-3xl mb-4">
        <h2 className="text-2xl font-semibold mb-2">
          {isLoading ? (
            <span className="animate-pulse">Loading posts...</span>
          ) : (
            <span>r/{subreddit}</span>
          )}
        </h2>
        
        <div className="flex items-center mb-4 text-sm text-blue-700 bg-blue-50 p-2 rounded">
          <Sparkles className="h-4 w-4 mr-2" />
          <span>AI features enabled: Post summaries</span>
        </div>
      </div>
      
      {/* Error message */}
      {error && (
        <Card className="w-full max-w-3xl mb-4 border-red-200 bg-red-50">
          <CardContent className="p-4 text-red-800">
            <p>{error}</p>
          </CardContent>
        </Card>
      )}
      
      {/* Post list */}
      <div className="w-full max-w-3xl">
        {posts.length > 0 ? (
          posts.map((post) => (
            <PostCard key={post.id} post={post} enableAI={enableAI} />
          ))
        ) : !isLoading && !error ? (
          <p className="text-center text-gray-500">No posts found.</p>
        ) : null}
      </div>
    </main>
  );
} 