import type { Analysis, GeneratedContent, Image, Platform, PromptVersion } from '../types';

const API_BASE = '/api/v1';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export { ApiError };

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new ApiError(response.status, error || 'Request failed');
  }

  return response.json();
}

export const api = {
  // Images
  uploadImage: async (file: File): Promise<Image> => {
    const formData = new FormData();
    formData.append('file', file);
    
    console.log('Uploading to:', `${API_BASE}/images/upload`);
    const response = await fetch(`${API_BASE}/images/upload`, {
      method: 'POST',
      body: formData,
    });

    console.log('Response status:', response.status);
    console.log('Response ok:', response.ok);

    if (!response.ok) {
      const error = await response.text();
      console.error('Upload error response:', error);
      throw new ApiError(response.status, error || 'Upload failed');
    }

    const data = await response.json();
    console.log('Upload response data:', data);
    return data;
  },

  getImages: async (skip = 0, limit = 100): Promise<Image[]> => {
    const response = await fetchApi<{images: Image[]}>(`/images?skip=${skip}&limit=${limit}`);
    return response.images;
  },

  getImage: async (id: string): Promise<Image> => {
    return fetchApi<Image>(`/images/${id}`);
  },

  deleteImage: async (id: string): Promise<void> => {
    const response = await fetch(`${API_BASE}/images/${id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new ApiError(response.status, error || 'Delete failed');
    }
  },

  // Analysis
  analyzeImage: async (imageId: string): Promise<Analysis> => {
    return fetchApi<Analysis>('/analysis/analyze', {
      method: 'POST',
      body: JSON.stringify({ image_id: imageId }),
    });
  },

  getAnalysis: async (imageId: string): Promise<Analysis> => {
    return fetchApi<Analysis>(`/analysis/${imageId}`);
  },

  updateAnalysis: async (imageId: string, data: Partial<Analysis>): Promise<Analysis> => {
    return fetchApi<Analysis>(`/analysis/${imageId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // Content
  generateContent: async (imageId: string, platforms?: Platform[]): Promise<GeneratedContent[]> => {
    return fetchApi<GeneratedContent[]>('/content/generate', {
      method: 'POST',
      body: JSON.stringify({
        image_id: imageId,
        platforms: platforms || ['artstation', 'x', 'instagram', 'reddit', 'deviantart'],
      }),
    });
  },

  getContent: async (imageId: string): Promise<GeneratedContent[]> => {
    const response = await fetchApi<{image_id: string, platforms: Record<string, GeneratedContent[]>}>(`/content/${imageId}`);
    // Flatten the platforms object into a single array
    const allContent: GeneratedContent[] = [];
    for (const platform in response.platforms) {
      allContent.push(...response.platforms[platform]);
    }
    return allContent;
  },

  getPlatformContent: async (imageId: string, platform: Platform): Promise<GeneratedContent[]> => {
    return fetchApi<GeneratedContent[]>(`/content/${imageId}/${platform}`);
  },

  updateContent: async (contentId: string, content: string): Promise<GeneratedContent> => {
    return fetchApi<GeneratedContent>(`/content/${contentId}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  },

  deleteContent: async (imageId: string): Promise<void> => {
    const response = await fetch(`${API_BASE}/content/${imageId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new ApiError(response.status, error || 'Delete failed');
    }
  },

  // Prompts
  getPrompts: async (): Promise<Record<string, PromptVersion[]>> => {
    const response = await fetchApi<{prompts: Record<string, PromptVersion[]>}>('/prompts');
    return response.prompts;
  },

  getPrompt: async (name: string): Promise<PromptVersion> => {
    return fetchApi<PromptVersion>(`/prompts/${name}`);
  },

  createPrompt: async (name: string, content: string, version?: string): Promise<PromptVersion> => {
    return fetchApi<PromptVersion>('/prompts', {
      method: 'POST',
      body: JSON.stringify({ name, content, version, set_active: true }),
    });
  },

  updatePrompt: async (name: string, content: string): Promise<PromptVersion> => {
    return fetchApi<PromptVersion>(`/prompts/${name}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  },

  reloadPrompt: async (name: string): Promise<PromptVersion> => {
    return fetchApi<PromptVersion>('/prompts/reload', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  },

  setActivePrompt: async (name: string, version: string): Promise<PromptVersion> => {
    return fetchApi<PromptVersion>('/prompts/set-active', {
      method: 'POST',
      body: JSON.stringify({ name, version }),
    });
  },
};
