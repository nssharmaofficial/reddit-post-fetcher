import { useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { ExternalLink, MessageSquare, ThumbsUp, Clock, Sparkles } from "lucide-react";
import { formatDistanceToNow } from 'date-fns';

type Post = {
  id: string;
  title: string;
  author: string;
  score: number;
  created_utc: number;
  url: string;
  permalink: string;
  is_self: boolean;
  selftext: string | null;
  thumbnail: string | null;
  num_comments: number;
  tldr?: string;
};

type PostCardProps = {
  post: Post;
  enableAI?: boolean;
};

export function PostCard({ post, enableAI = false }: PostCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showTldr, setShowTldr] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [tldr, setTldr] = useState<string | undefined>(post.tldr);

  // Format the post creation time
  const timeAgo = formatDistanceToNow(new Date(post.created_utc * 1000), { addSuffix: true });

  // Fetch AI enhancements for a single post
  const fetchAIEnhancements = async () => {
    if (tldr) {
      // If we already have the data, just show it
      setShowTldr(true);
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`/api/ai/enhance/${post.id}?title=${encodeURIComponent(post.title)}&text=${encodeURIComponent(post.selftext || post.title)}`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch AI enhancements');
      }
      
      const data = await response.json();
      
      if (data.success) {
        setTldr(data.tldr);
        setShowTldr(true);
      } else {
        console.error('AI enhancement failed:', data.message);
      }
    } catch (error) {
      console.error('Error fetching AI enhancements:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="mb-4 overflow-hidden hover:shadow-md transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <CardTitle className="text-lg font-bold text-gray-900">{post.title}</CardTitle>
        </div>
        <CardDescription className="flex items-center gap-2 text-sm text-gray-500">
          <span>Posted by u/{post.author}</span>
          <span>•</span>
          <Clock className="h-3 w-3" />
          <span>{timeAgo}</span>
        </CardDescription>
      </CardHeader>
      
      <CardContent className="pb-2">
        {/* Text content preview, expand on click */}
        {post.selftext && (
          <div className="mt-2">
            <div className={`prose max-w-none ${!isExpanded && 'line-clamp-3'}`}>
              <p>{post.selftext}</p>
            </div>
            {post.selftext.length > 180 && (
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setIsExpanded(!isExpanded)} 
                className="mt-1 text-xs"
              >
                {isExpanded ? 'Show less' : 'Read more'}
              </Button>
            )}
          </div>
        )}
        
        {/* Thumbnail if available */}
        {post.thumbnail && !post.is_self && (
          <div className="mt-2">
            <img 
              src={post.thumbnail} 
              alt="Post thumbnail" 
              className="rounded-md max-h-40 object-cover"
            />
          </div>
        )}
        
        {/* AI-generated summary */}
        {enableAI && (
          <div className="mt-3">
            {!showTldr ? (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={fetchAIEnhancements}
                disabled={isLoading}
                className="flex items-center gap-1 text-xs"
              >
                <Sparkles className="h-3 w-3" />
                {isLoading ? 'Generating...' : 'Generate TL;DR'}
              </Button>
            ) : (
              <div className="bg-blue-50 p-3 rounded-md mt-2">
                <div className="flex items-center gap-1 text-blue-700 font-medium text-sm mb-1">
                  <Sparkles className="h-3 w-3" />
                  <span>TL;DR</span>
                </div>
                <p className="text-sm text-gray-700">{tldr}</p>
              </div>
            )}
          </div>
        )}
      </CardContent>
      
      <CardFooter className="flex justify-between pt-2">
        <div className="flex gap-3">
          <span className="flex items-center gap-1 text-sm">
            <ThumbsUp className="h-4 w-4" />
            {post.score}
          </span>
          <span className="flex items-center gap-1 text-sm">
            <MessageSquare className="h-4 w-4" />
            {post.num_comments}
          </span>
        </div>
        
        <Button 
          variant="outline" 
          size="sm" 
          className="text-xs" 
          onClick={() => window.open(post.permalink, '_blank')}
        >
          <ExternalLink className="h-3 w-3 mr-1" />
          View on Reddit
        </Button>
      </CardFooter>
    </Card>
  );
} 