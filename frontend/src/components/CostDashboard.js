import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle,
  Lightbulb,
  Target,
  BarChart3,
  PieChart,
  Activity
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts';

const CostDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCostData();
  }, []);

  const fetchCostData = async () => {
    try {
      setLoading(true);
      // Mock data for demonstration
      const mockData = {
        current_costs: {
          total_cost: 45.67,
          currency: 'USD',
          period_days: 7,
          service_breakdown: {
            'Amazon Lambda': 12.34,
            'Amazon DynamoDB': 8.90,
            'Amazon S3': 5.43,
            'Amazon API Gateway': 4.21,
            'Amazon Bedrock': 10.50,
            'Amazon CloudWatch': 2.15,
            'Amazon SNS': 1.20,
            'Amazon SQS': 0.94
          }
        },
        optimization_recommendations: [
          {
            service: 'Amazon Lambda',
            type: 'memory_optimization',
            description: 'Optimize Lambda memory allocation based on actual usage patterns',
            potential_savings: 15.0,
            currency: 'USD',
            confidence: 0.85,
            effort: 'low',
            priority: 'medium'
          },
          {
            service: 'Amazon DynamoDB',
            type: 'billing_mode',
            description: 'Switch to on-demand billing for variable workloads',
            potential_savings: 30.0,
            currency: 'USD',
            confidence: 0.90,
            effort: 'low',
            priority: 'high'
          },
          {
            service: 'Amazon S3',
            type: 'lifecycle_policies',
            description: 'Implement lifecycle policies for data archival',
            potential_savings: 40.0,
            currency: 'USD',
            confidence: 0.95,
            effort: 'low',
            priority: 'high'
          },
          {
            service: 'Amazon Bedrock',
            type: 'model_selection',
            description: 'Use smaller models for simple tasks to reduce costs',
            potential_savings: 20.0,
            currency: 'USD',
            confidence: 0.80,
            effort: 'medium',
            priority: 'medium'
          }
        ],
        cost_trends: {
          trend: 'stable',
          change_percent: 2.5,
          daily_costs: {
            '2024-01-01': 6.2,
            '2024-01-02': 6.8,
            '2024-01-03': 5.9,
            '2024-01-04': 7.1,
            '2024-01-05': 6.5,
            '2024-01-06': 6.3,
            '2024-01-07': 6.7
          },
          average_daily_cost: 6.5,
          total_period_cost: 45.5,
          period_days: 7
        },
        budget_alerts: [
          {
            budget_name: 'Biomerkin Monthly Budget',
            threshold: 75,
            current_spend: 45.67,
            alert_type: 'forecasted',
            severity: 'low',
            timestamp: new Date().toISOString()
          }
        ],
        summary: {
          total_current_cost: 45.67,
          total_potential_savings: 105.0,
          optimization_score: 78,
          recommendations_count: 4,
          alerts_count: 1,
          last_updated: new Date().toISOString()
        }
      };
      
      setDashboardData(mockData);
    } catch (err) {
      setError('Failed to load cost data');
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getEffortColor = (effort) => {
    switch (effort) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="mx-auto h-12 w-12 text-red-500 mb-4" />
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  const { current_costs, optimization_recommendations, cost_trends, budget_alerts, summary } = dashboardData;

  // Prepare chart data
  const serviceChartData = Object.entries(current_costs.service_breakdown).map(([service, cost]) => ({
    service: service.replace('Amazon ', ''),
    cost: cost
  }));

  const trendChartData = Object.entries(cost_trends.daily_costs).map(([date, cost]) => ({
    date: new Date(date).toLocaleDateString(),
    cost: cost
  }));

  const COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#84cc16', '#f97316'];

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white p-6 rounded-lg shadow-md border border-gray-200"
        >
          <div className="flex items-center">
            <DollarSign className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Current Cost</p>
              <p className="text-2xl font-bold text-gray-900">
                ${current_costs.total_cost.toFixed(2)}
              </p>
              <p className="text-xs text-gray-500">Last {current_costs.period_days} days</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white p-6 rounded-lg shadow-md border border-gray-200"
        >
          <div className="flex items-center">
            {cost_trends.trend === 'increasing' ? (
              <TrendingUp className="h-8 w-8 text-red-600" />
            ) : cost_trends.trend === 'decreasing' ? (
              <TrendingDown className="h-8 w-8 text-green-600" />
            ) : (
              <Activity className="h-8 w-8 text-blue-600" />
            )}
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Cost Trend</p>
              <p className="text-2xl font-bold text-gray-900">
                {cost_trends.change_percent > 0 ? '+' : ''}{cost_trends.change_percent.toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500 capitalize">{cost_trends.trend}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white p-6 rounded-lg shadow-md border border-gray-200"
        >
          <div className="flex items-center">
            <Lightbulb className="h-8 w-8 text-yellow-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Potential Savings</p>
              <p className="text-2xl font-bold text-gray-900">
                ${summary.total_potential_savings.toFixed(0)}
              </p>
              <p className="text-xs text-gray-500">{summary.recommendations_count} recommendations</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white p-6 rounded-lg shadow-md border border-gray-200"
        >
          <div className="flex items-center">
            <Target className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Optimization Score</p>
              <p className="text-2xl font-bold text-gray-900">
                {summary.optimization_score}/100
              </p>
              <p className="text-xs text-gray-500">Cost efficiency</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Service Cost Breakdown */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white p-6 rounded-lg shadow-md border border-gray-200"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <BarChart3 className="h-5 w-5 mr-2" />
            Service Cost Breakdown
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={serviceChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="service" angle={-45} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip formatter={(value) => [`$${value.toFixed(2)}`, 'Cost']} />
              <Bar dataKey="cost" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Cost Trend */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white p-6 rounded-lg shadow-md border border-gray-200"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <TrendingUp className="h-5 w-5 mr-2" />
            Daily Cost Trend
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => [`$${value.toFixed(2)}`, 'Cost']} />
              <Line type="monotone" dataKey="cost" stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Optimization Recommendations */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="bg-white p-6 rounded-lg shadow-md border border-gray-200"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Lightbulb className="h-5 w-5 mr-2" />
          Optimization Recommendations
        </h3>
        <div className="space-y-4">
          {optimization_recommendations.map((rec, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{rec.service}</h4>
                  <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
                  <div className="flex items-center space-x-4 mt-2">
                    <span className="text-sm font-medium text-green-600">
                      Potential Savings: ${rec.potential_savings.toFixed(2)}
                    </span>
                    <span className="text-sm text-gray-500">
                      Confidence: {(rec.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
                <div className="flex flex-col space-y-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(rec.priority)}`}>
                    {rec.priority}
                  </span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getEffortColor(rec.effort)}`}>
                    {rec.effort} effort
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Budget Alerts */}
      {budget_alerts.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="bg-white p-6 rounded-lg shadow-md border border-gray-200"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2" />
            Budget Alerts
          </h3>
          <div className="space-y-3">
            {budget_alerts.map((alert, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <h4 className="font-medium text-gray-900">{alert.budget_name}</h4>
                  <p className="text-sm text-gray-600">
                    Current spend: ${alert.current_spend.toFixed(2)} | Threshold: {alert.threshold}%
                  </p>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getSeverityColor(alert.severity)}`}>
                  {alert.severity}
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default CostDashboard;

