import { useState, useEffect } from 'react';
import { FileText, RefreshCw, Save, Edit2 } from 'lucide-react';
import type { PromptVersion } from '../types';
import { api } from '../services/api';

export default function PromptEditor() {
  const [prompts, setPrompts] = useState<Record<string, PromptVersion[]>>({});
  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState('');

  const loadPrompts = async () => {
    try {
      const loadedPrompts = await api.getPrompts();
      setPrompts(loadedPrompts);
    } catch (error) {
      console.error('Failed to load prompts:', error);
    }
  };

  const handleViewPrompt = (name: string) => {
    const versions = prompts[name];
    if (versions && versions.length > 0) {
      const active = versions.find(v => v.is_active) || versions[0];
      setSelectedPrompt(name);
      setEditContent(active.content);
      setEditing(false);
    }
  };

  const handleReloadPrompt = async (name: string) => {
    try {
      await api.reloadPrompt(name);
      await loadPrompts();
      handleViewPrompt(name);
    } catch (error) {
      console.error('Reload failed:', error);
      alert('Reload failed. Please try again.');
    }
  };

  const handleSavePrompt = async () => {
    if (!selectedPrompt) return;
    
    try {
      await api.updatePrompt(selectedPrompt, editContent);
      await loadPrompts();
      setEditing(false);
    } catch (error) {
      console.error('Save failed:', error);
      alert('Save failed. Please try again.');
    }
  };

  useEffect(() => {
    loadPrompts();
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Prompt Templates</h2>
        
        {/* Prompt List */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {Object.entries(prompts).map(([name, versions]) => (
            <button
              key={name}
              onClick={() => handleViewPrompt(name)}
              className={`p-4 rounded-lg text-left transition ${
                selectedPrompt === name
                  ? 'bg-purple-600 ring-2 ring-purple-400'
                  : 'bg-gray-700 hover:bg-gray-600'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <FileText className="w-5 h-5" />
                <span className="text-sm text-gray-400">{versions.length} versions</span>
              </div>
              <p className="font-medium capitalize">{name.replace('_', ' ')}</p>
            </button>
          ))}
        </div>

        {/* Prompt Editor */}
        {selectedPrompt && (
          <div className="bg-gray-700 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold capitalize">
                {selectedPrompt.replace('_', ' ')}
              </h3>
              <div className="flex gap-2">
                <button
                  onClick={() => handleReloadPrompt(selectedPrompt)}
                  className="p-2 bg-gray-600 hover:bg-gray-500 rounded-lg transition"
                  title="Reload from file"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
                {editing ? (
                  <button
                    onClick={handleSavePrompt}
                    className="p-2 bg-green-600 hover:bg-green-700 rounded-lg transition"
                    title="Save"
                  >
                    <Save className="w-4 h-4" />
                  </button>
                ) : (
                  <button
                    onClick={() => setEditing(true)}
                    className="p-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition"
                    title="Edit"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>

            {editing ? (
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="w-full h-64 bg-gray-800 border border-gray-600 rounded-lg p-4 text-sm font-mono resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            ) : (
              <pre className="w-full h-64 bg-gray-800 border border-gray-600 rounded-lg p-4 text-sm font-mono overflow-auto">
                {editContent}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
