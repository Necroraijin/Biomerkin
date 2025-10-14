import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Brain, 
  Dna, 
  Zap, 
  Shield, 
  Globe, 
  Award,
  ArrowRight,
  Play,
  CheckCircle,
  Cpu,
  Database,
  Cloud
} from 'lucide-react';

const HomePage = () => {
  const features = [
    {
      icon: Brain,
      title: 'Autonomous AI Reasoning',
      description: 'Advanced LLM-powered decision making with Claude 3 Sonnet on AWS Bedrock',
      color: 'from-blue-500 to-cyan-500'
    },
    {
      icon: Dna,
      title: 'Genomics Analysis',
      description: 'Comprehensive DNA sequence analysis with gene identification and variant interpretation',
      color: 'from-green-500 to-emerald-500'
    },
    {
      icon: Zap,
      title: 'Multi-Agent Coordination',
      description: 'Autonomous coordination between specialized AI agents for complex analysis',
      color: 'from-purple-500 to-pink-500'
    },
    {
      icon: Shield,
      title: 'Clinical Grade',
      description: 'Medical-grade reports with ACMG guidelines and clinical decision support',
      color: 'from-red-500 to-orange-500'
    }
  ];

  const awsServices = [
    { name: 'Amazon Bedrock Agents', description: 'Autonomous AI reasoning and coordination' },
    { name: 'AWS Lambda', description: 'Serverless agent execution' },
    { name: 'API Gateway', description: 'RESTful API endpoints' },
    { name: 'DynamoDB', description: 'Workflow state management' },
    { name: 'S3 + CloudFront', description: 'File storage and web hosting' },
    { name: 'CloudWatch', description: 'Monitoring and logging' }
  ];

  const capabilities = [
    'Autonomous decision-making without human intervention',
    'Reasoning explanations for all clinical recommendations',
    'Integration with 5+ external scientific databases',
    'Real-time multi-agent workflow coordination',
    'Cost-optimized architecture under $35/month',
    'Scalable serverless infrastructure'
  ];

  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="text-center py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="mb-6">
            <span className="bg-gradient-to-r from-orange-500 to-red-500 text-white px-4 py-2 rounded-full text-sm font-semibold">
              🏆 AWS Hackathon 2024 Submission
            </span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold mb-6">
            <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
              Biomerkin
            </span>
          </h1>
          
          <h2 className="text-2xl md:text-3xl text-gray-700 mb-8 font-light">
            Autonomous AI Agent System for Genomics Analysis
          </h2>
          
          <p className="text-xl text-gray-600 mb-12 max-w-3xl mx-auto leading-relaxed">
            Revolutionary multi-agent AI system that autonomously analyzes DNA sequences, 
            researches scientific literature, identifies drug candidates, and generates 
            clinical-grade medical reports using AWS Bedrock Agents.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/analysis"
              className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:shadow-lg transform hover:scale-105 transition-all duration-200 flex items-center justify-center space-x-2"
            >
              <Brain className="h-5 w-5" />
              <span>Start Analysis</span>
              <ArrowRight className="h-5 w-5" />
            </Link>
            
            <Link
              to="/demo"
              className="border-2 border-gray-300 text-gray-700 px-8 py-4 rounded-lg font-semibold text-lg hover:border-blue-500 hover:text-blue-600 transition-all duration-200 flex items-center justify-center space-x-2"
            >
              <Play className="h-5 w-5" />
              <span>View Demo</span>
            </Link>
          </div>
        </motion.div>
      </section>

      {/* AWS Requirements Compliance */}
      <section className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            ✅ AWS Hackathon Requirements Met
          </h2>
          <p className="text-lg text-gray-600">
            Fully compliant with all AWS AI Agent requirements
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 gap-8">
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Core Requirements</h3>
            {[
              'LLM hosted on AWS Bedrock (Claude 3 Sonnet)',
              'Uses Amazon Bedrock Agents with reasoning',
              'Demonstrates autonomous capabilities',
              'Integrates external APIs and databases',
              'Uses multiple AWS services'
            ].map((requirement, index) => (
              <div key={index} className="flex items-center space-x-3">
                <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
                <span className="text-gray-700">{requirement}</span>
              </div>
            ))}
          </div>
          
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">AWS Services Used</h3>
            {awsServices.map((service, index) => (
              <div key={index} className="flex items-start space-x-3">
                <Cloud className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="font-medium text-gray-900">{service.name}</div>
                  <div className="text-sm text-gray-600">{service.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Key Features */}
      <section>
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Autonomous AI Capabilities
          </h2>
          <p className="text-lg text-gray-600">
            Advanced AI agents that work together autonomously
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100"
              >
                <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${feature.color} flex items-center justify-center mb-4`}>
                  <Icon className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* Autonomous Capabilities */}
      <section className="bg-white rounded-2xl p-8 shadow-lg">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-6">
              🤖 Autonomous AI Agent System
            </h2>
            <p className="text-lg text-gray-600 mb-8">
              Our AI agents work together without human intervention, making intelligent 
              decisions about genomics analysis, literature research, and clinical recommendations.
            </p>
            
            <div className="space-y-4">
              {capabilities.map((capability, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <Cpu className="h-5 w-5 text-blue-500 flex-shrink-0" />
                  <span className="text-gray-700">{capability}</span>
                </div>
              ))}
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl p-8">
            <h3 className="text-xl font-semibold text-gray-900 mb-6">
              Multi-Agent Workflow
            </h3>
            
            <div className="space-y-4">
              {[
                { name: 'GenomicsAgent', task: 'DNA sequence analysis & gene identification' },
                { name: 'ProteomicsAgent', task: 'Protein structure & function prediction' },
                { name: 'LiteratureAgent', task: 'Scientific literature research & summarization' },
                { name: 'DrugAgent', task: 'Drug candidate identification & clinical trials' },
                { name: 'DecisionAgent', task: 'Medical report generation & recommendations' }
              ].map((agent, index) => (
                <div key={index} className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
                    {index + 1}
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{agent.name}</div>
                    <div className="text-sm text-gray-600">{agent.task}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Call to Action */}
      <section className="text-center bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-12 text-white">
        <h2 className="text-3xl font-bold mb-4">
          Experience Autonomous AI in Action
        </h2>
        <p className="text-xl mb-8 opacity-90">
          Upload your DNA sequence and watch our AI agents work together autonomously
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/analysis"
            className="bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold text-lg hover:shadow-lg transform hover:scale-105 transition-all duration-200 flex items-center justify-center space-x-2"
          >
            <Dna className="h-5 w-5" />
            <span>Start Analysis</span>
          </Link>
          
          <Link
            to="/demo"
            className="border-2 border-white text-white px-8 py-4 rounded-lg font-semibold text-lg hover:bg-white hover:text-blue-600 transition-all duration-200 flex items-center justify-center space-x-2"
          >
            <Award className="h-5 w-5" />
            <span>View Demo</span>
          </Link>
        </div>
      </section>
    </div>
  );
};

export default HomePage;