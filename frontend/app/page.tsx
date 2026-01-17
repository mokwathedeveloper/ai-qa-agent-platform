'use client';

import { useState, useEffect } from 'react';

export default function Dashboard() {
  const [status, setStatus] = useState<'IDLE' | 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'ERROR'>('IDLE');
  const [logs, setLogs] = useState<string[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [bugs, setBugs] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);

  const fetchHistory = () => {
      fetch('http://localhost:8000/bugs')
        .then(res => res.json())
        .then(data => setHistory(data))
        .catch(console.error);
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleRunTests = async () => {
    setStatus('PENDING');
    setLogs(['Starting tests...']);
    setBugs([]);
    setJobId(null);
    
    try {
        const res = await fetch('http://localhost:8000/run-tests', { method: 'POST' });
        if (!res.ok) throw new Error('Failed to start tests');
        const data = await res.json();
        setJobId(data.job_id);
    } catch (e) {
        setStatus('FAILED');
        setLogs(prev => [...prev, 'Failed to connect to backend.']);
        console.error(e);
    }
  };

  useEffect(() => {
    if (!jobId || status === 'COMPLETED' || status === 'FAILED' || status === 'ERROR') return;

    const interval = setInterval(async () => {
        try {
            const res = await fetch(`http://localhost:8000/jobs/${jobId}`);
            if (!res.ok) return;
            const data = await res.json();
            
            if (['COMPLETED', 'FAILED', 'ERROR'].includes(data.status)) {
                setStatus(data.status);
                setLogs(data.logs);
                setBugs(data.bugs || []);
                fetchHistory(); // Refresh history
                clearInterval(interval);
            } else {
                 setStatus(data.status);
            }
        } catch (e) {
            console.error(e);
        }
    }, 1000);

    return () => clearInterval(interval);
  }, [jobId, status]);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <header className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900">QA Automation Dashboard</h1>
            <div className="flex items-center space-x-4">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    status === 'IDLE' ? 'bg-gray-100 text-gray-800' :
                    (status === 'RUNNING' || status === 'PENDING') ? 'bg-blue-100 text-blue-800' :
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
                        disabled={status === 'RUNNING' || status === 'PENDING'}
                        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {(status === 'RUNNING' || status === 'PENDING') ? 'Running...' : 'Run Automated Tests'}
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

            {/* Main Content */}
            <div className="lg:col-span-2 space-y-8">
                {/* Current Run Bugs */}
                <div className="bg-white rounded-lg shadow overflow-hidden">
                    <div className="px-6 py-5 border-b border-gray-200">
                        <h2 className="text-xl font-semibold text-gray-900">Current Run Results</h2>
                    </div>
                    <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                        {bugs.length === 0 ? (
                            <div className="p-6 text-center text-gray-500">
                                {status === 'COMPLETED' ? 'No bugs detected in this run.' : 'Run tests to see results.'}
                            </div>
                        ) : (
                            bugs.map((bug, index) => (
                                <div key={index} className="p-6 hover:bg-gray-50">
                                    <div className="flex justify-between items-start">
                                        <div className="space-y-2">
                                            <h3 className="text-lg font-medium text-gray-900">{bug.summary || 'No Summary'}</h3>
                                            <p className="text-sm text-gray-500">Test: {bug.test_name}</p>
                                        </div>
                                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                                            bug.severity === 'Critical' ? 'bg-red-100 text-red-800' :
                                            bug.severity === 'High' ? 'bg-orange-100 text-orange-800' :
                                            'bg-yellow-100 text-yellow-800'
                                        }`}>
                                            {bug.severity || 'Normal'}
                                        </span>
                                    </div>
                                    <p className="mt-2 text-sm text-gray-600"><strong>Status:</strong> {bug.status}</p>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Bug History */}
                <div className="bg-white rounded-lg shadow overflow-hidden">
                    <div className="px-6 py-5 border-b border-gray-200">
                        <h2 className="text-xl font-semibold text-gray-900">Bug History</h2>
                    </div>
                    <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                        {history.length === 0 ? (
                            <div className="p-6 text-center text-gray-500">
                                No history available.
                            </div>
                        ) : (
                            history.map((bug, index) => (
                                <div key={index} className="p-6 hover:bg-gray-50">
                                    <div className="flex justify-between items-start">
                                        <div className="space-y-2">
                                            <h3 className="text-lg font-medium text-gray-900">{bug.summary}</h3>
                                            <p className="text-sm text-gray-500">Test: {bug.test_name}</p>
                                            <p className="text-xs text-gray-400">{new Date(bug.created_at).toLocaleString()}</p>
                                        </div>
                                        <div className="flex flex-col items-end space-y-2">
                                            <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                                                bug.severity === 'Critical' ? 'bg-red-100 text-red-800' :
                                                bug.severity === 'High' ? 'bg-orange-100 text-orange-800' :
                                                'bg-yellow-100 text-yellow-800'
                                            }`}>
                                                {bug.severity}
                                            </span>
                                            <span className="text-xs text-gray-500 border border-gray-200 px-2 py-1 rounded">
                                                {bug.status}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </main>
      </div>
    </div>
  );
}
