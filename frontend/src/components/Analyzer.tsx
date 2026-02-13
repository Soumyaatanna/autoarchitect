import React, { useState, useEffect } from 'react';
import { analyzeRepo, getJobStatus } from '../api';
import DiagramViewer from './DiagramViewer';
import SummaryViewer from './SummaryViewer';
import { ArrowRight, Loader2, Github, CheckCircle, AlertTriangle, Cpu, Network, FileCode } from 'lucide-react';

const Analyzer: React.FC = () => {
    const [repoUrl, setRepoUrl] = useState('');
    const [token, setToken] = useState('');
    const [status, setStatus] = useState<string>('idle');
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [loadingStep, setLoadingStep] = useState<string>('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setStatus('submitting');
        setError(null);
        setResult(null);
        setLoadingStep('Initializing...');

        try {
            const data = await analyzeRepo(repoUrl, token || undefined);
            setStatus('queued');
            pollStatus(data.job_id);
        } catch (err: any) {
            setError(err.message || 'Failed to start analysis');
            setStatus('idle');
        }
    };

    const pollStatus = async (id: string) => {
        const interval = setInterval(async () => {
            try {
                const data = await getJobStatus(id);
                if (data.status === 'completed') {
                    clearInterval(interval);
                    setStatus('completed');
                    setResult(data.result);
                } else if (data.status === 'failed') {
                    clearInterval(interval);
                    setStatus('failed');
                    setError(data.error || 'Job failed');
                } else if (data.status === 'processing') {
                    setLoadingStep('Analyzing Code Structure & Querying LLM...');
                }
            } catch (err) {
                clearInterval(interval);
                setError('Lost connection to server');
                setStatus('failed');
            }
        }, 2000);
    };

    return (
        <div className="max-w-5xl mx-auto space-y-12">
            {/* Hero Section */}
            <div className="text-center space-y-4">
                <h1 className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 drop-shadow-sm">
                    AutoArchitect AI
                </h1>
                <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                    Instant architectural diagrams and technical summaries from your GitHub repositories.
                </p>
            </div>

            {/* Input Card */}
            <div className="bg-white/80 backdrop-blur-lg p-8 rounded-2xl shadow-xl border border-white/50 relative overflow-hidden group hover:shadow-2xl transition-all duration-300">
                <div className="absolute top-0 right-0 w-64 h-64 bg-purple-100 rounded-full mix-blend-multiply filter blur-3xl opacity-30 -mr-32 -mt-32"></div>
                <div className="absolute bottom-0 left-0 w-64 h-64 bg-blue-100 rounded-full mix-blend-multiply filter blur-3xl opacity-30 -ml-32 -mb-32"></div>

                <form onSubmit={handleSubmit} className="relative z-10 space-y-6">
                    <div className="space-y-2">
                        <label className="block text-sm font-semibold text-gray-700">
                            GitHub Repository URL
                        </label>
                        <div className="relative group">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400 group-focus-within:text-indigo-500 transition-colors">
                                <Github size={20} />
                            </div>
                            <input
                                type="url"
                                required
                                placeholder="https://github.com/username/repo"
                                className="block w-full pl-10 pr-3 py-4 border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all shadow-sm"
                                value={repoUrl}
                                onChange={(e) => setRepoUrl(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="block text-sm font-semibold text-gray-700">
                            GitHub Token <span className="text-gray-400 font-normal">(Optional, for private repos)</span>
                        </label>
                        <input
                            type="password"
                            placeholder="ghp_..."
                            className="block w-full px-4 py-3 border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all shadow-sm"
                            value={token}
                            onChange={(e) => setToken(e.target.value)}
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={status === 'submitting' || status === 'queued' || status === 'processing'}
                        className="w-full py-4 px-6 rounded-xl font-bold text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-4 focus:ring-indigo-300 disabled:opacity-70 disabled:cursor-not-allowed transform hover:-translate-y-0.5 transition-all shadow-lg hover:shadow-indigo-500/30 flex justify-center items-center"
                    >
                        {['submitting', 'queued', 'processing'].includes(status) ? (
                            <>
                                <Loader2 className="animate-spin -ml-1 mr-2 h-5 w-5" />
                                Processing...
                            </>
                        ) : (
                            <>
                                Analyze Repository <ArrowRight className="ml-2 h-5 w-5" />
                            </>
                        )}
                    </button>
                </form>
            </div>

            {/* Loading State */}
            {['submitting', 'queued', 'processing'].includes(status) && (
                <div className="flex flex-col items-center justify-center p-12 bg-white/50 backdrop-blur-sm rounded-2xl border border-dashed border-indigo-200 animate-pulse">
                    <Loader2 className="h-16 w-16 text-indigo-600 animate-spin mb-6" />
                    <h3 className="text-2xl font-bold text-gray-800 mb-2">Analyzing Codebase</h3>
                    <p className="text-indigo-600 font-medium bg-indigo-50 px-4 py-1 rounded-full">
                        {loadingStep || 'Initializing...'}
                    </p>
                    <div className="flex gap-8 mt-8 text-gray-400 text-sm">
                        <span className="flex items-center gap-2"><FileCode size={16} /> Parsing AST</span>
                        <span className="flex items-center gap-2"><Network size={16} /> Building Graph</span>
                        <span className="flex items-center gap-2"><Cpu size={16} /> AI Reasoning</span>
                    </div>
                </div>
            )}

            {/* Error State */}
            {error && (
                <div className="p-6 bg-red-50 border border-red-100 rounded-2xl flex items-start gap-4 shadow-sm animate-fade-in-up">
                    <div className="p-2 bg-red-100 rounded-full text-red-600">
                        <AlertTriangle className="h-6 w-6" />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-red-800">Analysis Failed</h3>
                        <p className="text-red-600 mt-1">{error}</p>
                    </div>
                </div>
            )}

            {/* Results */}
            {status === 'completed' && result && (
                <div className="space-y-8 animate-fade-in-up">

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Summary Card */}
                        <div className="lg:col-span-1 bg-white p-6 rounded-2xl shadow-lg border border-gray-100 h-fit">
                            <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                                <FileCode className="text-purple-500" />
                                Summary
                            </h2>
                            <SummaryViewer content={result.summary} />
                        </div>

                        {/* Diagram Card */}
                        <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-lg border border-gray-100">
                            <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                                <Network className="text-blue-500" />
                                Architecture Diagram
                            </h2>
                            <DiagramViewer chart={result.mermaid} />
                        </div>
                    </div>

                    <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex justify-between items-center text-green-800">
                        <div className="flex items-center">
                            <CheckCircle className="h-5 w-5 mr-3" />
                            <span className="font-medium">Analysis Completed Successfully</span>
                        </div>
                        <button
                            onClick={() => setStatus('idle')}
                            className="text-sm font-bold underline hover:text-green-900"
                        >
                            Analyze Another
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Analyzer;
