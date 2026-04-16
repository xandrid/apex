import React from 'react';

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
    strictMode: boolean;
    setStrictMode: (value: boolean) => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose, strictMode, setStrictMode }) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            />

            {/* Modal Content */}
            <div className="relative w-full max-w-md glass-panel rounded-2xl p-6 shadow-2xl animate-fade-in border border-slate-700/50 bg-slate-900/90">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-bold text-white">Analysis Settings</h2>
                    <button
                        onClick={onClose}
                        className="text-slate-400 hover:text-white transition-colors"
                    >
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div className="space-y-6">
                    <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5">
                        <div>
                            <h3 className="font-semibold text-slate-200">Strict Citation Mode</h3>
                            <p className="text-sm text-slate-400 mt-1 max-w-[240px]">
                                Enforces matching citations to verifiable database IDs. Disables AI hallucinations.
                            </p>
                        </div>

                        <button
                            onClick={() => setStrictMode(!strictMode)}
                            className={`
                relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-300
                ${strictMode ? 'bg-violet-600' : 'bg-slate-600'}
              `}
                        >
                            <span
                                className={`
                  inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-300
                  ${strictMode ? 'translate-x-6' : 'translate-x-1'}
                `}
                            />
                        </button>
                    </div>
                </div>

                <div className="mt-8 flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium transition-colors"
                    >
                        Done
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SettingsModal;
