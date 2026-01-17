'use client';

import { useState, useEffect } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Dashboard() {
  const [status, setStatus] = useState<'IDLE' | 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'ERROR'>('IDLE');
  const [logs, setLogs] = useState<string[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [bugs, setBugs] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [selectedBug, setSelectedBug] = useState<any | null>(null);

  const fetchHistory = () => {
      fetch(`${API_URL}/bugs`)
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
        const res = await fetch(`${API_URL}/run-tests`, { method: 'POST' });
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

    // Safety: Max polls to prevent infinite frontend loops if backend hangs
    let polls = 0;
    const MAX_POLLS = 600; // ~10 minutes

    const interval = setInterval(async () => {
        polls++;
        if (polls > MAX_POLLS) {
             setStatus('ERROR');
             setLogs(prev => [...prev, 'Frontend execution timeout (max polls reached).']);
             clearInterval(interval);
             return;
        }

        try {
            const res = await fetch(`${API_URL}/jobs/${jobId}`);
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
                                <div key={index} className="p-6 hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedBug(bug)}>
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
                                <div key={index} className="p-6 hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedBug(bug)}>
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

        {/* Bug Details Modal */}
        {selectedBug && (
            <div className="fixed inset-0 z-10 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
                <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true" onClick={() => setSelectedBug(null)}></div>
                    <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
                    <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
                        <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                            <div className="sm:flex sm:items-start">
                                <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                                    <h3 className="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                                        Bug Details
                                    </h3>
                                    <div className="mt-4 space-y-4 text-sm text-gray-700">
                                        <p><strong>Test Name:</strong> {selectedBug.test_name}</p>
                                        <p><strong>Summary:</strong> {selectedBug.summary}</p>
                                        <p><strong>Environment:</strong> {selectedBug.environment || "N/A"}</p>
                                        <div>
                                            <strong>Steps:</strong>
                                            <p className="whitespace-pre-wrap mt-1 bg-gray-50 p-2 rounded">{selectedBug.steps}</p>
                                        </div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <strong>Actual Result:</strong>
                                                <p className="whitespace-pre-wrap mt-1 bg-red-50 p-2 rounded text-red-900">{selectedBug.actual_result}</p>
                                            </div>
                                            <div>
                                                <strong>Expected Result:</strong>
                                                <p className="whitespace-pre-wrap mt-1 bg-green-50 p-2 rounded text-green-900">{selectedBug.expected_result}</p>
                                            </div>
                                        </div>
                                        <div className="flex justify-between items-center mt-4">
                                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                                Status: {selectedBug.status}
                                            </span>
                                            <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                                                selectedBug.severity === 'Critical' ? 'bg-red-100 text-red-800' :
                                                selectedBug.severity === 'High' ? 'bg-orange-100 text-orange-800' :
                                                'bg-yellow-100 text-yellow-800'
                                            }`}>
                                                Severity: {selectedBug.severity}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                            <button
                                type="button"
                                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm"
                                onClick={() => setSelectedBug(null)}
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        )}
      </div>
    </div>
  );
}
