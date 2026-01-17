'use client';

import { useState } from 'react';

export default function Dashboard() {
  const [status, setStatus] = useState<'IDLE' | 'RUNNING' | 'COMPLETED' | 'FAILED'>('IDLE');
  const [logs, setLogs] = useState<string[]>([]);

  const handleRunTests = async () => {
    setStatus('RUNNING');
    setLogs(prev => [...prev, 'Starting tests...']);
    // TODO: Call backend API
    setTimeout(() => {
        setStatus('COMPLETED');
        setLogs(prev => [...prev, 'Tests completed successfully.']);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <header className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900">QA Automation Dashboard</h1>
            <div className="flex items-center space-x-4">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    status === 'IDLE' ? 'bg-gray-100 text-gray-800' :
                    status === 'RUNNING' ? 'bg-blue-100 text-blue-800' :
                    status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                    'bg-red-100 text-red-800'
                }`}>
                    Status: {status}
                </span>
            </div>
        </header>

        <main className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Control Panel */}
            <div className="lg:col-span-1 space-y-6">
                <div className="bg-white p-6 rounded-lg shadow sm:p-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Actions</h2>
                    <button
                        onClick={handleRunTests}
                        disabled={status === 'RUNNING'}
                        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {status === 'RUNNING' ? 'Running...' : 'Run Automated Tests'}
                    </button>
                </div>

                 <div className="bg-white p-6 rounded-lg shadow sm:p-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Execution Logs</h2>
                    <div className="h-64 overflow-y-auto bg-gray-900 text-gray-100 p-4 rounded text-sm font-mono">
                        {logs.length === 0 ? (
                            <span className="text-gray-500">No logs available...</span>
                        ) : (
                            logs.map((log, i) => <div key={i}>{log}</div>)
                        )}
                    </div>
                </div>
            </div>

            {/* Bug List */}
            <div className="lg:col-span-2">
                <div className="bg-white rounded-lg shadow overflow-hidden">
                    <div className="px-6 py-5 border-b border-gray-200">
                        <h2 className="text-xl font-semibold text-gray-900">Recent Bugs</h2>
                    </div>
                    <div className="divide-y divide-gray-200">
                        {/* Placeholder for bugs */}
                         <div className="p-6 text-center text-gray-500">
                            No bugs detected yet. Run tests to start analysis.
                        </div>
                    </div>
                </div>
            </div>
        </main>
      </div>
    </div>
  );
}