export type ImageStatus = 'uploaded' | 'analyzing' | 'analyzed' | 'generating' | 'ready' | 'failed';

export type Platform = 'artstation' | 'x' | 'instagram' | 'reddit' | 'deviantart';

export type ContentType = 'title' | 'description' | 'hashtags' | 'post' | 'recommended_subreddits';

export interface Image {
  id: string;
  filename: string;
  original_path: string;
  thumbnail_path: string | null;
  file_size: number;
  width: number | null;
  height: number | null;
  mime_type: string;
  status: ImageStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface Analysis {
  id: string;
  image_id: string;
  raw_response: Record<string, unknown>;
  title: string | null;
  subject: string | null;
  character_description: string | null;
  environment: string | null;
  art_style: string | null;
  color_palette: string[];
  mood: string | null;
  genre: string | null;
  technical_details: string | null;
  artistic_influences: string | null;
  search_keywords: string[];
  audience_interests: string[];
  model_used: string;
  prompt_version: string;
  created_at: string;
  updated_at: string;
}

export interface GeneratedContent {
  id: string;
  image_id: string;
  platform: Platform;
  content_type: ContentType;
  content: string;
  is_edited: boolean;
  prompt_version: string;
  created_at: string;
  updated_at: string;
}

export interface PromptVersion {
  id: string;
  name: string;
  version: string;
  content: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
