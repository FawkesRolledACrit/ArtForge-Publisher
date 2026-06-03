import { Save, Loader2, Edit2, Sparkles } from 'lucide-react';
import type { Analysis } from '../types';
import { api } from '../services/api';
import { useState } from 'react';

interface AnalysisEditorProps {
  imageId: string;
  analysis: Analysis | null;
  onAnalysisUpdate: (analysis: Analysis) => void;
  onGenerateContent: () => void;
}

export default function AnalysisEditor({
  imageId,
  analysis,
  onAnalysisUpdate,
  onGenerateContent
}: AnalysisEditorProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [editedData, setEditedData] = useState<Partial<Analysis>>(analysis || {});

  const handleEdit = () => {
    setEditedData(analysis || {});
    setIsEditing(true);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditedData(analysis || {});
  };

  const handleSave = async () => {
    if (!analysis) return;

    setIsSaving(true);
    try {
      const updated = await api.updateAnalysis(imageId, editedData);
      onAnalysisUpdate(updated);
      setIsEditing(false);
    } catch (error) {
      console.error('Update failed:', error);
      alert('Update failed. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    try {
      const result = await api.analyzeImage(imageId);
      onAnalysisUpdate(result);
    } catch (error) {
      console.error('Analysis failed:', error);
      alert('Analysis failed. Please ensure Ollama is running.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleChange = (field: string, value: any) => {
    setEditedData({ ...editedData, [field]: value });
  };

  if (!analysis) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400 mb-4">No analysis yet. Click "Analyze" to start.</p>
        <button
          onClick={handleAnalyze}
          disabled={isAnalyzing}
          className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg transition flex items-center mx-auto"
        >
          {isAnalyzing ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5 mr-2" />
              Analyze
            </>
          )}
        </button>
      </div>
    );
  }

  if (isEditing) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Edit Analysis</h2>
          <div className="flex gap-2">
            <button
              onClick={handleCancel}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition flex items-center"
            >
              {isSaving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Save
                </>
              )}
            </button>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Title</label>
            <input
              type="text"
              value={editedData.title || ''}
              onChange={(e) => handleChange('title', e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Subject</label>
            <textarea
              value={editedData.subject || ''}
              onChange={(e) => handleChange('subject', e.target.value)}
              rows={3}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Character Description</label>
            <textarea
              value={editedData.character_description || ''}
              onChange={(e) => handleChange('character_description', e.target.value)}
              rows={3}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Environment</label>
            <textarea
              value={editedData.environment || ''}
              onChange={(e) => handleChange('environment', e.target.value)}
              rows={3}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Art Style</label>
            <input
              type="text"
              value={editedData.art_style || ''}
              onChange={(e) => handleChange('art_style', e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Color Palette (comma-separated)</label>
            <input
              type="text"
              value={Array.isArray(editedData.color_palette) ? editedData.color_palette.join(', ') : ''}
              onChange={(e) => handleChange('color_palette', e.target.value.split(',').map(s => s.trim()))}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Mood</label>
            <input
              type="text"
              value={editedData.mood || ''}
              onChange={(e) => handleChange('mood', e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Genre</label>
            <input
              type="text"
              value={editedData.genre || ''}
              onChange={(e) => handleChange('genre', e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Technical Details</label>
            <textarea
              value={editedData.technical_details || ''}
              onChange={(e) => handleChange('technical_details', e.target.value)}
              rows={4}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Artistic Influences</label>
            <textarea
              value={editedData.artistic_influences || ''}
              onChange={(e) => handleChange('artistic_influences', e.target.value)}
              rows={3}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Search Keywords (comma-separated)</label>
            <input
              type="text"
              value={Array.isArray(editedData.search_keywords) ? editedData.search_keywords.join(', ') : ''}
              onChange={(e) => handleChange('search_keywords', e.target.value.split(',').map(s => s.trim()))}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Audience Interests (comma-separated)</label>
            <input
              type="text"
              value={Array.isArray(editedData.audience_interests) ? editedData.audience_interests.join(', ') : ''}
              onChange={(e) => handleChange('audience_interests', e.target.value.split(',').map(s => s.trim()))}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Analysis Results</h2>
        <div className="flex gap-2">
          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition flex items-center"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Re-analyzing...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Re-analyze
              </>
            )}
          </button>
          <button
            onClick={handleEdit}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition flex items-center"
          >
            <Edit2 className="w-4 h-4 mr-2" />
            Edit
          </button>
          <button
            onClick={onGenerateContent}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition flex items-center"
          >
            Generate Content
          </button>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-6 space-y-4">
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-1">Title</h3>
          <p className="text-white">{analysis.title || 'N/A'}</p>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-1">Subject</h3>
          <p className="text-white">{analysis.subject || 'N/A'}</p>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-1">Character Description</h3>
          <p className="text-white">{analysis.character_description || 'N/A'}</p>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-1">Environment</h3>
          <p className="text-white">{analysis.environment || 'N/A'}</p>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-1">Art Style</h3>
          <p className="text-white">{analysis.art_style || 'N/A'}</p>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-1">Color Palette</h3>
          <div className="flex flex-wrap gap-2">
            {Array.isArray(analysis.color_palette) && analysis.color_palette.length > 0 ? (
              analysis.color_palette.map((color, idx) => (
                <span key={idx} className="px-2 py-1 bg-gray-700 rounded text-sm">{color}</span>
              ))
            ) : (
              <span className="text-gray-500">N/A</span>
            )}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-1">Mood</h3>
          <p className="text-white">{analysis.mood || 'N/A'}</p>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-1">Genre</h3>
          <p className="text-white">{analysis.genre || 'N/A'}</p>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-1">Technical Details</h3>
          <p className="text-white whitespace-pre-wrap">{analysis.technical_details || 'N/A'}</p>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-1">Artistic Influences</h3>
          <p className="text-white">{analysis.artistic_influences || 'N/A'}</p>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-1">Search Keywords</h3>
          <div className="flex flex-wrap gap-2">
            {Array.isArray(analysis.search_keywords) && analysis.search_keywords.length > 0 ? (
              analysis.search_keywords.map((keyword, idx) => (
                <span key={idx} className="px-2 py-1 bg-gray-700 rounded text-sm">{keyword}</span>
              ))
            ) : (
              <span className="text-gray-500">N/A</span>
            )}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-1">Audience Interests</h3>
          <div className="flex flex-wrap gap-2">
            {Array.isArray(analysis.audience_interests) && analysis.audience_interests.length > 0 ? (
              analysis.audience_interests.map((interest, idx) => (
                <span key={idx} className="px-2 py-1 bg-gray-700 rounded text-sm">{interest}</span>
              ))
            ) : (
              <span className="text-gray-500">N/A</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
