import React, { useState } from 'react';
import { motion } from 'framer-motion';
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
  ScatterChart,
  Scatter,
  LineChart,
  Line
} from 'recharts';
import { 
  Dna, 
  AlertTriangle, 
  CheckCircle, 
  Info,
  Filter,
  Eye,
  Download
} from 'lucide-react';

const GenomicsVisualization = ({ data, type = 'variants' }) => {
  const [selectedVariant, setSelectedVariant] = useState(null);
  const [filterLevel, setFilterLevel] = useState('all');

  // Color schemes for different visualization types
  const colors = {
    pathogenic: '#ef4444',
    likelyPathogenic: '#f97316',
    vus: '#eab308',
    likelyBenign: '#84cc16',
    benign: '#22c55e'
  };

  const riskColors = {
    high: '#dc2626',
    moderate: '#f59e0b',
    low: '#10b981'
  };

  // Mock data for demonstration
  const variantData = [
    { name: 'Pathogenic', value: 2, color: colors.pathogenic },
    { name: 'Likely Pathogenic', value: 1, color: colors.likelyPathogenic },
    { name: 'VUS', value: 3, color: colors.vus },
    { name: 'Likely Benign', value: 8, color: colors.likelyBenign },
    { name: 'Benign', value: 15, color: colors.benign }
  ];

  const geneExpressionData = [
    { gene: 'BRCA1', expression: 85, baseline: 100, significance: 'high' },
    { gene: 'TP53', expression: 45, baseline: 100, significance: 'high' },
    { gene: 'EGFR', expression: 120, baseline: 100, significance: 'moderate' },
    { gene: 'KRAS', expression: 95, baseline: 100, significance: 'low' },
    { gene: 'PIK3CA', expression: 110, baseline: 100, significance: 'moderate' }
  ];

  const chromosomeData = [
    { chromosome: 'chr1', variants: 5, pathogenic: 1 },
    { chromosome: 'chr2', variants: 3, pathogenic: 0 },
    { chromosome: 'chr17', variants: 8, pathogenic: 3 },
    { chromosome: 'chrX', variants: 2, pathogenic: 0 },
    { chromosome: 'chrY', variants: 1, pathogenic: 0 }
  ];

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const VariantPieChart = () => (
    <div className="bg-white rounded-lg p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Variant Classification</h3>
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-gray-400" />
          <select 
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value)}
            className="text-sm border border-gray-300 rounded px-2 py-1"
          >
            <option value="all">All Variants</option>
            <option value="significant">Significant Only</option>
            <option value="pathogenic">Pathogenic Only</option>
          </select>
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={variantData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={5}
            dataKey="value"
            onMouseEnter={(data) => setSelectedVariant(data)}
            onMouseLeave={() => setSelectedVariant(null)}
          >
            {variantData.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.color}
                stroke={selectedVariant?.name === entry.name ? '#1f2937' : 'none'}
                strokeWidth={selectedVariant?.name === entry.name ? 2 : 0}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>
      
      <div className="grid grid-cols-2 gap-2 mt-4">
        {variantData.map((item, index) => (
          <div 
            key={index} 
            className={`flex items-center space-x-2 p-2 rounded cursor-pointer transition-colors ${
              selectedVariant?.name === item.name ? 'bg-gray-100' : 'hover:bg-gray-50'
            }`}
            onMouseEnter={() => setSelectedVariant(item)}
            onMouseLeave={() => setSelectedVariant(null)}
          >
            <div 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: item.color }}
            />
            <span className="text-sm text-gray-700">{item.name}</span>
            <span className="text-sm font-medium text-gray-900">({item.value})</span>
          </div>
        ))}
      </div>
    </div>
  );

  const GeneExpressionChart = () => (
    <div className="bg-white rounded-lg p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Gene Expression Levels</h3>
        <button className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-700">
          <Eye className="h-4 w-4" />
          <span>View Details</span>
        </button>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={geneExpressionData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis dataKey="gene" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="baseline" fill="#e5e7eb" name="Baseline" />
          <Bar dataKey="expression" fill="#3b82f6" name="Expression" />
        </BarChart>
      </ResponsiveContainer>
      
      <div className="mt-4 grid grid-cols-3 gap-4 text-center">
        <div className="p-3 bg-red-50 rounded-lg">
          <div className="text-2xl font-bold text-red-600">2</div>
          <div className="text-sm text-red-700">Downregulated</div>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-gray-600">1</div>
          <div className="text-sm text-gray-700">Normal</div>
        </div>
        <div className="p-3 bg-green-50 rounded-lg">
          <div className="text-2xl font-bold text-green-600">2</div>
          <div className="text-sm text-green-700">Upregulated</div>
        </div>
      </div>
    </div>
  );

  const ChromosomeDistribution = () => (
    <div className="bg-white rounded-lg p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Chromosome Distribution</h3>
        <button className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-700">
          <Download className="h-4 w-4" />
          <span>Export</span>
        </button>
      </div>
      
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={chromosomeData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis dataKey="chromosome" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="variants" fill="#6366f1" name="Total Variants" />
          <Bar dataKey="pathogenic" fill="#ef4444" name="Pathogenic" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );

  const VariantTable = () => (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Significant Variants</h3>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Gene
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Variant
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Significance
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Impact
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {[
              { gene: 'BRCA1', variant: 'c.5266dupC', type: 'Frameshift', significance: 'Pathogenic', impact: 'High' },
              { gene: 'TP53', variant: 'c.524G>A', type: 'Missense', significance: 'Likely Pathogenic', impact: 'High' },
              { gene: 'BRCA1', variant: 'c.181T>G', type: 'Missense', significance: 'VUS', impact: 'Uncertain' }
            ].map((variant, index) => (
              <motion.tr 
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="hover:bg-gray-50 cursor-pointer"
                onClick={() => setSelectedVariant(variant)}
              >
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {variant.gene}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                  {variant.variant}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {variant.type}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    variant.significance === 'Pathogenic' ? 'bg-red-100 text-red-800' :
                    variant.significance === 'Likely Pathogenic' ? 'bg-orange-100 text-orange-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {variant.significance}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    {variant.impact === 'High' && <AlertTriangle className="h-4 w-4 text-red-500 mr-1" />}
                    {variant.impact === 'Uncertain' && <Info className="h-4 w-4 text-yellow-500 mr-1" />}
                    <span className="text-sm text-gray-500">{variant.impact}</span>
                  </div>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  // Render different visualization types
  switch (type) {
    case 'variants':
      return <VariantPieChart />;
    case 'expression':
      return <GeneExpressionChart />;
    case 'chromosomes':
      return <ChromosomeDistribution />;
    case 'table':
      return <VariantTable />;
    default:
      return (
        <div className="grid lg:grid-cols-2 gap-6">
          <VariantPieChart />
          <GeneExpressionChart />
          <div className="lg:col-span-2">
            <ChromosomeDistribution />
          </div>
          <div className="lg:col-span-2">
            <VariantTable />
          </div>
        </div>
      );
  }
};

export default GenomicsVisualization;