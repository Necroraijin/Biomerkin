import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  FileText, 
  Download, 
  Printer, 
  Share2, 
  Eye,
  EyeOff,
  Maximize2,
  Minimize2,
  Search,
  BookOpen,
  AlertTriangle,
  CheckCircle,
  Info
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const MedicalReportViewer = ({ reportData, workflowId }) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showAnnotations, setShowAnnotations] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeSection, setActiveSection] = useState('summary');

  const reportSections = [
    { id: 'summary', title: 'Executive Summary', icon: FileText },
    { id: 'genomics', title: 'Genomics Analysis', icon: BookOpen },
    { id: 'clinical', title: 'Clinical Significance', icon: AlertTriangle },
    { id: 'recommendations', title: 'Recommendations', icon: CheckCircle },
    { id: 'references', title: 'References', icon: Info }
  ];

  const mockReport = {
    patientInfo: {
      id: workflowId,
      analysisDate: new Date().toLocaleDateString(),
      reportType: 'Comprehensive Genomics Analysis'
    },
    summary: `
# Executive Summary

This comprehensive genomics analysis has identified several clinically significant genetic variants that have important implications for cancer risk assessment and treatment planning.

## Key Findings
- **High-risk pathogenic variants identified**: 2 variants in BRCA1 and TP53 genes
- **Cancer susceptibility**: Significantly elevated risk for hereditary breast and ovarian cancer
- **Treatment implications**: PARP inhibitor therapy likely to be highly effective
- **Family implications**: Cascade genetic testing recommended for first-degree relatives

## Risk Assessment
Based on the identified genetic variants, this individual has a **HIGH** risk profile for hereditary cancer syndromes, particularly:
- Hereditary Breast and Ovarian Cancer (HBOC) syndrome
- Li-Fraumeni syndrome (partial features)

## Immediate Actions Required
1. Genetic counseling consultation within 2 weeks
2. Enhanced cancer screening protocol implementation
3. Discussion of risk-reducing surgical options
4. Family cascade testing coordination
    `,
    genomics: `
# Genomics Analysis Results

## Variant Summary
The analysis identified **29 total variants** across the analyzed genes, with **3 variants of clinical significance**.

### Pathogenic Variants

#### BRCA1 c.5266dupC (p.Gln1756ProfsTer74)
- **Classification**: Pathogenic (Class 5)
- **Frequency**: Rare (<0.01% in population)
- **Clinical Significance**: Well-established pathogenic variant associated with high cancer risk
- **Functional Impact**: Frameshift mutation leading to premature protein truncation
- **Cancer Risk**: 
  - Breast cancer: 72% lifetime risk
  - Ovarian cancer: 44% lifetime risk

#### TP53 c.524G>A (p.Arg175His)
- **Classification**: Likely Pathogenic (Class 4)
- **Frequency**: Rare (<0.001% in population)
- **Clinical Significance**: Hotspot mutation in DNA-binding domain
- **Functional Impact**: Impaired DNA binding and transcriptional activity
- **Cancer Risk**: Associated with Li-Fraumeni spectrum cancers

### Variants of Uncertain Significance (VUS)

#### BRCA1 c.181T>G (p.Cys61Gly)
- **Classification**: VUS (Class 3)
- **Frequency**: Very rare
- **Clinical Significance**: Insufficient evidence for pathogenicity
- **Recommendation**: Periodic reclassification as evidence emerges
    `,
    clinical: `
# Clinical Significance and Implications

## Cancer Risk Assessment

### Hereditary Breast and Ovarian Cancer (HBOC)
The identified BRCA1 pathogenic variant confers significantly elevated cancer risks:

**Breast Cancer Risk**
- Lifetime risk: ~72% (vs. 12% general population)
- Early onset typical (before age 50)
- Higher grade, triple-negative subtype common

**Ovarian Cancer Risk**
- Lifetime risk: ~44% (vs. 1.3% general population)
- Typically high-grade serous carcinoma
- Often diagnosed at advanced stage

### Li-Fraumeni Syndrome Features
The TP53 variant may contribute to:
- Early-onset cancers
- Multiple primary cancers
- Diverse cancer spectrum (sarcomas, brain tumors, adrenocortical carcinoma)

## Treatment Implications

### Therapeutic Opportunities
1. **PARP Inhibitor Sensitivity**
   - Olaparib, talazoparib, rucaparib likely highly effective
   - Both treatment and prevention applications
   
2. **Platinum Sensitivity**
   - Enhanced response to platinum-based chemotherapy
   - Important for treatment planning

3. **Immunotherapy Considerations**
   - Potential enhanced response to checkpoint inhibitors
   - Tumor mutational burden implications

### Surgical Considerations
- Risk-reducing bilateral mastectomy (90% risk reduction)
- Risk-reducing bilateral salpingo-oophorectomy (85-90% ovarian cancer risk reduction)
- Timing considerations based on family planning
    `,
    recommendations: `
# Clinical Recommendations

## Immediate Actions (Within 2 weeks)

### 1. Genetic Counseling Referral
- **Urgency**: High priority
- **Purpose**: Risk assessment, family planning, surgical options discussion
- **Provider**: Board-certified genetic counselor or medical geneticist

### 2. Enhanced Screening Protocol
**Breast Cancer Screening**
- Annual breast MRI starting age 25 (or 10 years before earliest family diagnosis)
- Annual mammography starting age 30
- Clinical breast examination every 6 months
- Monthly breast self-examination

**Ovarian Cancer Screening**
- Transvaginal ultrasound and CA-125 every 6 months starting age 30
- Consider risk-reducing surgery by age 35-40 or after childbearing complete

## Medium-term Actions (Within 3 months)

### 3. Multidisciplinary Team Consultation
- High-risk breast clinic referral
- Gynecologic oncology consultation
- Plastic surgery consultation (if considering risk-reducing surgery)

### 4. Family Cascade Testing
- First-degree relatives (parents, siblings, children over 18)
- Genetic counseling for family members
- Coordinate testing through genetics clinic

## Long-term Management

### 5. Lifestyle Modifications
- Maintain healthy weight
- Regular exercise
- Limit alcohol consumption
- Avoid hormone replacement therapy
- Consider chemoprevention options

### 6. Reproductive Planning
- Preimplantation genetic diagnosis (PGD) options
- Fertility preservation before risk-reducing surgery
- Genetic counseling for reproductive decisions

## Follow-up Schedule
- Genetics clinic: 6 months
- High-risk breast clinic: Every 6 months
- Gynecologic oncology: Annually
- Primary care: Continue routine care with awareness of genetic status
    `,
    references: `
# References and Supporting Evidence

## Clinical Guidelines
1. NCCN Guidelines Version 1.2024, Genetic/Familial High-Risk Assessment: Breast, Ovarian, and Pancreatic
2. ACMG Standards and Guidelines for the Interpretation of Sequence Variants
3. ASCO Policy Statement Update: Genetic and Genomic Testing for Cancer Susceptibility

## Key Publications
1. Kuchenbaecker KB, et al. Risks of Breast, Ovarian, and Contralateral Breast Cancer for BRCA1 and BRCA2 Mutation Carriers. JAMA. 2017;317(23):2402-2416.

2. Robson M, et al. Olaparib for Metastatic Breast Cancer in Patients with a Germline BRCA Mutation. N Engl J Med. 2017;377(6):523-533.

3. Bougeard G, et al. Revisiting Li-Fraumeni Syndrome From TP53 Mutation Carriers. J Clin Oncol. 2015;33(21):2345-52.

## Database References
- ClinVar: Variant classifications and clinical significance
- HGMD: Human Gene Mutation Database
- LOVD: Leiden Open Variation Database
- BIC: Breast Cancer Information Core

## Laboratory Information
- **Testing Laboratory**: Biomerkin Genomics Laboratory
- **Test Method**: Next-generation sequencing with confirmatory Sanger sequencing
- **Coverage**: >99% for all analyzed regions
- **Sensitivity**: >99% for single nucleotide variants and small indels
    `
  };

  const highlightSearchTerm = (text) => {
    if (!searchTerm) return text;
    const regex = new RegExp(`(${searchTerm})`, 'gi');
    return text.replace(regex, '<mark class="bg-yellow-200">$1</mark>');
  };

  const downloadReport = (format) => {
    // Implementation would depend on backend API
    console.log(`Downloading report in ${format} format`);
  };

  const printReport = () => {
    window.print();
  };

  const shareReport = () => {
    if (navigator.share) {
      navigator.share({
        title: 'Medical Genomics Report',
        text: 'Comprehensive genomics analysis report',
        url: window.location.href
      });
    }
  };

  return (
    <div className={`bg-white ${isFullscreen ? 'fixed inset-0 z-50' : 'rounded-lg border border-gray-200'}`}>
      {/* Report Header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-200">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Medical Genomics Report</h2>
          <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
            <span>Patient ID: {mockReport.patientInfo.id}</span>
            <span>•</span>
            <span>Date: {mockReport.patientInfo.analysisDate}</span>
            <span>•</span>
            <span>{mockReport.patientInfo.reportType}</span>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search report..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <button
            onClick={() => setShowAnnotations(!showAnnotations)}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            title={showAnnotations ? 'Hide annotations' : 'Show annotations'}
          >
            {showAnnotations ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
          
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          >
            {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </button>
          
          <div className="flex items-center space-x-1 border-l border-gray-300 pl-2">
            <button
              onClick={printReport}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              title="Print report"
            >
              <Printer className="h-4 w-4" />
            </button>
            
            <button
              onClick={shareReport}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              title="Share report"
            >
              <Share2 className="h-4 w-4" />
            </button>
            
            <div className="relative group">
              <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors">
                <Download className="h-4 w-4" />
              </button>
              
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
                <button
                  onClick={() => downloadReport('pdf')}
                  className="w-full text-left px-4 py-2 hover:bg-gray-50 rounded-t-lg"
                >
                  Download PDF
                </button>
                <button
                  onClick={() => downloadReport('docx')}
                  className="w-full text-left px-4 py-2 hover:bg-gray-50"
                >
                  Download Word
                </button>
                <button
                  onClick={() => downloadReport('html')}
                  className="w-full text-left px-4 py-2 hover:bg-gray-50 rounded-b-lg"
                >
                  Download HTML
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex h-full">
        {/* Section Navigation */}
        <div className="w-64 border-r border-gray-200 bg-gray-50">
          <nav className="p-4 space-y-2">
            {reportSections.map((section) => {
              const Icon = section.icon;
              return (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                    activeSection === section.id
                      ? 'bg-blue-100 text-blue-700 font-medium'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span className="text-sm">{section.title}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Report Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-8 max-w-4xl mx-auto">
            <motion.div
              key={activeSection}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="prose prose-lg max-w-none"
            >
              <div 
                className="medical-report-content"
                dangerouslySetInnerHTML={{
                  __html: highlightSearchTerm(mockReport[activeSection] || '')
                }}
              />
            </motion.div>
          </div>
        </div>
      </div>

      {/* Report Footer */}
      <div className="border-t border-gray-200 p-4 bg-gray-50 text-center text-sm text-gray-600">
        <p>
          This report was generated by Biomerkin AI Agent System • 
          For questions, contact your healthcare provider • 
          Report ID: {workflowId}
        </p>
      </div>

      <style jsx>{`
        .medical-report-content {
          font-family: 'Georgia', serif;
          line-height: 1.6;
        }
        
        .medical-report-content h1 {
          color: #1f2937;
          border-bottom: 2px solid #3b82f6;
          padding-bottom: 0.5rem;
          margin-bottom: 1.5rem;
        }
        
        .medical-report-content h2 {
          color: #374151;
          margin-top: 2rem;
          margin-bottom: 1rem;
        }
        
        .medical-report-content h3 {
          color: #4b5563;
          margin-top: 1.5rem;
          margin-bottom: 0.75rem;
        }
        
        .medical-report-content strong {
          color: #1f2937;
        }
        
        .medical-report-content ul {
          margin-left: 1.5rem;
        }
        
        .medical-report-content li {
          margin-bottom: 0.5rem;
        }
        
        @media print {
          .medical-report-content {
            font-size: 12pt;
            line-height: 1.4;
          }
        }
      `}</style>
    </div>
  );
};

export default MedicalReportViewer;