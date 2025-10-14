import React, { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import { 
  Upload, 
  FileText, 
  Dna, 
  Brain, 
  Zap, 
  CheckCircle, 
  AlertCircle,
  Loader,
  Play,
  X,
  Download,
  Info
} from 'lucide-react';
import { analysisService } from '../services/api';
import { useWebSocket } from '../services/websocket';

const AnalysisPage = () => {
  const navigate = useNavigate();
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [workflowId, setWorkflowId] = useState(null);
  const [progress, setProgress] = useState({});
  const [socket, setSocket] = useState(null);
  const [error, setError] = useState(null);

  // WebSocket connection for real-time progress
  const { connectionState, lastMessage } = useWebSocket(workflowId);

  useEffect(() => {
    if (lastMessage && lastMessage.data) {
      const { data } = lastMessage;
      
      if (data.type === 'workflow-progress') {
        setProgress(data.progress);
      } else if (data.type === 'workflow-complete') {
        setIsAnalyzing(false);
        navigate(`/results/${workflowId}`);
      } else if (data.type === 'workflow-error') {
        setError(data.error);
        setIsAnalyzing(false);
      }
    }
  }, [lastMessage, navigate, workflowId]);

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file) {
      setUploadedFile(file);
      setError(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.fasta', '.fa', '.txt'],
      'application/octet-stream': ['.gb', '.gbk']
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024 // 10MB
  });

  const startAnalysis = async () => {
    if (!uploadedFile) return;

    setIsAnalyzing(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('sequence_file', uploadedFile);

      const response = await analysisService.startAnalysis(formData);
      setWorkflowId(response.data.workflow_id);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to start analysis');
      setIsAnalyzing(false);
    }
  };

  const loadSampleData = async (sampleType) => {
    try {
      const response = await analysisService.getSampleData();
      const sampleFile = response.data.samples.find(s => s.type === sampleType);
      
      if (sampleFile) {
        // Create a mock file object for the sample
        const mockFile = new File([sampleFile.content], sampleFile.filename, {
          type: 'text/plain'
        });
        setUploadedFile(mockFile);
        setError(null);
      }
    } catch (err) {
      setError('Failed to load sample data');
    }
  };

  const removeFile = () => {
    setUploadedFile(null);
    setError(null);
  };

  const agents = [
    {
      name: 'GenomicsAgent',
      description: 'Analyzing DNA sequence for genes and mutations',
      icon: Dna,
      color: 'from-green-500 to-emerald-500'
    },
    {
      name: 'ProteomicsAgent', 
      description: 'Predicting protein structure and function',
      icon: Brain,
      color: 'from-blue-500 to-cyan-500'
    },
    {
      name: 'LiteratureAgent',
      description: 'Researching scientific literature',
      icon: FileText,
      color: 'from-purple-500 to-pink-500'
    },
    {
      name: 'DrugAgent',
      description: 'Identifying drug candidates and clinical trials',
      icon: Zap,
      color: 'from-orange-500 to-red-500'
    },
    {
      name: 'DecisionAgent',
      description: 'Generating comprehensive medical report',
      icon: CheckCircle,
      color: 'from-indigo-500 to-purple-500'
    }
  ];

  const getAgentStatus = (agentName) => {
    const agentProgress = progress[agentName.toLowerCase()];
    if (!agentProgress) return 'pending';
    if (agentProgress.status === 'completed') return 'completed';
    if (agentProgress.status === 'processing') return 'processing';
    if (agentProgress.status === 'failed') return 'failed';
    return 'pending';
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Genomics Analysis
        </h1>
        <p className="text-lg text-gray-600">
          Upload your DNA sequence file and let our AI agents analyze it autonomously
        </p>
      </div>

      {/* File Upload Section */}
      {!isAnalyzing && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-lg p-8"
        >
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">
            Upload DNA Sequence File
          </h2>

          {!uploadedFile ? (
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all duration-200 ${
                isDragActive
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
              }`}
            >
              <input {...getInputProps()} />
              <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              
              {isDragActive ? (
                <p className="text-lg text-blue-600 font-medium">
                  Drop your DNA sequence file here...
                </p>
              ) : (
                <div>
                  <p className="text-lg text-gray-600 mb-2">
                    Drag and drop your DNA sequence file here, or click to browse
                  </p>
                  <p className="text-sm text-gray-500">
                    Supports FASTA (.fasta, .fa), GenBank (.gb, .gbk), and text files
                  </p>
                  <p className="text-sm text-gray-500">
                    Maximum file size: 10MB
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-gray-50 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <FileText className="h-8 w-8 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{uploadedFile.name}</p>
                    <p className="text-sm text-gray-500">
                      {(uploadedFile.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
                <button
                  onClick={removeFile}
                  className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {uploadedFile && (
            <div className="mt-6 flex justify-center">
              <button
                onClick={startAnalysis}
                disabled={!uploadedFile}
                className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-3 rounded-lg font-semibold text-lg hover:shadow-lg transform hover:scale-105 transition-all duration-200 flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                <Play className="h-5 w-5" />
                <span>Start Analysis</span>
              </button>
            </div>
          )}
        </motion.div>
      )}

      {/* Analysis Progress */}
      <AnimatePresence>
        {isAnalyzing && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-white rounded-xl shadow-lg p-8"
          >
            <div className="text-center mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                Analysis in Progress
              </h2>
              <p className="text-gray-600">
                Our AI agents are working autonomously to analyze your sequence
              </p>
            </div>

            <div className="space-y-6">
              {agents.map((agent, index) => {
                const Icon = agent.icon;
                const status = getAgentStatus(agent.name);
                
                return (
                  <motion.div
                    key={agent.name}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center space-x-4 p-4 rounded-lg border border-gray-200"
                  >
                    <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${agent.color} flex items-center justify-center`}>
                      <Icon className="h-6 w-6 text-white" />
                    </div>
                    
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{agent.name}</h3>
                      <p className="text-sm text-gray-600">{agent.description}</p>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {status === 'completed' && (
                        <CheckCircle className="h-6 w-6 text-green-500" />
                      )}
                      {status === 'processing' && (
                        <Loader className="h-6 w-6 text-blue-500 animate-spin" />
                      )}
                      {status === 'failed' && (
                        <AlertCircle className="h-6 w-6 text-red-500" />
                      )}
                      {status === 'pending' && (
                        <div className="h-6 w-6 rounded-full border-2 border-gray-300" />
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </div>

            {progress.overall && (
              <div className="mt-8">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">Overall Progress</span>
                  <span className="text-sm text-gray-500">{progress.overall.percentage}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <motion.div
                    className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress.overall.percentage}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sample Files Section */}
      {!isAnalyzing && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-8"
        >
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            Try Sample Data
          </h2>
          <p className="text-gray-600 mb-6">
            Don't have a DNA sequence file? Try our sample data to see the system in action.
          </p>
          
          <div className="grid md:grid-cols-2 gap-4">
            <button 
              onClick={() => loadSampleData('brca1')}
              className="p-4 bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all duration-200 text-left group"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-gray-900">BRCA1 Gene Sample</h3>
                <Download className="h-4 w-4 text-gray-400 group-hover:text-blue-500" />
              </div>
              <p className="text-sm text-gray-600 mb-2">Breast cancer susceptibility gene sequence</p>
              <div className="flex items-center space-x-2 text-xs text-gray-500">
                <Info className="h-3 w-3" />
                <span>Contains pathogenic variants</span>
              </div>
            </button>
            
            <button 
              onClick={() => loadSampleData('tp53')}
              className="p-4 bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all duration-200 text-left group"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-gray-900">TP53 Gene Sample</h3>
                <Download className="h-4 w-4 text-gray-400 group-hover:text-blue-500" />
              </div>
              <p className="text-sm text-gray-600 mb-2">Tumor suppressor gene sequence</p>
              <div className="flex items-center space-x-2 text-xs text-gray-500">
                <Info className="h-3 w-3" />
                <span>Includes missense mutations</span>
              </div>
            </button>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default AnalysisPage;