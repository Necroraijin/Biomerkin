import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  FastForward,
  Brain,
  Dna,
  FileText,
  Pill,
  CheckCircle,
  Loader,
  ArrowRight,
  Clock,
  Zap
} from 'lucide-react';
import { demoService } from '../services/api';
import LoadingSpinner from './LoadingSpinner';

const InteractiveDemo = ({ scenarioId, onComplete }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [agentStates, setAgentStates] = useState({});
  const [demoData, setDemoData] = useState(null);
  const [speed, setSpeed] = useState(1);

  const agents = [
    {
      id: 'genomics',
      name: 'GenomicsAgent',
      icon: Dna,
      color: 'from-green-500 to-emerald-500',
      description: 'Analyzing DNA sequence for genes and mutations',
      steps: [
        'Parsing FASTA sequence file',
        'Identifying gene regions',
        'Detecting variants against reference',
        'Translating to protein sequences',
        'Generating genomics report'
      ]
    },
    {
      id: 'proteomics',
      name: 'ProteomicsAgent',
      icon: Brain,
      color: 'from-blue-500 to-cyan-500',
      description: 'Predicting protein structure and function',
      steps: [
        'Querying PDB for structures',
        'Analyzing protein domains',
        'Predicting functional impact',
        'Identifying interactions',
        'Generating structure report'
      ]
    },
    {
      id: 'literature',
      name: 'LiteratureAgent',
      icon: FileText,
      color: 'from-purple-500 to-pink-500',
      description: 'Researching scientific literature',
      steps: [
        'Generating search terms',
        'Querying PubMed database',
        'Filtering relevant articles',
        'Summarizing with Bedrock LLM',
        'Generating literature summary'
      ]
    },
    {
      id: 'drug',
      name: 'DrugAgent',
      icon: Pill,
      color: 'from-orange-500 to-red-500',
      description: 'Identifying drug candidates',
      steps: [
        'Querying DrugBank database',
        'Searching clinical trials',
        'Analyzing drug-target interactions',
        'Scoring effectiveness',
        'Generating drug recommendations'
      ]
    },
    {
      id: 'decision',
      name: 'DecisionAgent',
      icon: CheckCircle,
      color: 'from-indigo-500 to-purple-500',
      description: 'Generating medical report',
      steps: [
        'Aggregating all agent results',
        'Analyzing clinical significance',
        'Generating report with Bedrock',
        'Creating recommendations',
        'Finalizing medical report'
      ]
    }
  ];

  useEffect(() => {
    if (scenarioId) {
      loadDemoScenario();
    }
  }, [scenarioId]);

  useEffect(() => {
    let interval;
    if (isPlaying && currentStep < getTotalSteps()) {
      interval = setInterval(() => {
        setProgress(prev => {
          const newProgress = prev + (2 * speed); // Adjust speed multiplier
          if (newProgress >= 100) {
            advanceStep();
            return 0;
          }
          return newProgress;
        });
      }, 100);
    }
    return () => clearInterval(interval);
  }, [isPlaying, currentStep, speed]);

  const loadDemoScenario = async () => {
    try {
      const response = await demoService.getDemoScenarios();
      const scenario = response.data.scenarios.find(s => s.id === scenarioId);
      setDemoData(scenario);
    } catch (err) {
      console.error('Failed to load demo scenario:', err);
    }
  };

  const getTotalSteps = () => {
    return agents.reduce((total, agent) => total + agent.steps.length, 0);
  };

  const getCurrentAgent = () => {
    let stepCount = 0;
    for (const agent of agents) {
      if (currentStep < stepCount + agent.steps.length) {
        return {
          agent,
          stepIndex: currentStep - stepCount,
          step: agent.steps[currentStep - stepCount]
        };
      }
      stepCount += agent.steps.length;
    }
    return null;
  };

  const advanceStep = () => {
    const current = getCurrentAgent();
    if (current) {
      setAgentStates(prev => ({
        ...prev,
        [current.agent.id]: {
          ...prev[current.agent.id],
          currentStep: current.stepIndex,
          status: current.stepIndex === current.agent.steps.length - 1 ? 'completed' : 'processing'
        }
      }));
    }

    setCurrentStep(prev => {
      const next = prev + 1;
      if (next >= getTotalSteps()) {
        setIsPlaying(false);
        if (onComplete) onComplete();
        return prev;
      }
      return next;
    });
  };

  const playPause = () => {
    setIsPlaying(!isPlaying);
  };

  const reset = () => {
    setIsPlaying(false);
    setCurrentStep(0);
    setProgress(0);
    setAgentStates({});
  };

  const getAgentStatus = (agentId) => {
    const state = agentStates[agentId];
    if (!state) return 'pending';
    return state.status || 'pending';
  };

  const getAgentProgress = (agentId) => {
    const state = agentStates[agentId];
    const agent = agents.find(a => a.id === agentId);
    if (!state || !agent) return 0;
    return ((state.currentStep + 1) / agent.steps.length) * 100;
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      {/* Demo Controls */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-semibold text-gray-900 mb-1">
            Interactive Demo: {demoData?.title || 'Loading...'}
          </h3>
          <p className="text-gray-600 text-sm">
            Watch our autonomous AI agents work together in real-time
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Speed:</span>
            <select 
              value={speed}
              onChange={(e) => setSpeed(Number(e.target.value))}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value={0.5}>0.5x</option>
              <option value={1}>1x</option>
              <option value={2}>2x</option>
              <option value={4}>4x</option>
            </select>
          </div>
          
          <button
            onClick={playPause}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            <span>{isPlaying ? 'Pause' : 'Play'}</span>
          </button>
          
          <button
            onClick={reset}
            className="border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors flex items-center space-x-2"
          >
            <RotateCcw className="h-4 w-4" />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* Overall Progress */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">Overall Progress</span>
          <span className="text-sm text-gray-500">
            Step {currentStep + 1} of {getTotalSteps()}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <motion.div
            className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${((currentStep / getTotalSteps()) * 100) + (progress / getTotalSteps())}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      </div>

      {/* Agent Status Cards */}
      <div className="grid lg:grid-cols-2 xl:grid-cols-3 gap-4 mb-6">
        {agents.map((agent, index) => {
          const Icon = agent.icon;
          const status = getAgentStatus(agent.id);
          const agentProgress = getAgentProgress(agent.id);
          const current = getCurrentAgent();
          const isActive = current?.agent.id === agent.id;
          
          return (
            <motion.div
              key={agent.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`border-2 rounded-lg p-4 transition-all duration-300 ${
                isActive 
                  ? 'border-blue-500 bg-blue-50 shadow-lg' 
                  : status === 'completed'
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-200 bg-white'
              }`}
            >
              <div className="flex items-center space-x-3 mb-3">
                <div className={`w-10 h-10 rounded-lg bg-gradient-to-r ${agent.color} flex items-center justify-center`}>
                  <Icon className="h-5 w-5 text-white" />
                </div>
                
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{agent.name}</h4>
                  <p className="text-xs text-gray-600">{agent.description}</p>
                </div>
                
                <div className="flex items-center">
                  {status === 'completed' && (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  )}
                  {status === 'processing' && (
                    <Loader className="h-5 w-5 text-blue-500 animate-spin" />
                  )}
                  {status === 'pending' && (
                    <div className="h-5 w-5 rounded-full border-2 border-gray-300" />
                  )}
                </div>
              </div>
              
              {/* Agent Progress Bar */}
              <div className="mb-2">
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <motion.div
                    className={`h-1.5 rounded-full ${
                      status === 'completed' ? 'bg-green-500' : 'bg-blue-500'
                    }`}
                    initial={{ width: 0 }}
                    animate={{ width: `${agentProgress}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              </div>
              
              {/* Current Step */}
              {isActive && current && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="text-xs text-blue-700 bg-blue-100 rounded px-2 py-1"
                >
                  <div className="flex items-center space-x-1">
                    <Zap className="h-3 w-3" />
                    <span>{current.step}</span>
                  </div>
                </motion.div>
              )}
              
              {status === 'completed' && (
                <div className="text-xs text-green-700 bg-green-100 rounded px-2 py-1">
                  ✓ Analysis Complete
                </div>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Current Activity Display */}
      <AnimatePresence>
        {isPlaying && getCurrentAgent() && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 mb-6"
          >
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                <Brain className="h-4 w-4 text-white" />
              </div>
              
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-1">
                  <span className="font-medium text-gray-900">
                    {getCurrentAgent()?.agent.name}
                  </span>
                  <ArrowRight className="h-4 w-4 text-gray-400" />
                  <span className="text-blue-600 font-medium">
                    {getCurrentAgent()?.step}
                  </span>
                </div>
                
                <div className="w-full bg-white rounded-full h-2">
                  <motion.div
                    className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.1 }}
                  />
                </div>
              </div>
              
              <div className="flex items-center space-x-1 text-sm text-gray-600">
                <Clock className="h-4 w-4" />
                <span>{Math.ceil((getTotalSteps() - currentStep) / speed)}s</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Demo Completion */}
      {currentStep >= getTotalSteps() && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center py-8"
        >
          <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="h-8 w-8 text-white" />
          </div>
          
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Demo Complete!
          </h3>
          
          <p className="text-gray-600 mb-6">
            All AI agents have completed their autonomous analysis. 
            The medical report is ready for review.
          </p>
          
          <div className="flex justify-center space-x-4">
            <button
              onClick={reset}
              className="border border-gray-300 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Run Again
            </button>
            
            <button className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors">
              View Results
            </button>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default InteractiveDemo;