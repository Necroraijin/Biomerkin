import React from 'react';
import { motion } from 'framer-motion';
import CostDashboard from '../components/CostDashboard';

const CostPage = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="max-w-7xl mx-auto"
    >
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Cost Optimization Dashboard
        </h1>
        <p className="text-gray-600">
          Monitor AWS costs, track spending trends, and discover optimization opportunities for your Biomerkin deployment.
        </p>
      </div>

      <CostDashboard />
    </motion.div>
  );
};

export default CostPage;

