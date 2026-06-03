import { useState } from 'react';
import { Upload, Image as ImageIcon, FileText, Settings, Loader2 } from 'lucide-react';
import ImageUpload from './components/ImageUpload';
import AnalysisEditor from './components/AnalysisEditor';
import ContentEditor from './components/ContentEditor';
import PromptEditor from './components/PromptEditor';
import type { Image, Analysis, GeneratedContent } from './types';
import { api } from './services/api';

type View = 'upload' | 'analysis' | 'content' | 'prompts';

function App() {
  const [view, setView] = useState<View>('upload');
  const [selectedImage, setSelectedImage] = useState<Image | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [content, setContent] = useState<GeneratedContent[] | null>(null);
  const [loading, setLoading] = useState(false);

  const handleImageSelect = async (image: Image) => {
    setSelectedImage(image);
    setAnalysis(null);
    setContent(null);

    // Load existing analysis if available
    try {
      const existingAnalysis = await api.getAnalysis(image.id);
      setAnalysis(existingAnalysis);
    } catch (error) {
      console.log('No existing analysis');
    }

    // Load existing content if available
    try {
      const existingContent = await api.getContent(image.id);
      setContent(existingContent);
    } catch (error) {
      console.log('No existing content');
    }
  };

  const handleGenerateContent = async () => {
    if (!selectedImage) return;

    setLoading(true);
    try {
      const result = await api.generateContent(selectedImage.id);
      setContent(result);
      setView('content');
    } catch (error) {
      console.error('Content generation failed:', error);
      alert('Content generation failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-purple-400">ArtForge Publisher</h1>
            <nav className="flex gap-4">
              <button
                onClick={() => setView('upload')}
                className={`px-4 py-2 rounded-lg transition ${
                  view === 'upload' ? 'bg-purple-600' : 'bg-gray-700 hover:bg-gray-600'
                }`}
              >
                <Upload className="inline w-4 h-4 mr-2" />
                Upload
              </button>
              <button
                onClick={() => setView('analysis')}
                className={`px-4 py-2 rounded-lg transition ${
                  view === 'analysis' ? 'bg-purple-600' : 'bg-gray-700 hover:bg-gray-600'
                }`}
                disabled={!selectedImage}
              >
                <ImageIcon className="inline w-4 h-4 mr-2" />
                Analysis
              </button>
              <button
                onClick={() => setView('content')}
                className={`px-4 py-2 rounded-lg transition ${
                  view === 'content' ? 'bg-purple-600' : 'bg-gray-700 hover:bg-gray-600'
                }`}
                disabled={!selectedImage}
              >
                <FileText className="inline w-4 h-4 mr-2" />
                Content
              </button>
              <button
                onClick={() => setView('prompts')}
                className={`px-4 py-2 rounded-lg transition ${
                  view === 'prompts' ? 'bg-purple-600' : 'bg-gray-700 hover:bg-gray-600'
                }`}
              >
                <Settings className="inline w-4 h-4 mr-2" />
                Prompts
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
            <span className="ml-3 text-gray-400">Processing...</span>
          </div>
        )}

        {!loading && (
          <>
            {view === 'upload' && (
              <ImageUpload onImageSelect={handleImageSelect} />
            )}

            {view === 'analysis' && selectedImage && (
              <AnalysisEditor
                imageId={selectedImage.id}
                analysis={analysis}
                onAnalysisUpdate={setAnalysis}
                onGenerateContent={handleGenerateContent}
              />
            )}

            {view === 'content' && selectedImage && (
              <ContentEditor
                image={selectedImage}
                content={content}
                onGenerate={handleGenerateContent}
                onContentUpdate={setContent}
              />
            )}

            {view === 'prompts' && <PromptEditor />}
          </>
        )}
      </main>
    </div>
  );
}

export default App;
