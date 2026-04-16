import Head from 'next/head';
import { useState } from 'react';
import ClaimInput from '../components/ClaimInput';
import AnalysisResult from '../components/AnalysisResult';
import SettingsModal from '../components/SettingsModal';

export default function Home() {
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');

    // Settings State
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [strictMode, setStrictMode] = useState(true);

    const handleAnalyze = async (claimText: string) => {
        setIsLoading(true);
        setError('');
        setResult(null);

        try {
            const response = await fetch('http://localhost:8000/analyze-claim', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    claim_text: claimText,
                    strict_mode: strictMode
                }),
            });

            if (!response.ok) {
                throw new Error('Analysis failed. Please try again.');
            }

            const data = await response.json();
            setResult(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An unexpected error occurred');
        } finally {
            setIsLoading(false);
        }
    };

    const showHistory = () => {
        alert("History feature coming in Phase 6!");
    };

    return (
        <div className="min-h-screen bg-[var(--bg-primary)] text-white selection:bg-violet-500/30">
            <Head>
                <title>APEX | AI Patent Examiner</title>
                <meta name="description" content="Advanced Patent Examination System" />
                <link rel="icon" href="/favicon.ico" />
            </Head>

            <SettingsModal
                isOpen={isSettingsOpen}
                onClose={() => setIsSettingsOpen(false)}
                strictMode={strictMode}
                setStrictMode={setStrictMode}
            />

            {/* Navbar */}
            <nav className="fixed top-0 w-full z-50 glass-panel border-b-0 border-b-white/5">
                <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-gradient-to-br from-violet-500 to-blue-600 rounded-lg flex items-center justify-center font-bold text-white shadow-[0_0_15px_rgba(139,92,246,0.5)]">
                            A
                        </div>
                        <span className="text-xl font-bold tracking-tight">APEX</span>
                    </div>
                    <div className="flex items-center gap-6 text-sm font-medium text-slate-400">
                        <span onClick={showHistory} className="hover:text-white cursor-pointer transition-colors">History</span>
                        <span onClick={() => setIsSettingsOpen(true)} className="hover:text-white cursor-pointer transition-colors">Settings</span>
                        <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700"></div>
                    </div>
                </div>
            </nav>

            <main className="pt-32 px-6 pb-20">
                {/* Hero Section */}
                {!result && !isLoading && (
                    <div className="text-center mb-16 animate-fade-in">
                        <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-slate-400">
                            Patent Analysis, <br />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-blue-400 glow-text">
                                Reimagined.
                            </span>
                        </h1>
                        <p className="text-slate-400 text-lg md:text-xl max-w-2xl mx-auto leading-relaxed mb-4">
                            Enter your patent claim below. APEX will decompose it, search millions of documents,
                            and provide a legal-grade validity opinion in seconds.
                        </p>
                        <div className="flex items-center justify-center gap-2 text-sm text-slate-500">
                            <span className={`w-2 h-2 rounded-full ${strictMode ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
                            Strict Citation Mode: {strictMode ? 'ON' : 'OFF'}
                        </div>
                    </div>
                )}

                {/* Input Section */}
                {!result && (
                    <ClaimInput onAnalyze={handleAnalyze} isLoading={isLoading} />
                )}

                {/* Loading State */}
                {isLoading && (
                    <div className="flex flex-col items-center justify-center mt-20 animate-pulse-slow">
                        <div className="w-16 h-16 border-4 border-violet-500/30 border-t-violet-500 rounded-full animate-spin mb-8"></div>
                        <h3 className="text-2xl font-bold text-white mb-2">Analyzing Claim...</h3>
                        <p className="text-slate-400">Searching prior art database • Verifying citations • Generating opinion</p>
                    </div>
                )}

                {/* Error State */}
                {error && (
                    <div className="max-w-2xl mx-auto mt-10 p-6 bg-red-500/10 border border-red-500/20 rounded-xl text-center animate-fade-in">
                        <p className="text-red-400 font-medium">{error}</p>
                        <button
                            onClick={() => setError('')}
                            className="mt-4 text-sm text-slate-400 hover:text-white underline"
                        >
                            Try Again
                        </button>
                    </div>
                )}

                {/* Results Section */}
                {result && (
                    <div className="animate-fade-in">
                        <div className="mb-8 flex justify-center">
                            <button
                                onClick={() => setResult(null)}
                                className="text-slate-400 hover:text-white flex items-center gap-2 transition-colors"
                            >
                                ← Analyze Another Claim
                            </button>
                        </div>
                        <AnalysisResult data={result} />
                    </div>
                )}
            </main>
        </div>
    );
}
