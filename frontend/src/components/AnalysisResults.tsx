import { Brain, Loader2, CheckCircle, XCircle } from 'lucide-react';
import type { Image, Analysis } from '../types';

interface AnalysisResultsProps {
  image: Image;
  analysis: Analysis | null;
  onAnalyze: () => void;
}

export default function AnalysisResults({ image, analysis, onAnalyze }: AnalysisResultsProps) {
  return (
    <div className="space-y-6">
      {/* Image Preview */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Image Preview</h2>
        {image.thumbnail_path ? (
          <img
            src={`http://localhost:8000${image.thumbnail_path}`}
            alt={image.filename}
            className="w-full max-w-md rounded-lg"
          />
        ) : (
          <div className="w-full max-w-md h-64 bg-gray-700 rounded-lg flex items-center justify-center">
            <p className="text-gray-500">No preview available</p>
          </div>
        )}
        <p className="mt-2 text-sm text-gray-400">{image.filename}</p>
      </div>

      {/* Analysis Controls */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">AI Analysis</h2>
        {!analysis ? (
          <div className="text-center">
            <Brain className="w-12 h-12 text-gray-500 mx-auto mb-4" />
            <p className="text-gray-400 mb-4">
              Analyze this image using Qwen2.5-VL-7B to extract metadata and insights
            </p>
            <button
              onClick={onAnalyze}
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg transition flex items-center mx-auto"
            >
              <Brain className="w-5 h-5 mr-2" />
              Analyze Image
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center text-green-400 mb-4">
              <CheckCircle className="w-5 h-5 mr-2" />
              <span>Analysis Complete</span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-1">Title</h3>
                <p className="text-white">{analysis.title || 'N/A'}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-1">Style</h3>
                <p className="text-white">{analysis.art_style || 'N/A'}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-1">Genre</h3>
                <p className="text-white">{analysis.genre || 'N/A'}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-1">Mood</h3>
                <p className="text-white">{analysis.mood || 'N/A'}</p>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-1">Subject</h3>
              <p className="text-white">{analysis.subject || 'N/A'}</p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-1">Environment</h3>
              <p className="text-white">{analysis.environment || 'N/A'}</p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-1">Technical Details</h3>
              <p className="text-white">{analysis.technical_details || 'N/A'}</p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-1">Color Palette</h3>
              <div className="flex gap-2 flex-wrap">
                {analysis.color_palette.map((color, index) => (
                  <div
                    key={index}
                    className="w-8 h-8 rounded border border-gray-600"
                    style={{ backgroundColor: color }}
                    title={color}
                  />
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-1">Search Keywords</h3>
              <div className="flex gap-2 flex-wrap">
                {analysis.search_keywords.map((keyword, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-gray-700 rounded-full text-sm"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
