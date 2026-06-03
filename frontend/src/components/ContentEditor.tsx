import { FileText, Copy, Edit2 } from 'lucide-react';
import type { Image, GeneratedContent, Platform } from '../types';
import { api } from '../services/api';

interface ContentEditorProps {
  image: Image;
  content: GeneratedContent[] | null;
  onGenerate: () => void;
  onContentUpdate: (content: GeneratedContent[]) => void;
}

const PLATFORM_NAMES: Record<Platform, string> = {
  artstation: 'ArtStation',
  x: 'X (Twitter)',
  instagram: 'Instagram',
  reddit: 'Reddit',
  deviantart: 'DeviantArt',
};

export default function ContentEditor({ image, content, onGenerate, onContentUpdate }: ContentEditorProps) {
  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const handleEdit = async (contentId: string, currentContent: string) => {
    const newContent = prompt('Edit content:', currentContent);
    if (newContent !== null) {
      try {
        await api.updateContent(contentId, newContent);
        // Reload content
        const updatedContent = await api.getContent(image.id);
        onContentUpdate(updatedContent);
      } catch (error) {
        console.error('Update failed:', error);
        alert('Update failed. Please try again.');
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Generate Controls */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Platform Content</h2>
        {!content || content.length === 0 ? (
          <div className="text-center">
            <FileText className="w-12 h-12 text-gray-500 mx-auto mb-4" />
            <p className="text-gray-400 mb-4">
              Generate platform-specific content for your artwork
            </p>
            <button
              onClick={onGenerate}
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg transition flex items-center mx-auto"
            >
              <FileText className="w-5 h-5 mr-2" />
              Generate Content
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center text-green-400">
              <span>Content generated for {content.length} items</span>
            </div>

            {/* Group by platform */}
            {(() => {
              const grouped: Record<string, GeneratedContent[]> = {};
              content.forEach(item => {
                if (!grouped[item.platform]) {
                  grouped[item.platform] = [];
                }
                grouped[item.platform].push(item);
              });

              return Object.entries(grouped).map(([platform, items]) => (
                <div key={platform} className="bg-gray-700 rounded-lg p-6">
                  <h3 className="text-lg font-semibold mb-4 text-purple-400">
                    {PLATFORM_NAMES[platform as Platform] || platform}
                  </h3>
                  <div className="space-y-4">
                    {items.map((item) => (
                      <div key={item.id} className="bg-gray-800 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-400 capitalize">
                            {item.content_type.replace('_', ' ')}
                          </span>
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleCopy(item.content)}
                              className="p-1 hover:bg-gray-600 rounded transition"
                              title="Copy"
                            >
                              <Copy className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleEdit(item.id, item.content)}
                              className="p-1 hover:bg-gray-600 rounded transition"
                              title="Edit"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                        <pre className="text-sm text-gray-300 whitespace-pre-wrap font-sans">
                          {item.content}
                        </pre>
                        {item.is_edited && (
                          <span className="text-xs text-yellow-400 mt-2 block">
                            (Manually edited)
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ));
            })()}
          </div>
        )}
      </div>
    </div>
  );
}
