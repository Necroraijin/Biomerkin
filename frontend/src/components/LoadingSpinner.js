import React from 'react';
import { motion } from 'framer-motion';
import { Loader, Dna } from 'lucide-react';

const LoadingSpinner = ({ 
  size = 'medium', 
  type = 'default', 
  message = 'Loading...', 
  className = '' 
}) => {
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-8 h-8',
    large: 'w-12 h-12',
    xlarge: 'w-16 h-16'
  };

  const messageClasses = {
    small: 'text-sm',
    medium: 'text-base',
    large: 'text-lg',
    xlarge: 'text-xl'
  };

  if (type === 'genomics') {
    return (
      <div className={`flex flex-col items-center justify-center ${className}`}>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className={`${sizeClasses[size]} text-blue-600 mb-2`}
        >
          <Dna className="w-full h-full" />
        </motion.div>
        {message && (
          <p className={`text-gray-600 ${messageClasses[size]} text-center`}>
            {message}
          </p>
        )}
      </div>
    );
  }

  if (type === 'pulse') {
    return (
      <div className={`flex flex-col items-center justify-center ${className}`}>
        <motion.div
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
          className={`${sizeClasses[size]} bg-blue-600 rounded-full mb-2`}
        />
        {message && (
          <p className={`text-gray-600 ${messageClasses[size]} text-center`}>
            {message}
          </p>
        )}
      </div>
    );
  }

  if (type === 'dots') {
    return (
      <div className={`flex flex-col items-center justify-center ${className}`}>
        <div className="flex space-x-1 mb-2">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              animate={{ y: [0, -10, 0] }}
              transition={{
                duration: 0.6,
                repeat: Infinity,
                delay: i * 0.2,
                ease: "easeInOut"
              }}
              className={`w-2 h-2 bg-blue-600 rounded-full ${size === 'large' ? 'w-3 h-3' : ''}`}
            />
          ))}
        </div>
        {message && (
          <p className={`text-gray-600 ${messageClasses[size]} text-center`}>
            {message}
          </p>
        )}
      </div>
    );
  }

  // Default spinner
  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        className={`${sizeClasses[size]} text-blue-600 mb-2`}
      >
        <Loader className="w-full h-full" />
      </motion.div>
      {message && (
        <p className={`text-gray-600 ${messageClasses[size]} text-center`}>
          {message}
        </p>
      )}
    </div>
  );
};

// Full page loading component
export const PageLoader = ({ message = 'Loading Biomerkin...' }) => {
  return (
    <div className="fixed inset-0 bg-white z-50 flex items-center justify-center">
      <div className="text-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="w-16 h-16 text-blue-600 mx-auto mb-4"
        >
          <Dna className="w-full h-full" />
        </motion.div>
        
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Biomerkin
        </h2>
        
        <p className="text-gray-600 mb-4">
          {message}
        </p>
        
        <div className="flex justify-center space-x-1">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                delay: i * 0.2,
                ease: "easeInOut"
              }}
              className="w-2 h-2 bg-blue-600 rounded-full"
            />
          ))}
        </div>
      </div>
    </div>
  );
};

// Inline loading component
export const InlineLoader = ({ message = 'Loading...', className = '' }) => {
  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        className="w-4 h-4 text-blue-600"
      >
        <Loader className="w-full h-full" />
      </motion.div>
      <span className="text-gray-600 text-sm">{message}</span>
    </div>
  );
};

// Button loading state
export const ButtonLoader = ({ size = 'small' }) => {
  const sizeClass = size === 'small' ? 'w-4 h-4' : 'w-5 h-5';
  
  return (
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
      className={`${sizeClass} text-current`}
    >
      <Loader className="w-full h-full" />
    </motion.div>
  );
};

export default LoadingSpinner;