import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  FileText,
  CheckCircle,
  AlertCircle,
  Info,
  X,
  Download,
  Database,
  Sparkles
} from 'lucide-react';

/**
 * Enhanced Dataset Upload Component
 * Provides validation, format detection, and quality assessment for judge datasets
 */
const EnhancedDatasetUpload = ({ onFileSelect, onValidationComplete }) => {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [isValidating, setIsValidating] = useState(false);
  const [validationError, setValidationError] = useState(null);

  const validateDataset = async (file) => {
    setIsValidating(true);
    setValidationError(null);

    try {
      // Create FormData for validation
      const formData = new FormData();
      formData.append('file', file);

      // Call validation API
      const response = await fetch('/api/validate-dataset', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Validation failed');
      }

      const result = await response.json();
      setValidationResult(result);
      
      if (onValidationComplete) {
        onValidationComplete(result);
      }

      return result;
    } catch (error) {
      setValidationError(error.message);
      return null;
    } finally {
      setIsValidating(false);
    }
  };

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file) {
      setUploadedFile(file);
      setValidationResult(null);
      
      // Automatically validate the file
      const validation = await validateDataset(file);
      
      if (validation && validation.is_valid && onFileSelect) {
        onFileSelect(file, validation);
      }
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.fasta', '.fa', '.fna', '.ffn', '.faa', '.txt'],
      'application/octet-stream': ['.gb', '.gbk', '.genbank']
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024 // 50MB - support larger datasets
  });

  const removeFile = () => {
    setUploadedFile(null);
    setValidationResult(null);
    setValidationError(null);
  };

  const getQualityColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getQualityBadge = (score) => {
    if (score >= 80) return { label: 'Excellent', color: 'bg-green-100 text-green-800' };
    if (score >= 60) return { label: 'Good', color: 'bg-yellow-100 text-yellow-800' };
    return { label: 'Needs Review', color: 'bg-red-100 text-red-800' };
  };

  return (
    <div className="space-y-4">
      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
          transition-all duration-200
          ${isDragActive 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
          }
          ${uploadedFile ? 'bg-gray-50' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center space-y-4">
          {!uploadedFile ? (
            <>
              <div className="p-4 bg-blue-100 rounded-full">
                <Upload className="w-8 h-8 text-blue-600" />
              </div>
              <div>
                <p className="text-lg font-semibold text-gray-700">
                  {isDragActive ? 'Drop your dataset here' : 'Upload Your Dataset'}
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  Drag & drop or click to browse
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Supports: FASTA, GenBank, and raw sequence files (up to 50MB)
                </p>
              </div>
            </>
          ) : (
            <div className="w-full">
              <div className="flex items-center justify-between bg-white rounded-lg p-4 shadow-sm">
                <div className="flex items-center space-x-3">
                  <FileText className="w-8 h-8 text-blue-600" />
                  <div className="text-left">
                    <p className="font-medium text-gray-900">{uploadedFile.name}</p>
                    <p className="text-sm text-gray-500">
                      {(uploadedFile.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile();
                  }}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Validation Progress */}
      <AnimatePresence>
        {isValidating && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-blue-50 border border-blue-200 rounded-lg p-4"
          >
            <div className="flex items-center space-x-3">
              <div className="animate-spin">
                <Sparkles className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="font-medium text-blue-900">Validating Dataset...</p>
                <p className="text-sm text-blue-700">
                  Checking format, quality, and compatibility
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Validation Results */}
      <AnimatePresence>
        {validationResult && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={`rounded-lg p-6 ${
              validationResult.is_valid
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
            }`}
          >
            <div className="space-y-4">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  {validationResult.is_valid ? (
                    <CheckCircle className="w-6 h-6 text-green-600" />
                  ) : (
                    <AlertCircle className="w-6 h-6 text-red-600" />
                  )}
                  <div>
                    <h3 className={`font-semibold text-lg ${
                      validationResult.is_valid ? 'text-green-900' : 'text-red-900'
                    }`}>
                      {validationResult.is_valid ? 'Dataset Valid' : 'Validation Failed'}
                    </h3>
                    <p className={`text-sm ${
                      validationResult.is_valid ? 'text-green-700' : 'text-red-700'
                    }`}>
                      {validationResult.is_valid 
                        ? 'Your dataset is ready for analysis'
                        : 'Please review the errors below'
                      }
                    </p>
                  </div>
                </div>
                
                {/* Quality Badge */}
                {validationResult.quality_score !== undefined && (
                  <div className="text-right">
                    <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${
                      getQualityBadge(validationResult.quality_score).color
                    }`}>
                      {getQualityBadge(validationResult.quality_score).label}
                    </span>
                    <p className={`text-2xl font-bold mt-1 ${getQualityColor(validationResult.quality_score)}`}>
                      {validationResult.quality_score.toFixed(1)}%
                    </p>
                  </div>
                )}
              </div>

              {/* Dataset Information */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white rounded-lg p-3 shadow-sm">
                  <p className="text-xs text-gray-500 uppercase">Format</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {validationResult.file_format || 'Unknown'}
                  </p>
                </div>
                <div className="bg-white rounded-lg p-3 shadow-sm">
                  <p className="text-xs text-gray-500 uppercase">Sequences</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {validationResult.sequence_count || 0}
                  </p>
                </div>
                <div className="bg-white rounded-lg p-3 shadow-sm">
                  <p className="text-xs text-gray-500 uppercase">Total Length</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {validationResult.total_length?.toLocaleString() || 0} bp
                  </p>
                </div>
                {validationResult.gc_content !== undefined && (
                  <div className="bg-white rounded-lg p-3 shadow-sm">
                    <p className="text-xs text-gray-500 uppercase">GC Content</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {validationResult.gc_content.toFixed(1)}%
                    </p>
                  </div>
                )}
              </div>

              {/* Warnings */}
              {validationResult.warnings && validationResult.warnings.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <div className="flex items-start space-x-2">
                    <Info className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="font-medium text-yellow-900">Warnings:</p>
                      <ul className="mt-1 text-sm text-yellow-800 space-y-1">
                        {validationResult.warnings.map((warning, idx) => (
                          <li key={idx}>• {warning}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {/* Errors */}
              {validationResult.errors && validationResult.errors.length > 0 && (
                <div className="bg-red-100 border border-red-300 rounded-lg p-3">
                  <div className="flex items-start space-x-2">
                    <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="font-medium text-red-900">Errors:</p>
                      <ul className="mt-1 text-sm text-red-800 space-y-1">
                        {validationResult.errors.map((error, idx) => (
                          <li key={idx}>• {error}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Validation Error */}
      <AnimatePresence>
        {validationError && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="bg-red-50 border border-red-200 rounded-lg p-4"
          >
            <div className="flex items-center space-x-3">
              <AlertCircle className="w-5 h-5 text-red-600" />
              <p className="text-red-800">{validationError}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Information Panel */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <Database className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-900">
            <p className="font-medium mb-2">Supported Dataset Types:</p>
            <ul className="space-y-1 text-blue-800">
              <li>• <strong>FASTA</strong> - DNA/RNA/Protein sequences (.fasta, .fa, .fna, .faa)</li>
              <li>• <strong>GenBank</strong> - Annotated sequences (.gb, .gbk)</li>
              <li>• <strong>Raw Text</strong> - Plain sequence data (.txt)</li>
            </ul>
            <p className="mt-3 text-xs text-blue-700">
              The system automatically detects format and validates data quality for optimal analysis accuracy.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedDatasetUpload;

