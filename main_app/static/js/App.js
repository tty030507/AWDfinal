const { useState, useEffect, useRef } = React;

// Global Axios configuration for CSRF Token
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

/**
 * 1. Chat Component (ChatPage)
 * Logic: Defined outside App to maintain state stability and prevent data loss during parent re-renders.
 */
const ChatPage = ({ user, onBack }) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [socket, setSocket] = useState(null);
    const [activeRecipient, setActiveRecipient] = useState(null); // 当前选中的人
    const [recentContacts, setRecentContacts] = useState([]); // 侧边栏列表
    const scrollRef = useRef(null);

    // 1. 初始化：获取最近联系过的人 (可以从 User 列表或专门接口拿)
    useEffect(() => {
        axios.get('/api/users/').then(res => {
        const allUsers = res.data.results || res.data;
        
        // --- 核心修复：使用 filter 过滤掉 ID 等于当前用户 ID 的项 ---
        const otherUsers = allUsers.filter(u => u.id !== user.id);
        
        setRecentContacts(otherUsers);
    });
}, [user.id]); // 依赖 user.id 确保数据准确

    // 2. 当切换聊天对象时：加载历史记录并重新连接 WebSocket
    useEffect(() => {
        if (!activeRecipient) return;

        // 加载历史记录
        axios.get(`/api/chathistory/?recipient_id=${activeRecipient.id}`)
    .then(res => {
        // --- 核心修复：兼容分页和非分页格式 ---
        const rawData = res.data.results || res.data; 
        
        if (Array.isArray(rawData)) {
            const history = rawData.map(m => ({
                sender: m.sender_name,
                message: m.message,
                timestamp:m.timestamp
            }));
            setMessages(history);
        } else {
            console.error("Unexpected data format:", res.data);
            setMessages([]);
        }
    })
    .catch(err => {
        console.error("Failed to load history", err);
        setMessages([]);
    });

        // 重连 WebSocket
        if (socket) socket.close();
        const roomName = user.id < activeRecipient.id 
            ? `${user.id}_${activeRecipient.id}` 
            : `${activeRecipient.id}_${user.id}`;
        
        const ws = new WebSocket(`ws://${window.location.host}/ws/chat/${roomName}/`);
        ws.onmessage = (e) => setMessages((prev) => [...prev, JSON.parse(e.data)]);
        setSocket(ws);

        return () => ws.close();
    }, [activeRecipient]);

    // 自动滚动
    useEffect(() => {
        if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }, [messages]);

    const handleSend = (e) => {
        e.preventDefault();
        if (input.trim() && socket) {
            socket.send(JSON.stringify({ message: input }));
            setInput('');
        }
    };

    return (
        <div className="container-fluid mt-4 animate__animated animate__fadeIn">
            <div className="row" style={{ height: '80vh' }}>
                
                {/* --- 左侧联系人栏 (类似你的截图) --- */}
                <div className="col-md-3 border-end bg-white rounded-start shadow-sm overflow-auto p-0">
                    <div className="p-3 border-bottom bg-primary text-white d-flex justify-content-between">
                        <h6 className="mb-0 fw-bold">Recent Chats</h6>
                        <i className="bi bi-person-plus" style={{cursor:'pointer'}} onClick={onBack}></i>
                    </div>
                    <div className="list-group list-group-flush">
                        {recentContacts.map(contact => (
                            <div 
                                key={contact.id}
                                onClick={() => setActiveRecipient(contact)}
                                className={`list-group-item list-group-item-action border-0 p-3 ${activeRecipient?.id === contact.id ? 'bg-light border-start border-primary border-4 fw-bold' : ''}`}
                                style={{ cursor: 'pointer', transition: '0.2s' }}
                            >
                                <div className="d-flex align-items-center">
                                    <div className="rounded-circle bg-secondary text-white me-3 d-flex align-items-center justify-content-center" style={{width:'40px', height:'40px'}}>
                                        {contact.real_name[0]}
                                    </div>
                                    <div>
                                        <div className="small">{contact.real_name}</div>
                                        <div className="text-muted small italic" style={{fontSize:'0.7rem'}}>Click to chat...</div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* --- 右侧聊天窗口 --- */}
                <div className="col-md-9 bg-white rounded-end shadow-sm d-flex flex-column p-0">
                    {activeRecipient ? (
                        <>
                            <div className="p-3 border-bottom d-flex align-items-center bg-white">
                                <h6 className="mb-0 fw-bold">Chatting with: {activeRecipient.real_name}</h6>
                            </div>
                            
                            <div className="flex-grow-1 bg-light p-4 overflow-auto" ref={scrollRef}>
                                {messages.map((m, i) => {
                                    const isMe = m.sender === user.real_name;
                                    return (
                                        <div key={i} className={`d-flex flex-column ${isMe ? 'align-items-end' : 'align-items-start'} mb-3`}>
                                            <div className={`bubble ${isMe ? 'bubble-me shadow' : 'bubble-them shadow-sm'}`}>
                                                <div className="small fw-bold mb-1" style={{ opacity: 0.8, fontSize: '0.7rem' }}>{m.sender} {m.timestamp}</div>
                                                {m.message}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>

                            <div className="p-3 border-top bg-white">
                                <form onSubmit={handleSend} className="input-group gap-2">
                                    <input className="form-control border-0 bg-light rounded-pill px-4" value={input} onChange={e => setInput(e.target.value)} placeholder="Type a message..." />
                                    <button className="btn btn-primary rounded-circle shadow" style={{width: '45px', height: '45px'}}><i className="bi bi-send-fill"></i></button>
                                </form>
                            </div>
                        </>
                    ) : (
                        <div className="d-flex flex-column align-items-center justify-content-center h-100 text-muted">
                            <i className="bi bi-chat-dots display-1 mb-3 opacity-25"></i>
                            <p>Select a contact to start conversation</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
/**
 * 2. Main Application Component (App)
 */
const App = () => {
    const [page, setPage] = useState('index');
    const [user, setUser] = useState(null);
    const [notifications, setNotifications] = useState([]);
    const [selectedRecipient, setSelectedRecipient] = useState(null);
    const [toast, setToast] = useState({ show: false, message: '' });

    // Initial check for authentication
    useEffect(() => {
        axios.get('/api/me/').then(res => {
            setUser(res.data);
            setPage('home');
        }).catch(() => console.log("Guest mode"));
    }, []);

    // Real-time notification WebSocket
    useEffect(() => {
        if (user) {
            axios.get('/api/notifications/').then(res => setNotifications(res.data.results || res.data));
            const socket = new WebSocket(`ws://${window.location.host}/ws/notifications/`);
            socket.onmessage = (e) => {
                const data = JSON.parse(e.data);
                setToast({ show: true, message: data.message });
                setNotifications(prev => [data, ...prev]);
            };
            return () => socket.close();
        }
    }, [user]);

    // Toast auto-hide logic
    useEffect(() => {
        if (toast.show) {
            const timer = setTimeout(() => setToast({ ...toast, show: false }), 5000);
            return () => clearTimeout(timer);
        }
    }, [toast.show]);

    const handleLogout = () => {
        setUser(null); setPage('index');
        window.location.href = '/logout/';
    };

    // --- Sub-components for pages ---

    const Navbar = () => (
        <nav className="navbar navbar-expand-lg navbar-dark bg-dark sticky-top py-3 navbar-blur shadow-sm mb-4">
            <div className="container">
                <a className="navbar-brand fw-bold fs-4 d-flex align-items-center" href="#" onClick={() => user ? setPage('home') : setPage('index')}>
                    <i className="bi bi-mortarboard-fill me-2 text-primary"></i>EduFlow
                </a>
                <div className="navbar-nav ms-auto gap-2">
                    {user ? (
                        <>
                            <button className="btn btn-link nav-link px-3" onClick={() => setPage('search')}>Search Members</button>
                            <button className="btn btn-link nav-link px-3" onClick={() => setPage('chat')}>Chat</button>
                            {user.user_type === 'teacher' && <button className="btn btn-link nav-link px-3 text-info" onClick={() => setPage('teacher_dashboard')}>Management</button>}
                            <button className="btn btn-link nav-link px-3" onClick={() => setPage('home')}>Home</button>
                            <button className="btn btn-outline-danger btn-sm rounded-pill px-4 ms-2" onClick={handleLogout}>Logout</button>
                        </>
                    ) : (
                        <>
                            <button className="btn btn-link nav-link px-4 text-white" onClick={() => setPage('login')}>Login</button>
                            <button className="btn btn-primary rounded-pill px-4 shadow" onClick={() => setPage('register')}>Join Us</button>
                        </>
                    )}
                </div>
            </div>
        </nav>
    );

    const IndexPage = () => (
        <div className="container py-5 text-center animate__animated animate__fadeIn">
            <div className="p-5 mb-4 bg-white card-modern shadow-lg py-5">
                <h1 className="display-4 fw-bold mb-3">Start Your <span className="text-primary">eLearning</span> Journey</h1>
                <p className="lead text-muted mb-5">Efficient interactive platform based on Django Channels + React.</p>
                <div className="d-flex gap-3 justify-content-center">
                    <button onClick={() => setPage('register')} className="btn btn-primary btn-lg px-5 shadow">Register Now</button>
                    <a href="/docs/" className="btn btn-outline-dark btn-lg px-4">REST API Swagger</a>
                </div>
            </div>
        </div>
    );

    const LoginPage = () => {
        const [formData, setFormData] = useState({ username: '', password: '' });
        const handleLogin = async (e) => {
            e.preventDefault();
            try {
                const res = await axios.post('/api/login/', formData);
                setUser(res.data.user); setPage('home');
            } catch (err) { alert("Login failed: Incorrect username or password"); }
        };
        return (
            <div className="row justify-content-center py-5 animate__animated animate__zoomIn">
                <div className="col-md-4 card-modern p-5 shadow-lg mt-5">
                    <h3 className="text-center fw-bold mb-4">User Login</h3>
                    <form onSubmit={handleLogin}>
                        <input className="form-control bg-light border-0 p-3 mb-3" placeholder="Username" onChange={e => setFormData({ ...formData, username: e.target.value })} required />
                        <input className="form-control bg-light border-0 p-3 mb-4" type="password" placeholder="Password" onChange={e => setFormData({ ...formData, password: e.target.value })} required />
                        <button className="btn btn-primary w-100 py-3 fw-bold">Enter Workspace</button>
                    </form>
                </div>
            </div>
        );
    };

    const RegisterPage = () => {
        const [formData, setFormData] = useState({ username: '', password: '', real_name: '', user_type: 'student' });
        const handleRegister = async (e) => {
            e.preventDefault();
            try {
                const res = await axios.post('/api/register/', formData);
                setUser(res.data.user); setPage('home');
            } catch (err) { alert("Registration failed, please check your inputs."); }
        };
        return (
            <div className="row justify-content-center py-5 animate__animated animate__fadeInUp">
                <div className="col-md-5 card-modern p-5 shadow-lg">
                    <h3 className="text-center fw-bold mb-4">Create Account</h3>
                    <form onSubmit={handleRegister}>
                        <input className="form-control bg-light border-0 p-3 mb-3" placeholder="Set Username" onChange={e => setFormData({ ...formData, username: e.target.value })} required />
                        <input className="form-control bg-light border-0 p-3 mb-3" placeholder="Real Name" onChange={e => setFormData({ ...formData, real_name: e.target.value })} required />
                        <input className="form-control bg-light border-0 p-3 mb-4" type="password" placeholder="Set Password" onChange={e => setFormData({ ...formData, password: e.target.value })} required />
                        <div className="mb-4 text-center">
                            <label className="form-label d-block fw-bold mb-3">I am a:</label>
                            <div className="btn-group w-100 shadow-sm rounded-pill overflow-hidden">
                                <button type="button" className={`btn ${formData.user_type === 'student' ? 'btn-primary' : 'btn-light'}`} onClick={() => setFormData({...formData, user_type: 'student'})}>Student</button>
                                <button type="button" className={`btn ${formData.user_type === 'teacher' ? 'btn-primary' : 'btn-light'}`} onClick={() => setFormData({...formData, user_type: 'teacher'})}>Teacher</button>
                            </div>
                        </div>
                        <button className="btn btn-primary w-100 py-3 fw-bold">Submit Registration</button>
                    </form>
                </div>
            </div>
        );
    };

    const HomePage = () => {
        const [courses, setCourses] = useState([]);
        const [myUpdates, setMyUpdates] = useState([]);
        const [statusText, setStatusText] = useState('');

        const fetchData = async () => {
            const cRes = await axios.get('/api/courses/'); setCourses(cRes.data.results || cRes.data);
            const uRes = await axios.get('/api/updates/'); setMyUpdates(uRes.data.results || uRes.data);
        };
        useEffect(() => { fetchData(); }, []);

        const handleEnrol = (id) => {
            axios.post(`/api/courses/${id}/enrol/`).then(() => { alert("Enrollment successful!"); fetchData(); })
                 .catch(e => alert(e.response.data.detail));
        };

        const handleFeedback = (courseId) => {
            const content = prompt("Please enter your feedback for this course:");
            if (content) {
                axios.post('/api/feedback/', { course: courseId, content: content })
                     .then(() => alert("Feedback sent to teacher successfully!"))
                     .catch(() => alert("Submission failed."));
            }
        };

        const handlePostUpdate = (e) => {
            e.preventDefault();
            axios.post('/api/updates/', { content: statusText }).then(() => {
                setStatusText(''); fetchData();
            });
        };

        return (
            <div className="row animate__animated animate__fadeIn">
                <div className="col-md-4">
                    <div className="card card-modern p-4 mb-4 text-center shadow-sm">
                        <div className="bg-primary text-white rounded-circle d-flex align-items-center justify-content-center m-auto shadow" style={{ width: '80px', height: '80px', fontSize: '2rem' }}>{user.real_name[0]}</div>
                        <h5 className="mt-3 fw-bold mb-1">{user.real_name}</h5>
                        <p className="badge bg-light text-primary border rounded-pill px-3">{user.user_type === 'teacher' ? 'Instructor' : 'Student'}</p>
                    </div>

                    {/* R1-i: Post Status Area */}
                     
                        <div className="card card-modern p-4 mb-4 shadow-sm">
                            <h6 className="fw-bold mb-3"><i className="bi bi-pencil-square me-2 text-primary"></i>Post Status</h6>
                            <form onSubmit={handlePostUpdate}>
                                <textarea className="form-control bg-light border-0 mb-2 small" rows="2" value={statusText} onChange={e => setStatusText(e.target.value)} placeholder="What did you learn today?" required></textarea>
                                <button className="btn btn-primary btn-sm w-100 rounded-pill">Post Update</button>
                            </form>
                            <hr />
                            <div style={{ maxHeight: '150px', overflowY: 'auto' }}>
                                {myUpdates.map(up => (
                                    <div key={up.id} className="small bg-light p-2 rounded mb-2 border-start border-primary">
                                        <div className="text-dark">{up.content}</div>
                                        <small className="text-muted" style={{fontSize: '0.65rem'}}>{new Date(up.created_at).toLocaleString()}</small>
                                    </div>
                                ))}
                            </div>
                        </div>
                    

                    <div className="card card-modern p-4 shadow-sm">
                        <h6 className="fw-bold mb-3"><i className="bi bi-bell-fill text-warning me-2"></i>Latest Notifications</h6>
                        <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                            {notifications.length > 0 ? notifications.map(n => (
                                <div key={n.id} onClick={() => n.message.includes("chat") && setPage('search')} className={`p-3 rounded-3 mb-2 small bg-light notif-item ${!n.is_read ? 'fw-bold border-start border-primary border-4' : 'opacity-75'}`}>
                                    {n.message}
                                </div>
                            )) : <p className="text-muted small text-center py-3">No new messages</p>}
                        </div>
                    </div>
                </div>
                <div className="col-md-8">
                    <div className="d-flex justify-content-between align-items-center mb-4">
                        <h4 className="fw-bold m-0">Recommended Courses</h4>
                        {user.user_type === 'teacher' && <button className="btn btn-primary btn-sm rounded-pill px-4 shadow-sm" onClick={() => setPage('create_course')}>+ Publish Course</button>}
                    </div>
                    <div className="row">
                        {courses.map(c => {
                            const isEnrolled = c.students?.includes(user.id);
                            return (
                                <div key={c.id} className="col-md-6 mb-4">
                                    <div className="card card-modern h-100 shadow-sm p-2 hover-shadow">
                                        <div className="card-body d-flex flex-column">
                                            <div className="text-primary small fw-bold mb-1">{c.teacher_name}</div>
                                            <h5 className="fw-bold">{c.title}</h5>
                                            <p className="text-muted small mb-3">{c.description}</p>
                                            
                                            <div className="mt-auto">
                                                {user.user_type === 'student' && (
                                                    isEnrolled ? (
                                                        <div className="bg-light p-3 rounded-4">
                                                            <div className="d-flex align-items-center mb-2 border-bottom pb-1">
                                                                <i className="bi bi-file-earmark-text text-primary me-2"></i>
                                                                <span className="small fw-bold text-dark">Course Materials</span>
                                                            </div>
                                                            <div style={{ maxHeight: '100px', overflowY: 'auto' }} className="mb-2">
                                                                {c.materials?.map(m => (
                                                                    <a key={m.id} href={m.file} target="_blank" className="d-block small text-decoration-none mb-1 text-dark">
                                                                        <i className="bi bi-download me-2 text-primary"></i>{m.title}
                                                                    </a>
                                                                ))}
                                                            </div>
                                                            <div className="d-flex gap-2">
                                                                <button className="btn btn-success btn-sm flex-grow-1 rounded-pill disabled shadow-sm">Enrolled</button>
                                                                <button className="btn btn-warning btn-sm rounded-pill shadow-sm" onClick={() => handleFeedback(c.id)}>
                                                                    <i className="bi bi-chat-left-dots text-white"></i>
                                                                </button>
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        <button className="btn btn-primary btn-sm w-100 rounded-pill shadow-sm" onClick={() => handleEnrol(c.id)}>Enrol Now</button>
                                                    )
                                                )}
                                                {user.user_type === 'teacher' && (
                                                    <button className="btn btn-outline-primary btn-sm w-100 rounded-pill" onClick={() => setPage('teacher_dashboard')}>Manage Course</button>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        );
    };

    const SearchUserPage = ({ onStartChat }) => {
        const [query, setQuery] = useState('');
        const [results, setResults] = useState([]);
        const handleSearch = async () => {
            const res = await axios.get(`/api/users/?search=${query}`);
            setResults(res.data.results || res.data);
        };
        return (
            <div className="card card-modern p-5 mt-4 animate__animated animate__fadeInUp shadow-lg">
                <h4 className="fw-bold mb-4"><i className="bi bi-people-fill me-2"></i>Find Platform Members</h4>
                <div className="input-group mb-4 shadow-sm rounded-pill overflow-hidden border">
                    <input className="form-control border-0 bg-light p-3 px-4" placeholder="Enter name or username..." onChange={e => setQuery(e.target.value)} />
                    <button className="btn btn-primary px-5" onClick={handleSearch}>Search</button>
                </div>
                <div className="list-group">
                    {results.map(u => (
                        <div key={u.id} className="list-group-item d-flex justify-content-between align-items-center mb-2 rounded-4 shadow-sm border-0 bg-light p-3">
                            <div><span className="fw-bold">{u.real_name}</span><span className="badge bg-white text-dark border ms-2 rounded-pill">{u.user_type}</span></div>
                            <button className="btn btn-success btn-sm rounded-pill px-4 shadow-sm" onClick={() => onStartChat(u)}>Message</button>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    const CreateCoursePage = () => {
        const [data, setData] = useState({ title: '', description: '' });
        const handleSubmit = (e) => {
            e.preventDefault();
            axios.post('/api/courses/', data).then(() => { alert("Course published successfully!"); setPage('home'); });
        };
        return (
            <div className="card card-modern p-5 mt-4 animate__animated animate__fadeIn">
                <h3 className="fw-bold mb-4 text-primary">Propose New Course</h3>
                <form onSubmit={handleSubmit}>
                    <div className="mb-3"><label className="form-label fw-bold">Course Title</label><input className="form-control bg-light border-0 p-3" placeholder="e.g., Python Basics" onChange={e => setData({...data, title: e.target.value})} required /></div>
                    <div className="mb-4"><label className="form-label fw-bold">Description</label><textarea className="form-control bg-light border-0 p-3" rows="4" placeholder="Briefly describe course objectives..." onChange={e => setData({...data, description: e.target.value})} required></textarea></div>
                    <button className="btn btn-primary px-5 shadow fw-bold">Submit</button>
                    <button type="button" className="btn btn-link text-muted" onClick={() => setPage('home')}>Cancel</button>
                </form>
            </div>
        );
    };

    const TeacherDashboard = () => {
        const [courses, setCourses] = useState([]);
        const [selected, setSelected] = useState(null);
        const [file, setFile] = useState(null);

        const refresh = () => axios.get('/api/courses/').then(res => setCourses(res.data.results || res.data));
        useEffect(() => { refresh(); }, []);

        const handleUpload = (e) => {
            e.preventDefault();
            const formData = new FormData();
            formData.append('course', selected.id); formData.append('file', file); formData.append('title', file.name);
            axios.post('/api/materials/', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
                 .then(() => { alert("Material uploaded and students notified!"); setFile(null); refresh(); });
        };

        return (
            <div className="row mt-4 animate__animated animate__fadeIn">
                <div className="col-md-4">
                    <h5 className="fw-bold mb-3">Managed Courses</h5>
                    {courses.map(c => (
                        <div key={c.id} onClick={() => setSelected(c)} className={`card p-3 mb-2 shadow-sm border-0 cursor-pointer ${selected?.id === c.id ? 'bg-primary text-white shadow-lg' : 'bg-white'}`} style={{cursor: 'pointer'}}>
                            <h6 className="mb-1 fw-bold">{c.title}</h6>
                            <small>{c.students?.length} Student(s) Enrolled</small>
                        </div>
                    ))}
                </div>
                <div className="col-md-8">
                    {selected ? (
                        <div className="card card-modern p-4 shadow-sm">
                            <h4 className="fw-bold text-primary mb-4">{selected.title} Management</h4>
                            <div className="row">
                                <div className="col-md-6 border-end">
                                    <h6 className="fw-bold mb-3"><i className="bi bi-chat-quote-fill me-2 text-warning"></i>Student Feedback</h6>
                                    <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                                        {selected.feedbacks?.length > 0 ? selected.feedbacks.map(f => (
                                            <div key={f.id} className="p-3 bg-light rounded-3 mb-2 shadow-sm">
                                                <div className="small fw-bold text-primary">{f.student_name}</div>
                                                <div className="small text-dark mt-1">"{f.content}"</div>
                                            </div>
                                        )) : <p className="text-muted small italic">No feedback yet</p>}
                                    </div>
                                </div>
                                <div className="col-md-6">
                                    <h6 className="fw-bold mb-3"><i className="bi bi-cloud-upload-fill me-2 text-success"></i>Upload Material</h6>
                                    <form onSubmit={handleUpload} className="d-flex flex-column gap-2">
                                        <input type="file" className="form-control form-control-sm" onChange={e => setFile(e.target.files[0])} required />
                                        <button className="btn btn-success btn-sm rounded-pill">Upload</button>
                                    </form>
                                    <hr />
                                    <h6 className="fw-bold mb-3"><i className="bi bi-people-fill me-2 text-danger"></i>Enrolled Students</h6>
                                    {selected.students_details?.map(st => (
                                        <div key={st.id} className="d-flex justify-content-between align-items-center bg-light p-2 rounded mb-1 small shadow-sm">
                                            <span>{st.real_name}</span>
                                            <button className="btn btn-link btn-sm text-danger" onClick={() => axios.post(`/api/courses/${selected.id}/remove_student/`, {student_id: st.id}).then(refresh)}>Remove</button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ) : <div className="text-center py-5 card card-modern bg-white shadow-sm">Select a course to manage from the left</div>}
                </div>
            </div>
        );
    };

    return (
        <div style={{ minHeight: '100vh' }}>
            <Navbar />
            <div className="container pb-5">
                {page === 'index' && (user ? setPage('home') : <IndexPage />)}
                {page === 'login' && <LoginPage />}
                {page === 'register' && <RegisterPage />}
                {page === 'home' && user && <HomePage />}
                {page === 'search' && <SearchUserPage onStartChat={(u) => { setSelectedRecipient(u); setPage('chat'); }} />}
                {page === 'chat' && <ChatPage user={user} onBack={() => setPage('search')} />}
                {page === 'create_course' && <CreateCoursePage />}
                {page === 'teacher_dashboard' && <TeacherDashboard />}
            </div>

            {/* Toast Notification Display */}
            {toast.show && (
                <div className="position-fixed bottom-0 end-0 p-4 animate__animated animate__slideInUp" style={{ zIndex: 9999 }}>
                    <div className="toast show bg-dark text-white border-0 shadow-lg p-3" style={{ borderRadius: '15px' }}>
                        <div className="d-flex align-items-center">
                            <i className="bi bi-lightning-fill text-warning me-3 fs-5"></i>
                            <div className="me-3">{toast.message}</div>
                            <button type="button" className="btn-close btn-close-white ms-auto" onClick={() => setToast({show:false})}></button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// Mount React root
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);