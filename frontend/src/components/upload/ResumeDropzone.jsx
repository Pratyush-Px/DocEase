import { useState, useRef } from 'react';
import '../../styles/components/dropzone.css';

export default function ResumeDropzone({ file, setFile, error }) {
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragActive(false);
  };

  const validateAndSetFile = (selectedFile) => {
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
    } else {
      // In a real app we might set an error state here specifically for file type
      alert('Only PDF files are accepted.');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const onButtonClick = () => {
    fileInputRef.current.click();
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={`dropzone-wrapper ${error ? 'has-error' : ''}`}>
      <div 
        className={`dropzone ${isDragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={onButtonClick}
      >
        <input 
          ref={fileInputRef}
          type="file" 
          accept=".pdf,application/pdf" 
          onChange={handleChange} 
          style={{ display: 'none' }} 
        />
        
        {file ? (
          <div className="file-display slide-up-anim">
            <div className="file-icon">📄</div>
            <div className="file-details">
              <span className="file-name">{file.name}</span>
              <span className="file-size">{formatFileSize(file.size)}</span>
            </div>
            <div className="file-success">✅</div>
          </div>
        ) : (
          <div className="dropzone-content">
            <div className="upload-icon">⬆️</div>
            <p className="dropzone-text">Drag & drop your resume PDF</p>
            <span className="dropzone-sub">or click to browse</span>
          </div>
        )}
      </div>
      {error && <span className="input-error-msg">{error}</span>}
    </div>
  );
}
