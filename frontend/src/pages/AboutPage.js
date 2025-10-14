import React from 'react';
import { motion } from 'framer-motion';
import { 
  Award, 
  Brain, 
  Dna, 
  Zap, 
  Shield, 
  Globe, 
  Users,
  Target,
  Lightbulb,
  Code,
  Database,
  Cloud,
  ExternalLink,
  Github,
  Mail,
  Linkedin
} from 'lucide-react';

const AboutPage = () => {
  const teamMembers = [
    {
      name: 'AI Agent System',
      role: 'Autonomous Multi-Agent Coordinator',
      description: 'Orchestrates 5 specialized AI agents for comprehensive genomics analysis',
      avatar: '🤖'
    },
    {
      name: 'AWS Bedrock',
      role: 'LLM Reasoning Engine',
      description: 'Powers autonomous decision-making with Claude 3 Sonnet',
      avatar: '🧠'
    },
    {
      name: 'Bioinformatics APIs',
      role: 'External Data Integration',
      description: 'Real-time integration with PubMed, DrugBank, PDB, and clinical databases',
      avatar: '🔬'
    }
  ];

  const technologies = [
    {
      category: 'AI & Machine Learning',
      items: [
        { name: 'Amazon Bedrock Agents', description: 'Autonomous AI agent orchestration' },
        { name: 'Claude 3 Sonnet', description: 'Advanced LLM for reasoning and text generation' },
        { name: 'Multi-Agent Systems', description: 'Coordinated autonomous agent workflows' },
        { name: 'Natural Language Processing', description: 'Literature analysis and report generation' }
      ]
    },
    {
      category: 'AWS Services',
      items: [
        { name: 'AWS Lambda', description: 'Serverless agent execution' },
        { name: 'API Gateway', description: 'RESTful API endpoints' },
        { name: 'DynamoDB', description: 'Workflow state management' },
        { name: 'S3 + CloudFront', description: 'File storage and web hosting' },
        { name: 'CloudWatch', description: 'Monitoring and logging' },
        { name: 'IAM', description: 'Security and access control' }
      ]
    },
    {
      category: 'Bioinformatics',
      items: [
        { name: 'Biopython', description: 'DNA sequence analysis and processing' },
        { name: 'PubMed E-utilities', description: 'Scientific literature search' },
        { name: 'PDB API', description: 'Protein structure data' },
        { name: 'DrugBank', description: 'Drug candidate identification' },
        { name: 'ClinicalTrials.gov', description: 'Clinical trial information' }
      ]
    },
    {
      category: 'Frontend & UI',
      items: [
        { name: 'React 18', description: 'Modern web application framework' },
        { name: 'Tailwind CSS', description: 'Utility-first CSS framework' },
        { name: 'Framer Motion', description: 'Animation and interaction library' },
        { name: 'Recharts', description: 'Data visualization components' },
        { name: 'Socket.IO', description: 'Real-time progress tracking' }
      ]
    }
  ];

  const achievements = [
    {
      icon: Award,
      title: 'AWS Hackathon Compliance',
      description: 'Fully meets all AWS AI Agent hackathon requirements',
      details: [
        'LLM hosted on AWS Bedrock',
        'Demonstrates autonomous capabilities',
        'Uses multiple AWS services',
        'Integrates external APIs'
      ]
    },
    {
      icon: Brain,
      title: 'Autonomous AI Innovation',
      description: 'Novel multi-agent system with zero human intervention',
      details: [
        'Autonomous decision-making',
        'Intelligent error handling',
        'Adaptive workflows',
        'Reasoning explanations'
      ]
    },
    {
      icon: Shield,
      title: 'Clinical Grade Quality',
      description: 'Medical-grade analysis and reporting standards',
      details: [
        'ACMG variant interpretation',
        'Clinical decision support',
        'Professional medical reports',
        'Evidence-based recommendations'
      ]
    },
    {
      icon: Zap,
      title: 'Performance Optimized',
      description: 'Cost-effective and scalable architecture',
      details: [
        'Serverless architecture',
        'Under $35/month operating cost',
        'Auto-scaling capabilities',
        'Optimized resource usage'
      ]
    }
  ];

  const useCases = [
    {
      title: 'Personalized Medicine',
      description: 'Analyze patient genomic data to provide personalized treatment recommendations',
      icon: Target,
      applications: [
        'Cancer susceptibility assessment',
        'Pharmacogenomics analysis',
        'Rare disease diagnosis',
        'Treatment response prediction'
      ]
    },
    {
      title: 'Clinical Decision Support',
      description: 'Assist healthcare providers with evidence-based clinical decisions',
      icon: Lightbulb,
      applications: [
        'Variant interpretation',
        'Drug selection guidance',
        'Risk stratification',
        'Monitoring recommendations'
      ]
    },
    {
      title: 'Research & Discovery',
      description: 'Accelerate biomedical research and drug discovery processes',
      icon: Globe,
      applications: [
        'Literature mining',
        'Biomarker discovery',
        'Drug repurposing',
        'Clinical trial matching'
      ]
    }
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-16">
      {/* Header */}
      <section className="text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <span className="bg-gradient-to-r from-orange-500 to-red-500 text-white px-4 py-2 rounded-full text-sm font-semibold">
            🏆 AWS Hackathon 2024 Submission
          </span>
        </motion.div>
        
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
          About <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Biomerkin</span>
        </h1>
        
        <p className="text-xl text-gray-600 max-w-4xl mx-auto leading-relaxed">
          Biomerkin is a revolutionary autonomous AI agent system that transforms genomics analysis 
          through intelligent multi-agent coordination, powered by AWS Bedrock and advanced LLM reasoning.
        </p>
      </section>

      {/* Mission Statement */}
      <section className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-8">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Our Mission</h2>
        </div>
        
        <div className="grid lg:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <Brain className="h-8 w-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Autonomous Intelligence</h3>
            <p className="text-gray-600">
              Develop AI systems that can reason, decide, and act autonomously in complex genomics workflows
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <Dna className="h-8 w-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Precision Medicine</h3>
            <p className="text-gray-600">
              Enable personalized healthcare through comprehensive genomic analysis and clinical decision support
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <Globe className="h-8 w-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Global Impact</h3>
            <p className="text-gray-600">
              Democratize access to advanced genomics analysis and accelerate biomedical research worldwide
            </p>
          </div>
        </div>
      </section>

      {/* Key Achievements */}
      <section>
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Key Achievements</h2>
          <p className="text-lg text-gray-600">
            Technical innovations and compliance with AWS hackathon requirements
          </p>
        </div>
        
        <div className="grid lg:grid-cols-2 gap-8">
          {achievements.map((achievement, index) => {
            const Icon = achievement.icon;
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white rounded-xl shadow-lg p-6 border border-gray-200"
              >
                <div className="flex items-center space-x-4 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900">{achievement.title}</h3>
                    <p className="text-gray-600">{achievement.description}</p>
                  </div>
                </div>
                
                <ul className="space-y-2">
                  {achievement.details.map((detail, idx) => (
                    <li key={idx} className="flex items-center space-x-2 text-sm text-gray-600">
                      <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                      <span>{detail}</span>
                    </li>
                  ))}
                </ul>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* Technology Stack */}
      <section className="bg-white rounded-2xl shadow-lg p-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Technology Stack</h2>
          <p className="text-lg text-gray-600">
            Cutting-edge technologies powering our autonomous AI system
          </p>
        </div>
        
        <div className="grid lg:grid-cols-2 gap-8">
          {technologies.map((category, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-6"
            >
              <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center space-x-2">
                <Code className="h-5 w-5 text-blue-500" />
                <span>{category.category}</span>
              </h3>
              
              <div className="space-y-3">
                {category.items.map((item, idx) => (
                  <div key={idx} className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                    <div>
                      <div className="font-medium text-gray-900">{item.name}</div>
                      <div className="text-sm text-gray-600">{item.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Use Cases */}
      <section>
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Use Cases & Applications</h2>
          <p className="text-lg text-gray-600">
            Real-world applications of our autonomous AI agent system
          </p>
        </div>
        
        <div className="grid lg:grid-cols-3 gap-8">
          {useCases.map((useCase, index) => {
            const Icon = useCase.icon;
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white rounded-xl shadow-lg p-6 border border-gray-200 hover:shadow-xl transition-all duration-300"
              >
                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center mb-4">
                  <Icon className="h-6 w-6 text-white" />
                </div>
                
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {useCase.title}
                </h3>
                
                <p className="text-gray-600 mb-4">
                  {useCase.description}
                </p>
                
                <div className="space-y-2">
                  {useCase.applications.map((app, idx) => (
                    <div key={idx} className="flex items-center space-x-2 text-sm text-gray-600">
                      <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                      <span>{app}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* Team Section */}
      <section className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">System Components</h2>
          <p className="text-lg text-gray-600">
            The autonomous agents and services that power Biomerkin
          </p>
        </div>
        
        <div className="grid lg:grid-cols-3 gap-8">
          {teamMembers.map((member, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white rounded-xl p-6 text-center shadow-lg"
            >
              <div className="text-4xl mb-4">{member.avatar}</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-1">
                {member.name}
              </h3>
              <p className="text-blue-600 font-medium mb-3">
                {member.role}
              </p>
              <p className="text-gray-600 text-sm">
                {member.description}
              </p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Contact & Links */}
      <section className="text-center bg-white rounded-2xl shadow-lg p-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Get Involved
        </h2>
        <p className="text-lg text-gray-600 mb-8">
          Interested in autonomous AI for genomics? Let's connect and collaborate.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-lg font-semibold hover:shadow-lg transform hover:scale-105 transition-all duration-200 flex items-center justify-center space-x-2">
            <Github className="h-5 w-5" />
            <span>View Source Code</span>
          </button>
          
          <button className="border-2 border-gray-300 text-gray-700 px-6 py-3 rounded-lg font-semibold hover:border-blue-500 hover:text-blue-600 transition-all duration-200 flex items-center justify-center space-x-2">
            <ExternalLink className="h-5 w-5" />
            <span>Technical Documentation</span>
          </button>
          
          <button className="border-2 border-gray-300 text-gray-700 px-6 py-3 rounded-lg font-semibold hover:border-blue-500 hover:text-blue-600 transition-all duration-200 flex items-center justify-center space-x-2">
            <Mail className="h-5 w-5" />
            <span>Contact Team</span>
          </button>
        </div>
      </section>
    </div>
  );
};

export default AboutPage;