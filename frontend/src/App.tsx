import { useState, useEffect, useCallback } from 'react';
import { Library, BookOpen, Feather, Book, User, Upload, Trash2, Loader2, CheckCircle2, Bookmark, Plus, MessageSquare, Edit2 } from 'lucide-react';
import { chat, ingestFile, listDocuments, deleteDocument, API_URL } from './api';
import { 
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, 
    LineChart, Line, AreaChart, Area, PieChart, Pie, Cell 
} from 'recharts';

interface Msg {
    role: 'user' | 'bot';
    text: string;
    citations?: any[];
    tool_trace?: any[];
    chart_data?: {
        config: {
            chart_type: 'bar' | 'line' | 'area' | 'pie';
            x_axis: string;
            y_axis: string;
            title: string;
        };
        data: any[];
    };
}

const COLORS = ['#8c4a23', '#c2985b', '#5c4d3c', '#d1c8bd', '#3a322b', '#733c1c'];

const ChartRenderer = ({ chart_data }: { chart_data: Msg['chart_data'] }) => {
    if (!chart_data) return null;
    const { config, data } = chart_data;
    const { chart_type, x_axis, y_axis, title } = config;

    const renderChart = () => {
        switch (chart_type) {
            case 'line':
                return (
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#3a322b" />
                        <XAxis dataKey={x_axis} stroke="#a39788" />
                        <YAxis stroke="#a39788" />
                        <Tooltip contentStyle={{ backgroundColor: '#1e1a17', borderColor: '#3a322b', color: '#e8e4df' }} />
                        <Legend />
                        <Line type="monotone" dataKey={y_axis} stroke="#c2985b" activeDot={{ r: 8 }} />
                    </LineChart>
                );
            case 'area':
                return (
                    <AreaChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#3a322b" />
                        <XAxis dataKey={x_axis} stroke="#a39788" />
                        <YAxis stroke="#a39788" />
                        <Tooltip contentStyle={{ backgroundColor: '#1e1a17', borderColor: '#3a322b', color: '#e8e4df' }} />
                        <Legend />
                        <Area type="monotone" dataKey={y_axis} stroke="#c2985b" fill="#8c4a23" fillOpacity={0.4} />
                    </AreaChart>
                );
            case 'pie':
                return (
                    <PieChart>
                        <Pie
                            data={data}
                            dataKey={y_axis}
                            nameKey={x_axis}
                            cx="50%"
                            cy="50%"
                            outerRadius={80}
                            label
                        >
                            {data.map((_, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: '#1e1a17', borderColor: '#3a322b', color: '#e8e4df' }} />
                        <Legend />
                    </PieChart>
                );
            case 'bar':
            default:
                return (
                    <BarChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#3a322b" />
                        <XAxis dataKey={x_axis} stroke="#a39788" />
                        <YAxis stroke="#a39788" />
                        <Tooltip contentStyle={{ backgroundColor: '#1e1a17', borderColor: '#3a322b', color: '#e8e4df' }} />
                        <Legend />
                        <Bar dataKey={y_axis} fill="#8c4a23" radius={[4, 4, 0, 0]} />
                    </BarChart>
                );
        }
    };

    return (
        <div className="mt-4 p-4 bg-[#1e1a17] rounded-xl border border-[#3a322b]">
            <h4 className="text-sm font-serif font-semibold text-[#c2985b] mb-4 text-center">{title}</h4>
            <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    {renderChart()}
                </ResponsiveContainer>
            </div>
        </div>
    );
};

interface DocInfo {
    doc_id: string;
    filename: string;
    chunks: number;
}

interface ChatSession {
    id: string;
    title: string;
    messages: Msg[];
}

function App() {
    const [sessions, setSessions] = useState<ChatSession[]>([{ id: 'default', title: 'New Conversation', messages: [] }]);
    const [currentSessionId, setCurrentSessionId] = useState('default');
    const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
    const [editingTitle, setEditingTitle] = useState('');
    const [input, setInput] = useState('');
    const [mode, setMode] = useState('auto');
    const [loading, setLoading] = useState(false);
    const [documents, setDocuments] = useState<DocInfo[]>([]);
    const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'processing' | 'done' | 'error'>('idle');
    const [uploadMsg, setUploadMsg] = useState('');

    const currentSession = sessions.find(s => s.id === currentSessionId) || sessions[0];
    const messages = currentSession.messages;

    // Load sessions from localStorage
    useEffect(() => {
        const saved = localStorage.getItem('library_chat_sessions');
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                if (parsed && parsed.length > 0) {
                    setSessions(parsed);
                    setCurrentSessionId(parsed[0].id);
                }
            } catch(e) {}
        }
    }, []);

    // Save sessions to localStorage
    useEffect(() => {
        localStorage.setItem('library_chat_sessions', JSON.stringify(sessions));
    }, [sessions]);

    const createNewSession = () => {
        const newId = Date.now().toString();
        setSessions(prev => [{ id: newId, title: 'New Conversation', messages: [] }, ...prev]);
        setCurrentSessionId(newId);
    };

    const deleteSession = (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (!window.confirm("Archive this conversation?")) return;
        
        setSessions(prev => {
            const remaining = prev.filter(s => s.id !== id);
            if (remaining.length === 0) {
                const newId = Date.now().toString();
                setCurrentSessionId(newId);
                return [{ id: newId, title: 'New Conversation', messages: [] }];
            }
            if (currentSessionId === id) {
                setCurrentSessionId(remaining[0].id);
            }
            return remaining;
        });
    };

    const startEditing = (id: string, currentTitle: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setEditingSessionId(id);
        setEditingTitle(currentTitle);
    };

    const saveEditing = () => {
        if (editingSessionId && editingTitle.trim()) {
            setSessions(prev => prev.map(s => s.id === editingSessionId ? { ...s, title: editingTitle.trim() } : s));
        }
        setEditingSessionId(null);
    };

    const fetchDocuments = useCallback(async () => {
        try {
            const docs = await listDocuments();
            setDocuments(docs);
        } catch (_) {}
    }, []);

    useEffect(() => {
        fetchDocuments();
        const interval = setInterval(fetchDocuments, 5000);
        return () => clearInterval(interval);
    }, [fetchDocuments]);

    const sendMessage = async () => {
        if (!input.trim()) return;
        const userMsg = input;
        
        const isFirstMessage = messages.length === 0;
        const newTitle = isFirstMessage ? (userMsg.length > 25 ? userMsg.substring(0, 25) + '...' : userMsg) : currentSession.title;

        setSessions(prev => prev.map(s => 
            s.id === currentSessionId 
                ? { ...s, title: newTitle, messages: [...s.messages, { role: 'user', text: userMsg }] }
                : s
        ));
        
        setInput('');
        setLoading(true);

        try {
            const res = await chat({ message: userMsg, mode, session_id: currentSessionId });
            setSessions(prev => prev.map(s => 
                s.id === currentSessionId 
                    ? { 
                        ...s, 
                        messages: [...s.messages, {
                            role: 'bot',
                            text: res.answer_text,
                            citations: res.citations,
                            tool_trace: res.tool_trace,
                            chart_data: res.chart_data
                        }] 
                      }
                    : s
            ));
        } catch (err: any) {
            let errMsg = 'Error connecting to server.';
            if (err?.message) errMsg = err.message;
            setSessions(prev => prev.map(s => 
                s.id === currentSessionId 
                    ? { ...s, messages: [...s.messages, { role: 'bot', text: `⚠️ ${errMsg}` }] }
                    : s
            ));
        }
        setLoading(false);
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            const file = e.target.files[0];
            e.target.value = '';
            setUploadStatus('uploading');
            setUploadMsg(`Uploading ${file.name}...`);
            try {
                await ingestFile(file);
                setUploadStatus('processing');
                setUploadMsg(`Processing ${file.name}... (Shelving the tome)`);
                // Poll until the doc appears in the list
                let attempts = 0;
                const poll = setInterval(async () => {
                    attempts++;
                    await fetchDocuments();
                    if (attempts > 20) {
                        clearInterval(poll);
                        setUploadStatus('done');
                        setUploadMsg('Done! Record archived.');
                        setTimeout(() => setUploadStatus('idle'), 3000);
                    }
                }, 2000);
            } catch (err) {
                setUploadStatus('error');
                setUploadMsg('Archiving failed. Please try again.');
                setTimeout(() => setUploadStatus('idle'), 4000);
            }
        }
    };

    const handleDelete = async (doc_id: string, filename: string) => {
        if (!window.confirm(`Discard "${filename}" from the archive?`)) return;
        try {
            await deleteDocument(doc_id);
            await fetchDocuments();
        } catch (_) {
            alert('Failed to remove record.');
        }
    };

    return (
        <div className="flex h-screen bg-[#1e1a17] text-[#e8e4df] font-sans selection:bg-[#c2985b] selection:text-white">
            {/* Sidebar */}
            <div className="w-64 bg-[#25201c] p-4 flex flex-col border-r border-[#3a322b] hidden md:flex shadow-xl z-20">
                <h2 className="text-xl font-serif font-bold mb-6 flex items-center gap-3 text-[#c2985b] tracking-wide">
                    <Library className="text-[#8c4a23]" size={28} /> Library Archive
                </h2>

                {/* SESSIONS LIST */}
                <div className="mb-6">
                    <button 
                        onClick={createNewSession}
                        className="flex w-full items-center justify-center gap-2 p-2.5 mb-3 bg-[#3a322b] hover:bg-[#4a4036] border border-[#4a4036] rounded-lg text-[#e8e4df] text-sm font-medium transition-colors shadow-sm"
                    >
                        <Plus size={16} /> New Record
                    </button>
                    
                    <div className="space-y-1 max-h-48 overflow-y-auto pr-1 custom-scrollbar">
                        {sessions.map(s => (
                            <div
                                key={s.id}
                                onClick={() => setCurrentSessionId(s.id)}
                                className={`flex items-center gap-2 w-full text-left p-2.5 rounded-md text-sm transition-colors cursor-pointer group ${
                                    currentSessionId === s.id 
                                        ? 'bg-[#8c4a23] text-[#f9f8f6] shadow-md' 
                                        : 'text-[#d1c8bd] hover:bg-[#3a322b]/50'
                                }`}
                            >
                                <MessageSquare size={14} className="shrink-0 opacity-70" />
                                {editingSessionId === s.id ? (
                                    <input
                                        autoFocus
                                        type="text"
                                        value={editingTitle}
                                        onChange={e => setEditingTitle(e.target.value)}
                                        onBlur={saveEditing}
                                        onKeyDown={e => {
                                            if (e.key === 'Enter') saveEditing();
                                            if (e.key === 'Escape') setEditingSessionId(null);
                                        }}
                                        className="flex-1 bg-[#141210] text-[#e8e4df] px-1 outline-none rounded min-w-0"
                                        onClick={e => e.stopPropagation()}
                                    />
                                ) : (
                                    <span className="flex-1 truncate">{s.title}</span>
                                )}

                                {!editingSessionId && currentSessionId === s.id && (
                                    <div className="flex items-center gap-1 opacity-100">
                                        <button onClick={(e) => startEditing(s.id, s.title, e)} className="p-1 hover:text-[#d1c8bd] text-[#fbfaf9] opacity-70 hover:opacity-100 transition" title="Rename">
                                            <Edit2 size={12} />
                                        </button>
                                        <button onClick={(e) => deleteSession(s.id, e)} className="p-1 hover:text-red-300 text-[#fbfaf9] opacity-70 hover:opacity-100 transition" title="Archive">
                                            <Trash2 size={12} />
                                        </button>
                                    </div>
                                )}
                                {!editingSessionId && currentSessionId !== s.id && (
                                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button onClick={(e) => startEditing(s.id, s.title, e)} className="p-1 hover:text-white text-[#a39788] transition" title="Rename">
                                            <Edit2 size={12} />
                                        </button>
                                        <button onClick={(e) => deleteSession(s.id, e)} className="p-1 hover:text-red-400 text-[#a39788] transition" title="Archive">
                                            <Trash2 size={12} />
                                        </button>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                <div className="w-full h-px bg-[#3a322b] mb-6"></div>

                {/* Upload area */}
                <div className="mb-6">
                    <label className={`flex items-center justify-center w-full p-4 border-2 border-dashed rounded-lg cursor-pointer transition-all duration-300 ${
                        uploadStatus === 'uploading' || uploadStatus === 'processing'
                            ? 'border-[#c2985b] bg-[#c2985b]/10 cursor-not-allowed'
                            : 'border-[#4a4036] hover:border-[#c2985b] hover:bg-[#3a322b]/30'
                    }`}>
                        {uploadStatus === 'uploading' || uploadStatus === 'processing' ? (
                            <Loader2 size={20} className="mr-2 text-[#c2985b] animate-spin" />
                        ) : uploadStatus === 'done' ? (
                            <CheckCircle2 size={20} className="mr-2 text-green-500" />
                        ) : (
                            <Upload size={20} className="mr-2 text-[#8a7a69]" />
                        )}
                        <span className="text-sm font-medium text-[#d1c8bd]">
                            {uploadStatus === 'idle' ? 'Add Records (PDF/TXT)' : uploadMsg}
                        </span>
                        <input
                            type="file"
                            className="hidden"
                            onChange={handleFileUpload}
                            accept=".pdf,.txt,.csv,.md"
                            disabled={uploadStatus === 'uploading' || uploadStatus === 'processing'}
                        />
                    </label>
                    {uploadStatus === 'error' && (
                        <p className="text-xs text-red-400 mt-2 text-center">{uploadMsg}</p>
                    )}
                </div>

                {/* Document list */}
                <div className="flex-1 overflow-y-auto pr-1">
                    <h3 className="text-xs uppercase tracking-widest text-[#a39788] font-semibold mb-3">
                        Archived Tomes ({documents.length})
                    </h3>
                    {documents.length === 0 ? (
                        <p className="text-xs text-[#6e6153] text-center py-6 italic font-serif">The shelves are empty...<br/>Archive a record to begin.</p>
                    ) : (
                        <div className="space-y-1">
                            {documents.map(doc => (
                                <div
                                    key={doc.doc_id}
                                    className="flex items-center gap-3 p-2.5 rounded-md hover:bg-[#3a322b]/50 cursor-pointer text-sm group transition-colors border border-transparent hover:border-[#4a4036]"
                                >
                                    <Book size={16} className="text-[#c2985b] shrink-0" />
                                    <span className="flex-1 truncate text-[#d1c8bd]" title={doc.filename}>
                                        {doc.filename}
                                        <span className="text-[11px] text-[#8a7a69] block mt-0.5 font-mono">{doc.chunks} fragments</span>
                                    </span>
                                    <button
                                        onClick={() => handleDelete(doc.doc_id, doc.filename)}
                                        className="opacity-0 group-hover:opacity-100 text-[#8a7a69] hover:text-red-400 transition-opacity"
                                        title="Remove record"
                                    >
                                        <Trash2 size={14} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col relative bg-[url('https://www.transparenttextures.com/patterns/cream-paper.png')] bg-blend-soft-light bg-[#1e1a17]">
                {/* Topbar */}
                <header className="h-16 bg-[#25201c]/90 backdrop-blur-sm border-b border-[#3a322b] flex items-center justify-between px-8 shadow-sm z-10 sticky top-0">
                    <h1 className="text-lg font-serif font-semibold text-[#e8e4df] tracking-wide">Librarian's Desk</h1>
                    <div className="flex bg-[#141210] rounded-lg p-1.5 shadow-inner border border-[#3a322b]">
                        {['auto', 'rag', 'sql'].map(m => (
                            <button
                                key={m}
                                onClick={() => setMode(m)}
                                className={`px-4 py-1.5 text-xs tracking-wider uppercase font-semibold rounded-md transition-all duration-300 ${mode === m ? 'bg-[#8c4a23] text-[#f9f8f6] shadow-md' : 'text-[#a39788] hover:text-[#e8e4df] hover:bg-[#2d2824]'
                                    }`}
                            >
                                {m}
                            </button>
                        ))}
                    </div>
                </header>

                {/* Chat Messages */}
                <main className="flex-1 overflow-y-auto p-4 md:p-8 space-y-8">
                    {messages.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-[#8a7a69] max-w-md mx-auto text-center">
                            <div className="w-24 h-24 mb-6 rounded-full bg-[#25201c] flex items-center justify-center border border-[#3a322b] shadow-xl">
                                <BookOpen size={40} className="text-[#c2985b]" />
                            </div>
                            <h2 className="text-2xl font-serif text-[#d1c8bd] mb-3">Welcome to the Archives.</h2>
                            <p className="text-base leading-relaxed">Ask me regarding the contents of our shelves, specific metrics, or any general inquiry.</p>
                            {documents.length > 0 && (
                                <p className="text-sm mt-6 px-4 py-2 bg-[#25201c] rounded-full border border-[#3a322b] text-[#c2985b] inline-block">
                                    <Bookmark size={14} className="inline mr-2 mb-0.5" />{documents.length} tomes ready for review.
                                </p>
                            )}
                        </div>
                    ) : (
                        <div className="max-w-4xl mx-auto space-y-8">
                            {messages.map((msg, idx) => (
                                <div key={idx} className={`flex gap-5 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                                    {msg.role === 'bot' && (
                                        <div className="w-10 h-10 rounded-full bg-[#1e1a17] flex items-center justify-center shrink-0 border-2 border-[#3a322b] shadow-md">
                                            <Library size={18} className="text-[#c2985b]" />
                                        </div>
                                    )}
                                    <div className={`max-w-[80%] p-5 shadow-lg relative ${msg.role === 'user' ? 'bg-[#8c4a23] text-[#fbfaf9] rounded-2xl rounded-tr-sm' : 'bg-[#2d2824] text-[#e8e4df] border border-[#3a322b] rounded-2xl rounded-tl-sm font-serif leading-relaxed text-lg'
                                        }`}
                                         style={msg.role === 'bot' ? {boxShadow: 'inset 0 1px 1px rgba(255,255,255,0.05)'} : {}}
                                    >
                                        <div className="whitespace-pre-wrap flex-col">
                                            {msg.text.split(/(\[.*?\]\(.*?\))/g).map((part, i) => {
                                                const match = part.match(/\[(.*?)\]\((.*?)\)/);
                                                if (match) {
                                                    return <a key={i} href={match[2]} target="_blank" rel="noreferrer" className="text-[#c2985b] hover:font-bold hover:text-[#d1c8bd] underline underline-offset-2 transition-colors">{match[1]}</a>;
                                                }
                                                return <span key={i}>{part}</span>;
                                            })}
                                        </div>

                                        {/* Chart Rendering */}
                                        {msg.role === 'bot' && msg.chart_data && (
                                            <div className="font-sans mt-6">
                                                <ChartRenderer chart_data={msg.chart_data} />
                                            </div>
                                        )}

                                        {/* Tool Trace & Citations */}
                                        {msg.role === 'bot' && (msg.tool_trace?.length || msg.citations?.length) ? (
                                            <div className="mt-6 pt-5 border-t border-[#4a4036] font-sans">
                                                {msg.tool_trace && msg.tool_trace.length > 0 && (
                                                    <div className="mb-4">
                                                        <p className="text-[#c2985b] text-xs uppercase tracking-widest font-bold mb-2 flex items-center gap-1">
                                                            <Feather size={12} /> Librarian's Ledger
                                                        </p>
                                                        <ul className="list-disc pl-5 text-[#a39788] text-sm space-y-1.5">
                                                            {msg.tool_trace.map((t, i) => (
                                                                <li key={i}>
                                                                    <span className="font-medium text-[#d1c8bd]">{t.step}</span>
                                                                    {t.result && <span className="opacity-70 ml-2">({typeof t.result === 'string' ? t.result.substring(0, 50) + '...' : JSON.stringify(t.result)})</span>}
                                                                    {t.query && <span className="text-[#c2985b] ml-1">[{t.query}]</span>}
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}
                                                {msg.citations && msg.citations.length > 0 && (
                                                    <div>
                                                        <p className="text-[#c2985b] text-xs uppercase tracking-widest font-bold mb-2 flex items-center gap-1">
                                                            <Bookmark size={12} /> References
                                                        </p>
                                                        <div className="flex flex-wrap gap-2">
                                                            {msg.citations.map((c, i) => (
                                                                <a key={i} href={`${API_URL}/uploads/${encodeURIComponent(c.filename)}`} target="_blank" rel="noreferrer" className="bg-[#1e1a17] border border-[#3a322b] px-2.5 py-1 rounded text-xs text-[#a39788] shadow-inner hover:text-[#c2985b] hover:border-[#c2985b] transition-colors inline-block">
                                                                    Tome: {c.filename ? c.filename : `${c.doc_id.substring(0, 6)}...`} | Pg: {c.chunk} | Match: {(c.score * 100).toFixed(1)}%
                                                                </a>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        ) : null}
                                    </div>
                                    {msg.role === 'user' && (
                                        <div className="w-10 h-10 rounded-full bg-[#25201c] border-2 border-[#4a4036] flex items-center justify-center shrink-0 shadow-md">
                                            <User size={18} className="text-[#a39788]" />
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                    {loading && (
                        <div className="max-w-4xl mx-auto flex gap-5">
                            <div className="w-10 h-10 rounded-full bg-[#1e1a17] flex items-center justify-center shrink-0 border-2 border-[#3a322b] shadow-md">
                                <Library size={18} className="text-[#c2985b]" />
                            </div>
                            <div className="p-4 px-6 bg-[#2d2824] border border-[#3a322b] rounded-2xl rounded-tl-sm flex items-center shadow-lg">
                                <span className="flex gap-1.5 items-center">
                                    <span className="w-2 h-2 bg-[#c2985b] rounded-full animate-bounce" style={{animationDelay: '0ms'}}></span>
                                    <span className="w-2 h-2 bg-[#c2985b] rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
                                    <span className="w-2 h-2 bg-[#c2985b] rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
                                </span>
                            </div>
                        </div>
                    )}
                </main>

                {/* Input Area */}
                <footer className="p-4 md:p-6 bg-[#25201c] border-t border-[#3a322b] shadow-[0_-10px_30px_rgba(0,0,0,0.2)]">
                    <div className="max-w-4xl mx-auto flex items-end gap-3 bg-[#141210] rounded-2xl border border-[#3a322b] p-2.5 shadow-inner focus-within:ring-2 ring-[#c2985b]/40 focus-within:border-[#c2985b] transition-all">
                        <textarea
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={e => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    sendMessage();
                                }
                            }}
                            placeholder="Inquire the archives... (Shift+Enter for new line)"
                            className="flex-1 max-h-32 min-h-[44px] bg-transparent resize-none outline-none py-2 px-4 text-[#e8e4df] placeholder-[#6e6153] font-serif text-lg leading-relaxed"
                            rows={1}
                        />
                        <button
                            onClick={sendMessage}
                            disabled={loading || !input.trim()}
                            className="p-3.5 bg-gradient-to-br from-[#8c4a23] to-[#733c1c] text-[#fbfaf9] rounded-xl hover:from-[#a65628] hover:to-[#8c4a23] disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md shrink-0 mb-0.5 border border-[#4a2e1b]"
                            title="Send Missive"
                        >
                            <Feather size={20} className="transform -rotate-12" />
                        </button>
                    </div>
                </footer>
            </div>
        </div>
    );
}

export default App;
