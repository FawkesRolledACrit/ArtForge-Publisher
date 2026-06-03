import { useState, useCallback, useEffect } from 'react';
import { Upload, X, Image as ImageIcon, Loader2 } from 'lucide-react';
import type { Image } from '../types';
import { api, ApiError } from '../services/api';

interface ImageUploadProps {
  onImageSelect: (image: Image) => void;
}

export default function ImageUpload({ onImageSelect }: ImageUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [images, setImages] = useState<Image[]>([]);

  const loadImages = async () => {
    try {
      const loadedImages = await api.getImages();
      setImages(loadedImages);
    } catch (error) {
      console.error('Failed to load images:', error);
    }
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFile = async (file: File) => {
    setUploading(true);
    try {
      console.log('Uploading file:', file.name, file.size, file.type);
      const uploadedImage = await api.uploadImage(file);
      console.log('Upload successful:', uploadedImage);
      setImages([uploadedImage, ...images]);
      onImageSelect(uploadedImage);
    } catch (error) {
      console.error('Upload failed:', error);
      const errorMessage = error instanceof ApiError 
        ? error.message 
        : error instanceof Error 
        ? error.message 
        : 'Unknown error';
      console.error('Error message:', errorMessage);
      alert(`Upload failed: ${errorMessage}`);
    } finally {
      setUploading(false);
    }
  };

  const handleInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      await handleFile(e.target.files[0]);
    }
  };

  const handleDelete = async (imageId: string) => {
    try {
      await api.deleteImage(imageId);
      setImages(images.filter(img => img.id !== imageId));
    } catch (error) {
      console.error('Delete failed:', error);
      alert('Delete failed. Please try again.');
    }
  };

  // Load images on mount
  useEffect(() => {
    loadImages();
  }, []);

  return (
    <div className="space-y-8">
      {/* Upload Area */}
      <div
        className={`border-2 border-dashed rounded-lg p-12 text-center transition ${
          dragActive ? 'border-purple-500 bg-purple-500/10' : 'border-gray-600 hover:border-gray-500'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        {uploading ? (
          <div className="flex flex-col items-center">
            <Loader2 className="w-12 h-12 animate-spin text-purple-400 mb-4" />
            <p className="text-gray-400">Uploading...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <Upload className="w-12 h-12 text-gray-500 mb-4" />
            <p className="text-gray-400 mb-4">
              Drag and drop an image here, or click to select
            </p>
            <input
              type="file"
              accept="image/*"
              onChange={handleInputChange}
              className="hidden"
              id="file-input"
            />
            <label
              htmlFor="file-input"
              className="px-6 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg cursor-pointer transition"
            >
              Select Image
            </label>
          </div>
        )}
      </div>

      {/* Image List */}
      {images.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Uploaded Images</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {images.map((image) => (
              <div
                key={image.id}
                className="relative group bg-gray-800 rounded-lg overflow-hidden cursor-pointer hover:ring-2 hover:ring-purple-500 transition"
                onClick={() => onImageSelect(image)}
              >
                {image.thumbnail_path ? (
                  <img
                    src={`/storage/thumbnails/${image.thumbnail_path.split(/[\\/]/).pop()}`}
                    alt={image.filename}
                    className="w-full h-40 object-cover"
                  />
                ) : (
                  <div className="w-full h-40 flex items-center justify-center bg-gray-700">
                    <ImageIcon className="w-8 h-8 text-gray-500" />
                  </div>
                )}
                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(image.id);
                    }}
                    className="p-2 bg-red-600 hover:bg-red-700 rounded-full"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="p-2">
                  <p className="text-sm text-gray-300 truncate">{image.filename}</p>
                  <p className="text-xs text-gray-500">{image.status}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
