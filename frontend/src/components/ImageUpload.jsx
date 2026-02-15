import { useState, useRef } from 'react'

function ImageUpload({ prompt, onSubmit, onSkip }) {
  const [preview, setPreview] = useState(null)
  const [imageData, setImageData] = useState(null)
  const [loading, setLoading] = useState(false)
  const fileInputRef = useRef(null)
  const cameraInputRef = useRef(null)
  
  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    
    await processImage(file)
  }
  
  const processImage = async (file) => {
    setLoading(true)
    
    try {
      // Create preview
      const previewUrl = URL.createObjectURL(file)
      setPreview(previewUrl)
      
      // Convert to base64
      const base64 = await fileToBase64(file)
      setImageData({
        base64: base64,
        mimeType: file.type || 'image/jpeg'
      })
    } catch (err) {
      console.error('Failed to process image:', err)
    } finally {
      setLoading(false)
    }
  }
  
  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => {
        // Remove the data URL prefix to get just the base64 data
        const base64 = reader.result.split(',')[1]
        resolve(base64)
      }
      reader.onerror = reject
      reader.readAsDataURL(file)
    })
  }
  
  const handleSubmit = () => {
    if (imageData) {
      onSubmit(imageData)
    }
  }
  
  const handleClear = () => {
    setPreview(null)
    setImageData(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
    if (cameraInputRef.current) cameraInputRef.current.value = ''
  }
  
  return (
    <div className="image-upload-overlay">
      <div className="image-upload-modal card">
        <div className="image-upload-header">
          <span className="image-upload-icon">📸</span>
          <h3>Add a Photo for Better Steps</h3>
        </div>
        
        <p className="image-upload-prompt">
          {prompt || "A photo would help me create more specific steps for you!"}
        </p>
        
        {!preview ? (
          <div className="image-upload-buttons">
            {/* Camera capture (mobile) */}
            <label className="btn btn-primary image-upload-btn">
              <span>📷 Take Photo</span>
              <input
                ref={cameraInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
              />
            </label>
            
            {/* File picker */}
            <label className="btn image-upload-btn">
              <span>🖼️ Choose from Gallery</span>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
              />
            </label>
          </div>
        ) : (
          <div className="image-preview-container">
            <img 
              src={preview} 
              alt="Preview" 
              className="image-preview"
            />
            <button 
              type="button"
              className="btn image-preview-clear"
              onClick={handleClear}
            >
              ✕ Remove
            </button>
          </div>
        )}
        
        {loading && (
          <div className="image-upload-loading">
            <span className="spinner"></span>
            Processing image...
          </div>
        )}
        
        <div className="image-upload-actions">
          {preview && imageData && (
            <button 
              type="button"
              className="btn btn-primary btn-large"
              onClick={handleSubmit}
              disabled={loading}
            >
              ✨ Use This Photo
            </button>
          )}
          
          <button 
            type="button"
            className="btn btn-text"
            onClick={onSkip}
            disabled={loading}
          >
            Skip, continue without photo
          </button>
        </div>
      </div>
    </div>
  )
}

export default ImageUpload
