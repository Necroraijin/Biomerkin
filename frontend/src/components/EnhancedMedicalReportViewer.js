import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  Download,
  Share2,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  CheckCircle,
  Info,
  TrendingUp,
  Users,
  Activity,
  Target,
  Heart,
  Brain,
  Dna,
  Pill
} from 'lucide-react';

/**
 * Enhanced Medical Report Viewer
 * Displays comprehensive analysis results with interactive sections
 */
const EnhancedMedicalReportViewer = ({ report, workflowId }) => {
  const [expandedSections, setExpandedSections] = useState({
    executive: true,
    genomics: false,
    proteomics: false,
    literature: false,
    recommendations: true,
    evidence: false
  });
  const [selectedTab, setSelectedTab] = useState('overview');
  const [showConfidential, setShowConfidential] = useState(false);

  // Parse report data
  const reportData = useMemo(() => {
    if (!report) return null;
    
    // Handle different report formats
    if (typeof report === 'string') {
      try {
        return JSON.parse(report);
      } catch {
        return { report_text: report };
      }
    }
    
    return report;
  }, [report]);

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const downloadReport = async (format = 'pdf') => {
    try {
      const response = await fetch(`/api/workflows/${workflowId}/report?format=${format}`);
      const blob = await response.blob();
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `medical_report_${workflowId}.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const shareReport = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Biomerkin Medical Report',
          text: 'Comprehensive genomic analysis report',
          url: window.location.href
        });
      } catch (error) {
        console.log('Share cancelled');
      }
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(window.location.href);
      alert('Report link copied to clipboard');
    }
  };

  if (!reportData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No report data available</p>
        </div>
      </div>
    );
  }

  const sections = [
    { id: 'executive', title: 'Executive Summary', icon: TrendingUp, color: 'blue' },
    { id: 'genomics', title: 'Genomic Analysis', icon: Dna, color: 'green' },
    { id: 'proteomics', title: 'Protein Analysis', icon: Activity, color: 'purple' },
    { id: 'literature', title: 'Literature Review', icon: FileText, color: 'orange' },
    { id: 'recommendations', title: 'Recommendations', icon: Target, color: 'red' },
    { id: 'evidence', title: 'Evidence Base', icon: Info, color: 'gray' }
  ];

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Medical Analysis Report</h1>
            <p className="text-gray-600 mt-1">
              Workflow ID: {workflowId} • Generated: {new Date().toLocaleDateString()}
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => setShowConfidential(!showConfidential)}
              className="flex items-center px-3 py-2 text-sm border rounded-lg hover:bg-gray-50"
            >
              {showConfidential ? <EyeOff className="w-4 h-4 mr-2" /> : <Eye className="w-4 h-4 mr-2" />}
              {showConfidential ? 'Hide' : 'Show'} Confidential
            </button>
            <button
              onClick={shareReport}
              className="flex items-center px-3 py-2 text-sm border rounded-lg hover:bg-gray-50"
            >
              <Share2 className="w-4 h-4 mr-2" />
              Share
            </button>
            <div className="relative">
              <button
                onClick={() => downloadReport('pdf')}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Download className="w-4 h-4 mr-2" />
                Download PDF
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg">
        {[
          { id: 'overview', label: 'Overview', icon: Eye },
          { id: 'detailed', label: 'Detailed Analysis', icon: FileText },
          { id: 'visualizations', label: 'Visualizations', icon: TrendingUp }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setSelectedTab(tab.id)}
            className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedTab === tab.id
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <tab.icon className="w-4 h-4 mr-2" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Report Content */}
      <div className="space-y-4">
        {selectedTab === 'overview' && (
          <OverviewTab reportData={reportData} sections={sections} expandedSections={expandedSections} toggleSection={toggleSection} />
        )}
        
        {selectedTab === 'detailed' && (
          <DetailedTab reportData={reportData} sections={sections} expandedSections={expandedSections} toggleSection={toggleSection} />
        )}
        
        {selectedTab === 'visualizations' && (
          <VisualizationsTab reportData={reportData} />
        )}
      </div>
    </div>
  );
};

// Overview Tab Component
const OverviewTab = ({ reportData, sections, expandedSections, toggleSection }) => (
  <div className="space-y-4">
    {/* Key Metrics */}
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <MetricCard
        title="Genes Analyzed"
        value={reportData.genomics?.genes?.length || 0}
        icon={Dna}
        color="blue"
      />
      <MetricCard
        title="Mutations Found"
        value={reportData.genomics?.mutations?.length || 0}
        icon={AlertTriangle}
        color="red"
      />
      <MetricCard
        title="Proteins Identified"
        value={reportData.proteomics?.length || 0}
        icon={Activity}
        color="green"
      />
      <MetricCard
        title="Risk Level"
        value={reportData.risk_assessment?.overall_risk || 'Low'}
        icon={Heart}
        color="purple"
      />
    </div>

    {/* Executive Summary */}
    <ReportSection
      id="executive"
      title="Executive Summary"
      icon={TrendingUp}
      color="blue"
      expanded={expandedSections.executive}
      onToggle={() => toggleSection('executive')}
    >
      <div className="prose max-w-none">
        <p className="text-gray-700 leading-relaxed">
          {reportData.executive_summary || 
           "This comprehensive genomic analysis reveals key genetic variants and their potential clinical significance. The analysis combines genomic sequencing, protein structure prediction, and literature review to provide personalized medical insights."}
        </p>
      </div>
    </ReportSection>

    {/* Key Findings */}
    <ReportSection
      id="findings"
      title="Key Findings"
      icon={CheckCircle}
      color="green"
      expanded={true}
    >
      <div className="space-y-3">
        {reportData.key_findings?.map((finding, index) => (
          <div key={index} className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg">
            <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-green-900">{finding.title}</p>
              <p className="text-sm text-green-700">{finding.description}</p>
            </div>
          </div>
        )) || (
          <div className="text-gray-500 italic">No specific findings reported</div>
        )}
      </div>
    </ReportSection>
  </div>
);

// Detailed Tab Component
const DetailedTab = ({ reportData, sections, expandedSections, toggleSection }) => (
  <div className="space-y-4">
    {sections.map(section => (
      <ReportSection
        key={section.id}
        id={section.id}
        title={section.title}
        icon={section.icon}
        color={section.color}
        expanded={expandedSections[section.id]}
        onToggle={() => toggleSection(section.id)}
      >
        <SectionContent sectionId={section.id} reportData={reportData} />
      </ReportSection>
    ))}
  </div>
);

// Visualizations Tab Component
const VisualizationsTab = ({ reportData }) => (
  <div className="space-y-6">
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <h3 className="text-lg font-semibold mb-4">Analysis Overview</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h4 className="font-medium mb-2">Mutation Distribution</h4>
          <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
            <span className="text-gray-500">Mutation chart would be here</span>
          </div>
        </div>
        <div>
          <h4 className="font-medium mb-2">Gene Expression</h4>
          <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
            <span className="text-gray-500">Expression chart would be here</span>
          </div>
        </div>
      </div>
    </div>
  </div>
);

// Report Section Component
const ReportSection = ({ id, title, icon: Icon, color, expanded, onToggle, children }) => (
  <div className="bg-white rounded-lg shadow-sm border">
    <button
      onClick={onToggle}
      className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors"
    >
      <div className="flex items-center space-x-3">
        <div className={`p-2 rounded-lg bg-${color}-100`}>
          <Icon className={`w-5 h-5 text-${color}-600`} />
        </div>
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      </div>
      {onToggle && (
        expanded ? <ChevronDown className="w-5 h-5 text-gray-500" /> : <ChevronRight className="w-5 h-5 text-gray-500" />
      )}
    </button>
    
    <AnimatePresence>
      {expanded && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="overflow-hidden"
        >
          <div className="px-4 pb-4">
            {children}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  </div>
);

// Section Content Component
const SectionContent = ({ sectionId, reportData }) => {
  switch (sectionId) {
    case 'genomics':
      return <GenomicsContent data={reportData.genomics} />;
    case 'proteomics':
      return <ProteomicsContent data={reportData.proteomics} />;
    case 'literature':
      return <LiteratureContent data={reportData.literature} />;
    case 'recommendations':
      return <RecommendationsContent data={reportData.recommendations} />;
    case 'evidence':
      return <EvidenceContent data={reportData.evidence} />;
    default:
      return <div className="text-gray-500">Content not available</div>;
  }
};

// Content Components
const GenomicsContent = ({ data }) => (
  <div className="space-y-4">
    {data?.genes?.map((gene, index) => (
      <div key={index} className="border rounded-lg p-4">
        <h4 className="font-medium">{gene.name || `Gene ${index + 1}`}</h4>
        <p className="text-sm text-gray-600">Position: {gene.position}</p>
        <p className="text-sm text-gray-600">Function: {gene.function || 'Unknown'}</p>
      </div>
    )) || <div className="text-gray-500">No genomic data available</div>}
  </div>
);

const ProteomicsContent = ({ data }) => (
  <div className="space-y-4">
    {data?.map((protein, index) => (
      <div key={index} className="border rounded-lg p-4">
        <h4 className="font-medium">{protein.name || `Protein ${index + 1}`}</h4>
        <p className="text-sm text-gray-600">Length: {protein.length} amino acids</p>
        <p className="text-sm text-gray-600">Function: {protein.function || 'Unknown'}</p>
      </div>
    )) || <div className="text-gray-500">No proteomic data available</div>}
  </div>
);

const LiteratureContent = ({ data }) => (
  <div className="space-y-4">
    {data?.articles?.map((article, index) => (
      <div key={index} className="border rounded-lg p-4">
        <h4 className="font-medium">{article.title}</h4>
        <p className="text-sm text-gray-600">Authors: {article.authors}</p>
        <p className="text-sm text-gray-600">Journal: {article.journal}</p>
      </div>
    )) || <div className="text-gray-500">No literature data available</div>}
  </div>
);

const RecommendationsContent = ({ data }) => (
  <div className="space-y-4">
    {data?.map((rec, index) => (
      <div key={index} className="border-l-4 border-blue-500 pl-4">
        <h4 className="font-medium">{rec.title}</h4>
        <p className="text-sm text-gray-600">{rec.description}</p>
        <p className="text-xs text-gray-500 mt-1">Priority: {rec.priority}</p>
      </div>
    )) || <div className="text-gray-500">No recommendations available</div>}
  </div>
);

const EvidenceContent = ({ data }) => (
  <div className="space-y-4">
    {data?.map((evidence, index) => (
      <div key={index} className="border rounded-lg p-4">
        <h4 className="font-medium">{evidence.source}</h4>
        <p className="text-sm text-gray-600">{evidence.description}</p>
        <p className="text-xs text-gray-500">Confidence: {evidence.confidence}%</p>
      </div>
    )) || <div className="text-gray-500">No evidence data available</div>}
  </div>
);

// Metric Card Component
const MetricCard = ({ title, value, icon: Icon, color }) => (
  <div className="bg-white rounded-lg shadow-sm border p-4">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-gray-600">{title}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
      </div>
      <div className={`p-3 rounded-lg bg-${color}-100`}>
        <Icon className={`w-6 h-6 text-${color}-600`} />
      </div>
    </div>
  </div>
);

export default EnhancedMedicalReportViewer;
