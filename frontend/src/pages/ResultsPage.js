import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  FileText, 
  Download, 
  Share2, 
  Dna, 
  Brain, 
  Zap, 
  AlertTriangle,
  CheckCircle,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Pill,
  BookOpen,
  Activity,
  Eye,
  Copy,
  Filter,
  Search
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  ScatterChart,
  Scatter
} from 'recharts';
import ReactMarkdown from 'react-markdown';
import { analysisService, handleApiError } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import GenomicsVisualization from '../components/GenomicsVisualization';
import MedicalReportViewer from '../components/MedicalReportViewer';

const ResultsPage = () => {
  const { workflowId } = useParams();
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [expandedSections, setExpandedSections] = useState({});

  useEffect(() => {
    fetchResults();
  }, [workflowId]);

  const fetchResults = async () => {
    try {
      const response = await analysisService.getAnalysisResults(workflowId);
      setResults(response.data);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const downloadReport = async (format = 'pdf') => {
    try {
      const response = await analysisService.downloadReport(workflowId, format);
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `biomerkin-report-${workflowId}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Failed to download report:', err);
      setError('Failed to download report');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      // Could add a toast notification here
      console.log('Copied to clipboard');
    });
  };

  const shareResults = () => {
    const shareUrl = window.location.href;
    if (navigator.share) {
      navigator.share({
        title: 'Biomerkin Analysis Results',
        text: 'Check out my genomics analysis results from Biomerkin AI',
        url: shareUrl
      });
    } else {
      copyToClipboard(shareUrl);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner 
          type="genomics" 
          size="large" 
          message="Loading analysis results..." 
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Results</h2>
        <p className="text-gray-600 mb-6">{error}</p>
        <Link
          to="/analysis"
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Start New Analysis
        </Link>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', name: 'Overview', icon: Activity },
    { id: 'genomics', name: 'Genomics', icon: Dna },
    { id: 'proteomics', name: 'Proteomics', icon: Brain },
    { id: 'literature', name: 'Literature', icon: BookOpen },
    { id: 'drugs', name: 'Drug Candidates', icon: Pill },
    { id: 'report', name: 'Medical Report', icon: FileText }
  ];

  // Mock data for demonstration - replace with actual results
  const mockResults = {
    overview: {
      analysisId: workflowId,
      completedAt: new Date().toISOString(),
      totalGenes: 15,
      significantVariants: 3,
      drugCandidates: 8,
      literatureArticles: 24,
      riskScore: 'Moderate'
    },
    genomics: {
      genes: [
        { name: 'BRCA1', location: 'chr17:43044295-43125483', function: 'DNA repair', variants: 2 },
        { name: 'TP53', location: 'chr17:7661779-7687550', function: 'Tumor suppressor', variants: 1 },
        { name: 'EGFR', location: 'chr7:55019017-55211628', function: 'Growth factor receptor', variants: 0 }
      ],
      variants: [
        { gene: 'BRCA1', position: 'c.5266dupC', type: 'Frameshift', significance: 'Pathogenic' },
        { gene: 'BRCA1', position: 'c.181T>G', type: 'Missense', significance: 'VUS' },
        { gene: 'TP53', position: 'c.524G>A', type: 'Missense', significance: 'Likely Pathogenic' }
      ]
    },
    proteomics: {
      proteins: [
        { name: 'BRCA1', structure: 'Available', domains: ['RING', 'BRCT'], interactions: 15 },
        { name: 'TP53', structure: 'Available', domains: ['DNA-binding', 'Tetramerization'], interactions: 23 },
        { name: 'EGFR', structure: 'Available', domains: ['Kinase', 'Receptor'], interactions: 18 }
      ]
    },
    literature: {
      summary: "Recent studies have identified BRCA1 and TP53 variants as significant risk factors for hereditary breast and ovarian cancer syndrome. The identified variants show strong association with increased cancer susceptibility.",
      keyFindings: [
        "BRCA1 c.5266dupC is a well-established pathogenic variant",
        "TP53 c.524G>A shows functional impact on DNA binding",
        "Combined variants increase cancer risk significantly"
      ],
      articles: [
        { title: "BRCA1 variants in hereditary breast cancer", journal: "Nature Genetics", year: 2023 },
        { title: "TP53 mutations and cancer susceptibility", journal: "Cell", year: 2023 }
      ]
    },
    drugs: {
      candidates: [
        { name: 'Olaparib', target: 'PARP', phase: 'Approved', indication: 'BRCA-mutated cancers' },
        { name: 'Talazoparib', target: 'PARP', phase: 'Approved', indication: 'BRCA-mutated breast cancer' },
        { name: 'Rucaparib', target: 'PARP', phase: 'Approved', indication: 'BRCA-mutated ovarian cancer' }
      ]
    },
    report: {
      content: `# Genomics Analysis Report

## Patient Information
- Analysis ID: ${workflowId}
- Analysis Date: ${new Date().toLocaleDateString()}
- Analysis Type: Comprehensive Genomics Panel

## Executive Summary
This analysis identified several clinically significant genetic variants that may impact cancer susceptibility and treatment options.

## Key Findings
- **High-risk variants identified**: 2 pathogenic/likely pathogenic variants
- **Genes of interest**: BRCA1, TP53
- **Recommended follow-up**: Genetic counseling and enhanced screening

## Detailed Analysis
### Genomics Results
The analysis identified variants in genes associated with hereditary cancer syndromes, particularly BRCA1 and TP53.

### Treatment Implications
Based on the identified variants, PARP inhibitor therapy may be particularly effective.

## Recommendations
1. Genetic counseling consultation
2. Enhanced cancer screening protocol
3. Consider PARP inhibitor therapy if cancer develops
4. Family cascade testing recommended`
    }
  };

  const variantData = [
    { name: 'Pathogenic', value: 1, color: '#ef4444' },
    { name: 'Likely Pathogenic', value: 1, color: '#f97316' },
    { name: 'VUS', value: 1, color: '#eab308' },
    { name: 'Benign', value: 12, color: '#22c55e' }
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Analysis Results
            </h1>
            <p className="text-gray-600">
              Analysis ID: {workflowId} • Completed: {new Date().toLocaleDateString()}
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="relative group">
              <button
                onClick={() => downloadReport('pdf')}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
              >
                <Download className="h-4 w-4" />
                <span>Download</span>
                <ChevronDown className="h-3 w-3" />
              </button>
              
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
                <button
                  onClick={() => downloadReport('pdf')}
                  className="w-full text-left px-4 py-2 hover:bg-gray-50 rounded-t-lg"
                >
                  PDF Report
                </button>
                <button
                  onClick={() => downloadReport('json')}
                  className="w-full text-left px-4 py-2 hover:bg-gray-50"
                >
                  JSON Data
                </button>
                <button
                  onClick={() => downloadReport('csv')}
                  className="w-full text-left px-4 py-2 hover:bg-gray-50 rounded-b-lg"
                >
                  CSV Export
                </button>
              </div>
            </div>
            
            <button 
              onClick={shareResults}
              className="border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors flex items-center space-x-2"
            >
              <Share2 className="h-4 w-4" />
              <span>Share</span>
            </button>
            
            <button 
              onClick={() => copyToClipboard(workflowId)}
              className="border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors flex items-center space-x-2"
            >
              <Copy className="h-4 w-4" />
              <span>Copy ID</span>
            </button>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white rounded-xl shadow-lg">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </nav>
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-blue-600 text-sm font-medium">Total Genes</p>
                      <p className="text-2xl font-bold text-blue-900">{mockResults.overview.totalGenes}</p>
                    </div>
                    <Dna className="h-8 w-8 text-blue-500" />
                  </div>
                </div>
                
                <div className="bg-gradient-to-r from-red-50 to-red-100 rounded-lg p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-red-600 text-sm font-medium">Significant Variants</p>
                      <p className="text-2xl font-bold text-red-900">{mockResults.overview.significantVariants}</p>
                    </div>
                    <AlertTriangle className="h-8 w-8 text-red-500" />
                  </div>
                </div>
                
                <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-green-600 text-sm font-medium">Drug Candidates</p>
                      <p className="text-2xl font-bold text-green-900">{mockResults.overview.drugCandidates}</p>
                    </div>
                    <Pill className="h-8 w-8 text-green-500" />
                  </div>
                </div>
                
                <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-purple-600 text-sm font-medium">Literature Articles</p>
                      <p className="text-2xl font-bold text-purple-900">{mockResults.overview.literatureArticles}</p>
                    </div>
                    <BookOpen className="h-8 w-8 text-purple-500" />
                  </div>
                </div>
              </div>

              <div className="grid lg:grid-cols-2 gap-6">
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Variant Classification</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={variantData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {variantData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="flex flex-wrap gap-2 mt-4">
                    {variantData.map((item, index) => (
                      <div key={index} className="flex items-center space-x-2">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: item.color }}
                        />
                        <span className="text-sm text-gray-600">{item.name} ({item.value})</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Assessment</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Overall Risk Score</span>
                      <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                        {mockResults.overview.riskScore}
                      </span>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Cancer Susceptibility</span>
                        <span>High</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-red-500 h-2 rounded-full" style={{ width: '75%' }}></div>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Treatment Response</span>
                        <span>Good</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-green-500 h-2 rounded-full" style={{ width: '80%' }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Genomics Tab */}
          {activeTab === 'genomics' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <GenomicsVisualization data={mockResults.genomics} />
            </motion.div>
          )}

          {/* Proteomics Tab */}
          {activeTab === 'proteomics' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <div className="grid lg:grid-cols-2 gap-6">
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Protein Structures</h3>
                  <div className="space-y-4">
                    {mockResults.proteomics.proteins.map((protein, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <h4 className="font-medium text-gray-900">{protein.name}</h4>
                          <p className="text-sm text-gray-600">
                            Domains: {protein.domains.join(', ')}
                          </p>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium text-green-600">
                            {protein.structure}
                          </div>
                          <div className="text-xs text-gray-500">
                            {protein.interactions} interactions
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Functional Impact</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={mockResults.proteomics.proteins}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="interactions" fill="#3b82f6" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </motion.div>
          )}

          {/* Literature Tab */}
          {activeTab === 'literature' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Literature Summary</h3>
                <p className="text-gray-700 mb-6">{mockResults.literature.summary}</p>
                
                <h4 className="font-medium text-gray-900 mb-3">Key Findings</h4>
                <ul className="space-y-2 mb-6">
                  {mockResults.literature.keyFindings.map((finding, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{finding}</span>
                    </li>
                  ))}
                </ul>
                
                <h4 className="font-medium text-gray-900 mb-3">Recent Articles</h4>
                <div className="space-y-3">
                  {mockResults.literature.articles.map((article, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <h5 className="font-medium text-gray-900">{article.title}</h5>
                        <p className="text-sm text-gray-600">{article.journal} • {article.year}</p>
                      </div>
                      <ExternalLink className="h-4 w-4 text-gray-400" />
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {/* Drugs Tab */}
          {activeTab === 'drugs' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Drug Candidates</h3>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {mockResults.drugs.candidates.map((drug, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-900">{drug.name}</h4>
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                          {drug.phase}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">Target: {drug.target}</p>
                      <p className="text-sm text-gray-700">{drug.indication}</p>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {/* Medical Report Tab */}
          {activeTab === 'report' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="h-screen"
            >
              <MedicalReportViewer 
                reportData={mockResults.report} 
                workflowId={workflowId}
              />
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResultsPage;