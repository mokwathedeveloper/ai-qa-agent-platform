'use client';

import { useState, useEffect } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { useOffline } from './hooks/useOffline';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface LoadingState {
  type: 'idle' | 'validating' | 'submitting' | 'running' | 'analyzing' | 'completed' | 'error';
  message: string;
  progress?: number;
}

export default function Dashboard() {
  const isOffline = useOffline();
  
  const [status, setStatus] = useState<'IDLE' | 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'ERROR'>('IDLE');
  const [loadingState, setLoadingState] = useState<LoadingState>({ type: 'idle', message: 'Ready to start testing' });
  const [logs, setLogs] = useState<string[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [bugs, setBugs] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [selectedBug, setSelectedBug] = useState<any | null>(null);
  const [provider, setProvider] = useState<'uTest' | 'test.io'>('uTest');
  const [testUrl, setTestUrl] = useState('');
  const [urlError, setUrlError] = useState('');
  const [copySuccess, setCopySuccess] = useState('');
  
  // New State for Context
  const [cycleOverview, setCycleOverview] = useState('');
  const [testingInstructions, setTestingInstructions] = useState('');

  // WebSocket connection
  const { lastMessage, connectionStatus } = useWebSocket(jobId);

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      setStatus(lastMessage.status as any);
      setLogs(lastMessage.logs || []);
      setBugs(lastMessage.bugs || []);
      
      // Update loading state based on status
      switch (lastMessage.status) {
        case 'RUNNING':
          setLoadingState({ type: 'running', message: 'Running automated tests...', progress: 50 });
          break;
        case 'COMPLETED':
          setLoadingState({ type: 'completed', message: 'Tests completed successfully' });
          fetchHistory();
          break;
        case 'FAILED':
          setLoadingState({ type: 'analyzing', message: 'Analyzing failures and generating bug reports...', progress: 75 });
          fetchHistory();
          break;
        case 'ERROR':
          setLoadingState({ type: 'error', message: 'An error occurred during testing' });
          break;
      }
    }
  }, [lastMessage]);

  const validateUrl = (url: string): boolean => {
    const urlPattern = /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/;
    return urlPattern.test(url);
  };

  const fetchHistory = async () => {
    try {
      const response = await fetch(`${API_URL}/bugs`);
      if (response.ok) {
        const data = await response.json();
        setHistory(data);
      }
    } catch (error) {
      console.error('Failed to fetch history:', error);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleRunTests = async () => {
    if (!testUrl) {
      setUrlError('Please provide a URL to test.');
      return;
    }

    if (!validateUrl(testUrl)) {
      setUrlError('Please enter a valid URL (must start with http:// or https://)');
      return;
    }

    setUrlError('');
    setLoadingState({ type: 'validating', message: 'Validating input and preparing tests...', progress: 10 });
    setStatus('PENDING');
    setLogs(['Starting tests...']);
    setBugs([]);
    setJobId(null);
    
    try {
      setLoadingState({ type: 'submitting', message: 'Submitting test request...', progress: 25 });
      
      const res = await fetch(`${API_URL}/run-tests`, { 
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          test_url: testUrl,
          cycle_overview: cycleOverview,
          testing_instructions: testingInstructions,
          provider: provider
        })
      });
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || 'Failed to start tests');
      }
      
      const data = await res.json();
      setJobId(data.id);
      setLoadingState({ type: 'running', message: 'Test request accepted. Initializing...', progress: 30 });
    } catch (e: any) {
      setStatus('ERROR');
      setLoadingState({ type: 'error', message: e.message || 'Failed to connect to backend.' });
      setLogs(prev => [...prev, e.message || 'Failed to connect to backend.']);
      console.error(e);
    }
  };

  const copyToClipboard = async (provider: 'uTest' | 'test.io') => {
    if (!selectedBug) return;
    
    let report = '';
    if (provider === 'uTest') {
      report = `
**Title:** ${selectedBug.summary}

**Environment:** 
- **${selectedBug.environment?.browser || 'Chrome'}**
- **${selectedBug.environment?.os || 'Linux'}**

**Preconditions:**
(Add preconditions here)

**Steps:**
${selectedBug.steps}

**Expected Result:**
${selectedBug.expected_result}

**Actual Result:**
${selectedBug.actual_result}

**Severity:** ${selectedBug.severity}
      `.trim();
    } else if (provider === 'test.io') {
      report = `
# **${selectedBug.summary}**

### Environment
- **Browser:** ${selectedBug.environment?.browser || 'Chrome'}
- **OS:** ${selectedBug.environment?.os || 'Linux'}

### Preconditions
> (Add preconditions here)

### Steps to Reproduce
${selectedBug.steps}

### Expected Result
> ${selectedBug.expected_result}

### Actual Result
> ${selectedBug.actual_result}

### Severity
${selectedBug.severity}
      `.trim();
    }

    try {
      await navigator.clipboard.writeText(report);
      setCopySuccess(`Bug report for ${provider} copied to clipboard!`);
      setTimeout(() => setCopySuccess(''), 3000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  if (isOffline) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">You are currently offline</div>
          <p className="text-gray-600">Please check your internet connection and try again.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      {/* Offline Banner */}
      {isOffline && (
        <div className="fixed top-0 left-0 right-0 bg-red-600 text-white text-center py-2 z-50">
          You are currently offline. Some features may not work properly.
        </div>
      )}
      
      {/* Copy Success Banner */}
      {copySuccess && (
        <div className="fixed top-0 left-0 right-0 bg-green-600 text-white text-center py-2 z-50">
          {copySuccess}
        </div>
      )}
      
      <div className="max-w-7xl mx-auto space-y-8" style={{ marginTop: isOffline || copySuccess ? '3rem' : '0' }}>
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
                {connectionStatus !== 'Closed' && jobId && (
                  <span className={`px-2 py-1 rounded text-xs ${
                    connectionStatus === 'Open' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {connectionStatus === 'Open' ? '🟢 Live' : '🟡 Connecting'}
                  </span>
                )}
            </div>
        </header>

        <main className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Control Panel */}
            <div className="lg:col-span-1 space-y-6">
                
                {/* Context Input */}
                <div className="bg-white p-6 rounded-lg shadow sm:p-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Test Cycle Context</h2>
                    <div className="space-y-4">
                        <div>
                            <label htmlFor="testUrl" className="block text-sm font-medium text-gray-700">URL to Test *</label>
                            <input
                                type="url"
                                id="testUrl"
                                className={`mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border rounded-md text-black p-2 ${
                                  urlError ? 'border-red-300' : 'border-gray-300'
                                }`}
                                placeholder="https://example.com"
                                value={testUrl}
                                onChange={(e) => {
                                  setTestUrl(e.target.value);
                                  if (urlError) setUrlError('');
                                }}
                                disabled={status === 'RUNNING' || status === 'PENDING'}
                            />
                            {urlError && (
                              <p className="mt-1 text-sm text-red-600">{urlError}</p>
                            )}
                        </div>
                        <div>
                            <label htmlFor="overview" className="block text-sm font-medium text-gray-700">Cycle Overview</label>
                            <textarea
                                id="overview"
                                rows={3}
                                className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md text-black border p-2"
                                placeholder="Paste the cycle overview here..."
                                value={cycleOverview}
                                onChange={(e) => setCycleOverview(e.target.value)}
                                disabled={status === 'RUNNING' || status === 'PENDING'}
                            />
                        </div>
                        <div>
                            <label htmlFor="instructions" className="block text-sm font-medium text-gray-700">Testing Instructions</label>
                            <textarea
                                id="instructions"
                                rows={3}
                                className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md text-black border p-2"
                                placeholder="Paste specific testing instructions/scope here..."
                                value={testingInstructions}
                                onChange={(e) => setTestingInstructions(e.target.value)}
                                disabled={status === 'RUNNING' || status === 'PENDING'}
                            />
                        </div>
                        <div>
                            <label htmlFor="provider" className="block text-sm font-medium text-gray-700">Reporting Provider</label>
                            <select
                                id="provider"
                                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md text-black border"
                                value={provider}
                                onChange={(e) => setProvider(e.target.value as 'uTest' | 'test.io')}
                                disabled={status === 'RUNNING' || status === 'PENDING'}
                            >
                                <option value="uTest">uTest</option>
                                <option value="test.io">test.io</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow sm:p-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Actions</h2>
                    <button
                        onClick={handleRunTests}
                        disabled={status === 'RUNNING' || status === 'PENDING' || isOffline}
                        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {(status === 'RUNNING' || status === 'PENDING') ? 'Running...' : 'Run Automated Tests'}
                    </button>
                    {isOffline && (
                      <p className="mt-2 text-sm text-red-600 text-center">Cannot run tests while offline</p>
                    )}
                </div>

                {/* Enhanced Loading State */}
                <div className="bg-white p-6 rounded-lg shadow sm:p-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Status</h2>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700">{loadingState.message}</span>
                        {loadingState.type !== 'idle' && loadingState.type !== 'completed' && loadingState.type !== 'error' && (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
                        )}
                      </div>
                      {loadingState.progress && (
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-indigo-600 h-2 rounded-full transition-all duration-300" 
                            style={{ width: `${loadingState.progress}%` }}
                          ></div>
                        </div>
                      )}
                    </div>
                </div>

                 <div className="bg-white p-6 rounded-lg shadow sm:p-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Execution Logs</h2>
                    <div className="h-64 overflow-y-auto bg-gray-900 text-gray-100 p-4 rounded text-sm font-mono">
                        {logs.length === 0 ? (
                            <span className="text-gray-500">No logs available...</span>
                        ) : (
                            logs.map((log, i) => (
                              <div key={i} className="mb-1">
                                <span className="text-gray-400 text-xs">[{new Date().toLocaleTimeString()}]</span> {log}
                              </div>
                            ))
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
                                        { (selectedBug.screenshot_path || selectedBug.video_path) && (
                                            <div>
                                                <strong>Artifacts:</strong>
                                                <div className="flex space-x-2 mt-1">
                                                    {selectedBug.screenshot_path && (
                                                        <a 
                                                            href={`${API_URL}${selectedBug.screenshot_path}`} 
                                                            target="_blank" 
                                                            rel="noopener noreferrer" 
                                                            className="text-indigo-600 hover:text-indigo-900 text-sm font-medium"
                                                        >
                                                            Screenshot
                                                        </a>
                                                    )}
                                                    {selectedBug.video_path && (
                                                        <a 
                                                            href={`${API_URL}${selectedBug.video_path}`} 
                                                            target="_blank" 
                                                            rel="noopener noreferrer" 
                                                            className="text-indigo-600 hover:text-indigo-900 text-sm font-medium"
                                                        >
                                                            Video
                                                        </a>
                                                    )}
                                                </div>
                                            </div>
                                        )}
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
                        <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse gap-2">
                             <button
                                type="button"
                                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm"
                                onClick={() => copyToClipboard('uTest')}
                            >
                                Copy for uTest
                            </button>
                            <button
                                type="button"
                                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                                onClick={() => copyToClipboard('test.io')}
                            >
                                Copy for test.io
                            </button>
                            <button
                                type="button"
                                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
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
