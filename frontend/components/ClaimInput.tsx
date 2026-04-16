import React, { useState } from 'react';

interface ClaimInputProps {
    onAnalyze: (claimText: string) => void;
    isLoading: boolean;
}

const ClaimInput: React.FC<ClaimInputProps> = ({ onAnalyze, isLoading }) => {
    const [claim, setClaim] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (claim.trim()) {
            onAnalyze(claim);
        }
    };

    return (
        <div className="w-full max-w-4xl mx-auto animate-fade-in">
            <form onSubmit={handleSubmit} className="flex flex-col gap-6">
                <div className="glass-panel rounded-2xl p-1 relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-r from-violet-600/20 to-blue-600/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
                    <textarea
                        className="w-full h-48 bg-transparent text-slate-200 p-6 text-lg outline-none resize-none placeholder-slate-500 font-light leading-relaxed"
                        placeholder="Paste your patent claim here to begin analysis..."
                        value={claim}
                        onChange={(e) => setClaim(e.target.value)}
                        disabled={isLoading}
                    />
                </div>

                <div className="flex justify-end">
                    <button
                        type="submit"
                        disabled={isLoading || !claim.trim()}
                        className={`
              px-8 py-4 rounded-xl font-semibold text-white tracking-wide transition-all duration-300
              ${isLoading || !claim.trim()
                                ? 'bg-slate-700 cursor-not-allowed opacity-50'
                                : 'bg-gradient-to-r from-violet-600 to-blue-600 hover:shadow-[0_0_30px_rgba(139,92,246,0.5)] hover:scale-105 active:scale-95'}
            `}
                    >
                        {isLoading ? (
                            <span className="flex items-center gap-2">
                                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Analyzing...
                            </span>
                        ) : (
                            'ANALYZE CLAIM'
                        )}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default ClaimInput;
