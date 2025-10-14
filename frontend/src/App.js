import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { motion } from 'framer-motion';
import Header from './components/Header';
import HomePage from './pages/HomePage';
import AnalysisPage from './pages/AnalysisPage';
import ResultsPage from './pages/ResultsPage';
import DemoPage from './pages/DemoPage';
import AboutPage from './pages/AboutPage';
import CostPage from './pages/CostPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <Header />
        
        <motion.main
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="container mx-auto px-4 py-8"
        >
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/analysis" element={<AnalysisPage />} />
            <Route path="/results/:workflowId" element={<ResultsPage />} />
            <Route path="/demo" element={<DemoPage />} />
            <Route path="/cost" element={<CostPage />} />
            <Route path="/about" element={<AboutPage />} />
          </Routes>
        </motion.main>
        
        <footer className="bg-gray-900 text-white py-8 mt-16">
          <div className="container mx-auto px-4 text-center">
            <div className="mb-4">
              <h3 className="text-xl font-bold mb-2">Biomerkin AI Agent</h3>
              <p className="text-gray-300">
                Autonomous Multi-Agent System for Genomics Analysis
              </p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-8 mb-6">
              <div>
                <h4 className="font-semibold mb-2">AWS Services</h4>
                <ul className="text-sm text-gray-300 space-y-1">
                  <li>Amazon Bedrock Agents</li>
                  <li>AWS Lambda</li>
                  <li>API Gateway</li>
                  <li>DynamoDB</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-semibold mb-2">AI Capabilities</h4>
                <ul className="text-sm text-gray-300 space-y-1">
                  <li>Autonomous Reasoning</li>
                  <li>Clinical Decision Making</li>
                  <li>Multi-Agent Coordination</li>
                  <li>External API Integration</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-semibold mb-2">Applications</h4>
                <ul className="text-sm text-gray-300 space-y-1">
                  <li>Personalized Medicine</li>
                  <li>Genomics Analysis</li>
                  <li>Drug Discovery</li>
                  <li>Clinical Reports</li>
                </ul>
              </div>
            </div>
            
            <div className="border-t border-gray-700 pt-4">
              <p className="text-sm text-gray-400">
                Built for AWS Hackathon 2024 • Demonstrating Autonomous AI Agents
              </p>
            </div>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;