from flask import Flask, request, jsonify, render_template_string
import sqlite3
import os
import subprocess



@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                priority TEXT CHECK(priority IN ('high', 'medium', 'low')) NOT NULL,
                completed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()
        
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Drop and recreate to ensure correct schema (safe for demo)
        cursor.execute('DROP TABLE IF EXISTS tasks')
        cursor.execute('''
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                priority TEXT CHECK(priority IN ('high', 'medium', 'low')) NOT NULL,
                completed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()

# Initialize database on startup
init_db()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>TaskFlow – Priority Manager</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet" />
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #0F172A;
            color: #F8FAFC;
            min-height: 100vh;
            transition: background 0.3s, color 0.3s;
        }
        .font-space { font-family: 'Space Grotesk', sans-serif; }
        .glass {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        .glass-light {
            background: rgba(255, 255, 255, 0.6);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
        }
        .hero-gradient {
            background: radial-gradient(ellipse at 50% 0%, #6366F1 0%, transparent 70%),
                        radial-gradient(ellipse at 0% 50%, #22C55E 0%, transparent 50%),
                        radial-gradient(ellipse at 100% 50%, #F59E0B 0%, transparent 50%),
                        #0F172A;
            background-blend-mode: overlay, normal, normal, normal;
            background-size: 200% 200%;
            animation: gradientShift 10s ease infinite;
        }
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .task-card {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: default;
        }
        .task-card:hover {
            transform: translateY(-4px) scale(1.01);
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        }
        .task-card.completed {
            opacity: 0.5;
            text-decoration: line-through;
        }
        .task-card.completed .task-title {
            text-decoration: line-through;
        }
        .priority-high { border-left: 4px solid #EF4444; box-shadow: 0 0 15px rgba(239, 68, 68, 0.2); }
        .priority-medium { border-left: 4px solid #F59E0B; box-shadow: 0 0 15px rgba(245, 158, 11, 0.2); }
        .priority-low { border-left: 4px solid #22C55E; box-shadow: 0 0 15px rgba(34, 197, 94, 0.2); }
        .badge-high { background: #EF4444; color: white; }
        .badge-medium { background: #F59E0B; color: #0F172A; }
        .badge-low { background: #22C55E; color: #0F172A; }

        .fade-in {
            animation: fadeIn 0.5s ease forwards;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .slide-up {
            animation: slideUp 0.4s ease forwards;
        }
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(30px) scale(0.95); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        .toast {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            z-index: 1000;
            padding: 1rem 1.5rem;
            border-radius: 1rem;
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.2);
            color: #F8FAFC;
            font-weight: 500;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .toast.show {
            transform: translateY(0);
            opacity: 1;
        }
        .toast.success { border-left: 4px solid #22C55E; }
        .toast.error { border-left: 4px solid #EF4444; }
        .toast.info { border-left: 4px solid #6366F1; }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #1E293B; }
        ::-webkit-scrollbar-thumb { background: #6366F1; border-radius: 10px; }

        /* Dark mode toggle icon */
        .dark-mode-toggle {
            cursor: pointer;
            transition: transform 0.3s;
        }
        .dark-mode-toggle:hover { transform: rotate(30deg); }

        /* Mobile responsive */
        @media (max-width: 640px) {
            .hero-heading { font-size: 2.5rem; line-height: 1.2; }
            .stats-grid { grid-template-columns: 1fr 1fr; }
        }

        /* Button styles */
        .btn-primary {
            background: #6366F1;
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 1rem;
            font-weight: 600;
            transition: all 0.3s;
            border: none;
            cursor: pointer;
        }
        .btn-primary:hover {
            background: #4F46E5;
            transform: scale(1.02);
            box-shadow: 0 10px 25px rgba(99, 102, 241, 0.4);
        }
        .btn-primary:active { transform: scale(0.98); }

        .btn-icon {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 50%;
            width: 2.5rem;
            height: 2.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            cursor: pointer;
            color: #F8FAFC;
        }
        .btn-icon:hover {
            background: rgba(255,255,255,0.15);
            transform: scale(1.05);
        }
        .btn-icon.delete:hover { background: rgba(239, 68, 68, 0.3); border-color: #EF4444; }
        .btn-icon.complete:hover { background: rgba(34, 197, 94, 0.3); border-color: #22C55E; }

        /* Select styling */
        select, input[type="text"] {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 1rem;
            padding: 0.75rem 1rem;
            color: #F8FAFC;
            font-weight: 400;
            transition: all 0.3s;
            outline: none;
        }
        select:focus, input[type="text"]:focus {
            border-color: #6366F1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.3);
        }
        select option { background: #1E293B; }

        /* Light mode overrides */
        html:not(.dark) body {
            background: #F8FAFC;
            color: #0F172A;
        }
        html:not(.dark) .glass {
            background: rgba(255,255,255,0.7);
            border: 1px solid rgba(255,255,255,0.5);
            box-shadow: 0 8px 32px rgba(0,0,0,0.05);
        }
        html:not(.dark) .hero-gradient {
            background: radial-gradient(ellipse at 50% 0%, #6366F1 0%, transparent 70%),
                        radial-gradient(ellipse at 0% 50%, #22C55E 0%, transparent 50%),
                        radial-gradient(ellipse at 100% 50%, #F59E0B 0%, transparent 50%),
                        #F8FAFC;
        }
        html:not(.dark) select,
        html:not(.dark) input[type="text"] {
            background: rgba(0,0,0,0.03);
            border: 1px solid rgba(0,0,0,0.1);
            color: #0F172A;
        }
        html:not(.dark) select option { background: #F8FAFC; }
        html:not(.dark) .btn-icon {
            color: #0F172A;
            background: rgba(0,0,0,0.03);
            border-color: rgba(0,0,0,0.08);
        }
        html:not(.dark) .btn-icon:hover {
            background: rgba(0,0,0,0.08);
        }
        html:not(.dark) .task-card {
            background: white;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        }
        html:not(.dark) .task-card:hover {
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        html:not(.dark) .toast {
            background: rgba(255,255,255,0.9);
            color: #0F172A;
            border: 1px solid rgba(0,0,0,0.1);
        }
        html:not(.dark) .stat-card {
            background: white;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        }
        html:not(.dark) .stat-card:hover {
            box-shadow: 0 20px 40px rgba(0,0,0,0.08);
        }
        html:not(.dark) .glass-light {
            background: rgba(255,255,255,0.8);
            border: 1px solid rgba(255,255,255,0.5);
        }
    </style>
</head>
<body>

    <!-- Toast Container -->
    <div id="toast" class="toast"></div>

    <!-- Navbar -->
    <nav class="fixed top-0 left-0 w-full z-50 glass py-3 px-6 md:px-12 flex items-center justify-between backdrop-blur-xl">
        <div class="flex items-center space-x-2">
            <span class="text-2xl font-space font-bold bg-gradient-to-r from-indigo-400 to-emerald-400 bg-clip-text text-transparent">TaskFlow</span>
        </div>
        <div class="flex items-center space-x-4">
            <button id="darkModeToggle" class="btn-icon dark-mode-toggle" aria-label="Toggle dark mode">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0112 21.75 9.75 9.75 0 0112 2.25a9.718 9.718 0 019.752 6.752" />
                </svg>
            </button>
            <div class="btn-icon">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                </svg>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero-gradient pt-28 pb-16 px-4 md:px-12 text-center relative overflow-hidden">
        <div class="max-w-4xl mx-auto relative z-10">
            <h1 class="hero-heading text-5xl md:text-7xl font-space font-bold leading-tight mb-4 bg-clip-text text-transparent bg-gradient-to-r from-indigo-300 via-purple-300 to-emerald-300">
                Focus On What Matters
            </h1>
            <p class="text-lg md:text-xl text-slate-300 dark:text-slate-300 max-w-2xl mx-auto font-light">
                Organize, prioritize, and complete your most important work.
            </p>
        </div>
        <!-- Animated blobs -->
        <div class="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
            <div class="absolute -top-20 -left-20 w-64 h-64 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
            <div class="absolute -bottom-20 -right-20 w-64 h-64 bg-emerald-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse delay-1000"></div>
        </div>
    </section>

    <!-- Main Content -->
    <main class="max-w-5xl mx-auto px-4 md:px-8 py-8 -mt-8 relative z-20">
        <!-- Task Input -->
        <div class="glass rounded-3xl p-6 md:p-8 mb-10 slide-up">
            <form id="taskForm" class="flex flex-col md:flex-row gap-4 items-end">
                <div class="flex-1 w-full">
                    <label for="taskInput" class="block text-sm font-medium text-slate-300 dark:text-slate-300 mb-1">Task Title</label>
                    <input type="text" id="taskInput" placeholder="Write a new task..." class="w-full bg-transparent border border-white/10 rounded-2xl px-4 py-3 text-base focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/30 transition" />
                </div>
                <div class="w-full md:w-48">
                    <label for="prioritySelect" class="block text-sm font-medium text-slate-300 dark:text-slate-300 mb-1">Priority</label>
                    <select id="prioritySelect" class="w-full bg-transparent border border-white/10 rounded-2xl px-4 py-3 text-base focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/30 transition">
                        <option value="high">🔴 High</option>
                        <option value="medium" selected>🟡 Medium</option>
                        <option value="low">🟢 Low</option>
                    </select>
                </div>
                <button type="submit" class="btn-primary w-full md:w-auto px-8 py-3 rounded-2xl flex items-center justify-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                    </svg>
                    Add Task
                </button>
            </form>
        </div>

        <!-- Stats -->
        <div class="stats-grid grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
            <div class="glass rounded-2xl p-5 text-center stat-card transition hover:scale-105">
                <div class="text-3xl font-bold text-indigo-400" id="totalTasks">0</div>
                <div class="text-sm text-slate-300 dark:text-slate-300 mt-1">Total</div>
            </div>
            <div class="glass rounded-2xl p-5 text-center stat-card transition hover:scale-105">
                <div class="text-3xl font-bold text-emerald-400" id="completedTasks">0</div>
                <div class="text-sm text-slate-300 dark:text-slate-300 mt-1">Completed</div>
            </div>
            <div class="glass rounded-2xl p-5 text-center stat-card transition hover:scale-105">
                <div class="text-3xl font-bold text-amber-400" id="pendingTasks">0</div>
                <div class="text-sm text-slate-300 dark:text-slate-300 mt-1">Pending</div>
            </div>
            <div class="glass rounded-2xl p-5 text-center stat-card transition hover:scale-105">
                <div class="text-3xl font-bold text-cyan-400" id="completionRate">0%</div>
                <div class="text-sm text-slate-300 dark:text-slate-300 mt-1">Completion Rate</div>
            </div>
        </div>

        <!-- Filters & Search -->
        <div class="flex flex-col md:flex-row gap-4 mb-6 items-start md:items-center">
            <div class="flex-1 w-full">
                <input type="text" id="searchInput" placeholder="Search tasks..." class="w-full bg-transparent border border-white/10 rounded-2xl px-4 py-2.5 text-sm focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/30 transition" />
            </div>
            <div class="flex flex-wrap gap-3 items-center">
                <select id="filterPriority" class="bg-transparent border border-white/10 rounded-2xl px-3 py-2 text-sm focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/30 transition">
                    <option value="all">All Priorities</option>
                    <option value="high">🔴 High</option>
                    <option value="medium">🟡 Medium</option>
                    <option value="low">🟢 Low</option>
                </select>
                <select id="sortBy" class="bg-transparent border border-white/10 rounded-2xl px-3 py-2 text-sm focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/30 transition">
                    <option value="created_at_desc">Newest First</option>
                    <option value="created_at_asc">Oldest First</option>
                    <option value="priority_high">Priority (High → Low)</option>
                    <option value="priority_low">Priority (Low → High)</option>
                </select>
            </div>
        </div>

        <!-- Task List -->
        <div id="taskList" class="space-y-3">
            {% if tasks %}
                {% for task in tasks %}
                    <div class="task-card glass rounded-2xl p-5 flex flex-wrap items-center justify-between gap-3 priority-{{ task.priority }} fade-in" data-id="{{ task.id }}" data-completed="{{ task.completed }}" data-priority="{{ task.priority }}" data-title="{{ task.title }}">
                        <div class="flex items-center gap-4 flex-1 min-w-[200px]">
                            <button class="complete-btn btn-icon complete transition" data-id="{{ task.id }}">
                                {% if task.completed %}
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5 text-emerald-400">
                                        <path fill-rule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm13.36-1.814a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z" clip-rule="evenodd" />
                                    </svg>
                                {% else %}
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                                        <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                                    </svg>
                                {% endif %}
                            </button>
                            <div>
                                <div class="task-title text-base font-medium {% if task.completed %}line-through opacity-50{% endif %}">{{ task.title }}</div>
                                <div class="flex items-center gap-2 mt-0.5">
                                    <span class="text-xs px-2.5 py-0.5 rounded-full badge-{{ task.priority }} font-medium">
                                        {{ task.priority|capitalize }}
                                    </span>
                                    <span class="text-xs text-slate-400">{{ task.created_at[:10] }}</span>
                                </div>
                            </div>
                        </div>
                        <button class="delete-btn btn-icon delete transition" data-id="{{ task.id }}">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                            </svg>
                        </button>
                    </div>
                {% endfor %}
            {% else %}
                <div id="emptyState" class="glass rounded-3xl p-12 text-center">
                    <div class="text-6xl mb-4">📋</div>
                    <h3 class="text-2xl font-space font-semibold">No Tasks Yet</h3>
                    <p class="text-slate-400 dark:text-slate-400 mt-2">Start by creating your first priority.</p>
                </div>
            {% endif %}
        </div>
    </main>

    <script>
        // ----- DOM refs -----
        const taskForm = document.getElementById('taskForm');
        const taskInput = document.getElementById('taskInput');
        const prioritySelect = document.getElementById('prioritySelect');
        const taskList = document.getElementById('taskList');
        const searchInput = document.getElementById('searchInput');
        const filterPriority = document.getElementById('filterPriority');
        const sortBy = document.getElementById('sortBy');
        const totalEl = document.getElementById('totalTasks');
        const completedEl = document.getElementById('completedTasks');
        const pendingEl = document.getElementById('pendingTasks');
        const completionEl = document.getElementById('completionRate');
        const darkToggle = document.getElementById('darkModeToggle');
        const toast = document.getElementById('toast');

        let toastTimer = null;

        // ----- Toast -----
        function showToast(message, type = 'info') {
            if (toastTimer) clearTimeout(toastTimer);
            toast.textContent = message;
            toast.className = `toast ${type}`;
            // Force reflow
            void toast.offsetWidth;
            toast.classList.add('show');
            toastTimer = setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }

        // ----- Dark Mode -----
        function setDarkMode(isDark) {
            const html = document.documentElement;
            if (isDark) {
                html.classList.add('dark');
                localStorage.setItem('darkMode', 'true');
            } else {
                html.classList.remove('dark');
                localStorage.setItem('darkMode', 'false');
            }
        }
        // Load saved
        if (localStorage.getItem('darkMode') === 'false') {
            setDarkMode(false);
        } else {
            setDarkMode(true);
        }
        darkToggle.addEventListener('click', () => {
            const isDark = document.documentElement.classList.contains('dark');
            setDarkMode(!isDark);
        });

        // ----- API helpers -----
        async function addTask(title, priority) {
            const res = await fetch('/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, priority })
            });
            return res.json();
        }

        async function toggleTask(id) {
            const res = await fetch(`/toggle/${id}`, { method: 'POST' });
            return res.json();
        }

        async function deleteTask(id) {
            const res = await fetch(`/delete/${id}`, { method: 'POST' });
            return res.json();
        }

        // ----- Render tasks from data -----
        function renderTasks(tasks) {
            if (!tasks || tasks.length === 0) {
                taskList.innerHTML = `
                    <div class="glass rounded-3xl p-12 text-center">
                        <div class="text-6xl mb-4">📋</div>
                        <h3 class="text-2xl font-space font-semibold">No Tasks Yet</h3>
                        <p class="text-slate-400 dark:text-slate-400 mt-2">Start by creating your first priority.</p>
                    </div>
                `;
                updateStats([]);
                return;
            }

            let html = '';
            tasks.forEach(task => {
                const completedClass = task.completed ? 'completed' : '';
                const priorityClass = `priority-${task.priority}`;
                const badgeClass = `badge-${task.priority}`;
                const checkedIcon = task.completed ?
                    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5 text-emerald-400">
                        <path fill-rule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm13.36-1.814a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z" clip-rule="evenodd" />
                    </svg>` :
                    `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>`;

                html += `
                    <div class="task-card glass rounded-2xl p-5 flex flex-wrap items-center justify-between gap-3 ${priorityClass} ${completedClass} fade-in" data-id="${task.id}" data-completed="${task.completed}" data-priority="${task.priority}" data-title="${task.title}">
                        <div class="flex items-center gap-4 flex-1 min-w-[200px]">
                            <button class="complete-btn btn-icon complete transition" data-id="${task.id}">
                                ${checkedIcon}
                            </button>
                            <div>
                                <div class="task-title text-base font-medium ${task.completed ? 'line-through opacity-50' : ''}">${task.title}</div>
                                <div class="flex items-center gap-2 mt-0.5">
                                    <span class="text-xs px-2.5 py-0.5 rounded-full ${badgeClass} font-medium">
                                        ${task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}
                                    </span>
                                    <span class="text-xs text-slate-400">${task.created_at ? task.created_at.slice(0,10) : ''}</span>
                                </div>
                            </div>
                        </div>
                        <button class="delete-btn btn-icon delete transition" data-id="${task.id}">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                            </svg>
                        </button>
                    </div>
                `;
            });
            taskList.innerHTML = html;
            updateStats(tasks);
            // Re-bind events
            bindTaskEvents();
        }

        // ----- Update stats -----
        function updateStats(tasks) {
            const total = tasks.length;
            const completed = tasks.filter(t => t.completed).length;
            const pending = total - completed;
            const rate = total === 0 ? 0 : Math.round((completed / total) * 100);
            totalEl.textContent = total;
            completedEl.textContent = completed;
            pendingEl.textContent = pending;
            completionEl.textContent = rate + '%';
        }

        // ----- Filter & Sort -----
        function getFilteredAndSortedTasks() {
            // Get all task elements
            const taskElements = document.querySelectorAll('.task-card');
            let tasks = [];
            taskElements.forEach(el => {
                tasks.push({
                    id: parseInt(el.dataset.id),
                    title: el.dataset.title,
                    priority: el.dataset.priority,
                    completed: el.dataset.completed === 'true',
                    created_at: el.querySelector('.text-slate-400') ? el.querySelector('.text-slate-400').textContent : '',
                    element: el
                });
            });

            // Filter by search
            const search = searchInput.value.toLowerCase().trim();
            if (search) {
                tasks = tasks.filter(t => t.title.toLowerCase().includes(search));
            }

            // Filter by priority
            const priority = filterPriority.value;
            if (priority !== 'all') {
                tasks = tasks.filter(t => t.priority === priority);
            }

            // Sort
            const sort = sortBy.value;
            if (sort === 'created_at_desc') {
                tasks.sort((a, b) => b.created_at.localeCompare(a.created_at));
            } else if (sort === 'created_at_asc') {
                tasks.sort((a, b) => a.created_at.localeCompare(b.created_at));
            } else if (sort === 'priority_high') {
                const order = { high: 0, medium: 1, low: 2 };
                tasks.sort((a, b) => order[a.priority] - order[b.priority]);
            } else if (sort === 'priority_low') {
                const order = { high: 0, medium: 1, low: 2 };
                tasks.sort((a, b) => order[b.priority] - order[a.priority]);
            }

            return tasks;
        }

        function applyFiltersAndSort() {
            const tasks = getFilteredAndSortedTasks();
            // Show/hide elements
            const allElements = document.querySelectorAll('.task-card');
            allElements.forEach(el => el.style.display = 'none');
            tasks.forEach(t => t.element.style.display = 'flex');
            // Update stats based on visible tasks? Actually stats should be based on all tasks, not filtered.
            // We'll keep stats based on all tasks (already updated on render). So no change.
            // But we might want to show "no tasks" if filtered result empty.
            const visible = tasks.length;
            const emptyState = document.getElementById('emptyState');
            if (visible === 0 && allElements.length > 0) {
                // We have tasks but none visible, show a message
                const msg = document.createElement('div');
                msg.id = 'filterEmpty';
                msg.className = 'glass rounded-3xl p-12 text-center';
                msg.innerHTML = `<p class="text-slate-400 dark:text-slate-400">No tasks match your filters.</p>`;
                // Remove existing if any
                const old = document.getElementById('filterEmpty');
                if (old) old.remove();
                taskList.appendChild(msg);
            } else {
                const old = document.getElementById('filterEmpty');
                if (old) old.remove();
            }
        }

        // ----- Bind events on task buttons -----
        function bindTaskEvents() {
            document.querySelectorAll('.complete-btn').forEach(btn => {
                btn.addEventListener('click', async function(e) {
                    e.stopPropagation();
                    const id = parseInt(this.dataset.id);
                    try {
                        const result = await toggleTask(id);
                        if (result.success) {
                            // Update UI: toggle completed class and icon
                            const card = this.closest('.task-card');
                            const isCompleted = result.completed;
                            card.dataset.completed = isCompleted;
                            card.classList.toggle('completed', isCompleted);
                            const titleDiv = card.querySelector('.task-title');
                            titleDiv.classList.toggle('line-through', isCompleted);
                            titleDiv.classList.toggle('opacity-50', isCompleted);
                            // Update icon
                            this.innerHTML = isCompleted ?
                                `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5 text-emerald-400">
                                    <path fill-rule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm13.36-1.814a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z" clip-rule="evenodd" />
                                </svg>` :
                                `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                                </svg>`;
                            // Update stats
                            const allTasks = getFilteredAndSortedTasks(); // but we need all tasks, not filtered
                            // Better: fetch all tasks from server or maintain a list.
                            // We'll re-fetch all tasks from the server to keep stats consistent.
                            await refreshTasks();
                            showToast('Task updated!', 'success');
                        }
                    } catch (err) {
                        showToast('Error updating task.', 'error');
                    }
                });
            });

            document.querySelectorAll('.delete-btn').forEach(btn => {
                btn.addEventListener('click', async function(e) {
                    e.stopPropagation();
                    const id = parseInt(this.dataset.id);
                    if (!confirm('Delete this task?')) return;
                    try {
                        const result = await deleteTask(id);
                        if (result.success) {
                            const card = this.closest('.task-card');
                            card.style.transition = 'all 0.3s';
                            card.style.transform = 'scale(0.8)';
                            card.style.opacity = '0';
                            setTimeout(() => {
                                card.remove();
                                // Refresh stats and reapply filters
                                refreshTasks();
                            }, 300);
                            showToast('Task deleted.', 'info');
                        }
                    } catch (err) {
                        showToast('Error deleting task.', 'error');
                    }
                });
            });
        }

        // ----- Refresh tasks from server -----
        async function refreshTasks() {
            try {
                const res = await fetch('/tasks');
                const data = await res.json();
                if (data.success) {
                    renderTasks(data.tasks);
                    // Reapply filters after render
                    applyFiltersAndSort();
                }
            } catch (err) {
                console.error(err);
            }
        }

        // ----- Add task form -----
        taskForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const title = taskInput.value.trim();
            if (!title) {
                showToast('Please enter a task title.', 'error');
                return;
            }
            const priority = prioritySelect.value;
            try {
                const result = await addTask(title, priority);
                if (result.success) {
                    taskInput.value = '';
                    showToast('Task added!', 'success');
                    await refreshTasks();
                } else {
                    showToast('Error adding task.', 'error');
                }
            } catch (err) {
                showToast('Error adding task.', 'error');
            }
        });

        // Keyboard shortcut: Ctrl+Enter to submit
        taskInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && e.ctrlKey) {
                taskForm.dispatchEvent(new Event('submit'));
            }
        });

        // ----- Filters change -----
        searchInput.addEventListener('input', applyFiltersAndSort);
        filterPriority.addEventListener('change', applyFiltersAndSort);
        sortBy.addEventListener('change', applyFiltersAndSort);

        // ----- Init -----
        // On load, bind events and apply filters
        document.addEventListener('DOMContentLoaded', function() {
            bindTaskEvents();
            applyFiltersAndSort();
            // Initial stats are already set via renderTasks from server-side rendering.
            // But if we have tasks from server, we need to update stats.
            // The server rendered tasks, so stats are updated.
        });

        // Also refresh tasks every minute to sync with other clients (optional)
        // setInterval(refreshTasks, 60000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
    tasks = cursor.fetchall()
    tasks_list = [dict(row) for row in tasks]
    return render_template_string(HTML_TEMPLATE, tasks=tasks_list)

@app.route('/add', methods=['POST'])
def add_task():
    data = request.get_json()
    title = data.get('title', '').strip()
    priority = data.get('priority', 'medium')
    if not title:
        return jsonify({'success': False, 'error': 'Title is required'})
    if priority not in ['high', 'medium', 'low']:
        priority = 'medium'
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'INSERT INTO tasks (title, priority) VALUES (?, ?)',
        (title, priority)
    )
    db.commit()
    return jsonify({'success': True, 'id': cursor.lastrowid})

@app.route('/toggle/<int:task_id>', methods=['POST'])
def toggle_task(task_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT completed FROM tasks WHERE id = ?', (task_id,))
    row = cursor.fetchone()
    if not row:
        return jsonify({'success': False, 'error': 'Task not found'})
    new_status = 1 if row['completed'] == 0 else 0
    cursor.execute(
        'UPDATE tasks SET completed = ? WHERE id = ?',
        (new_status, task_id)
    )
    db.commit()
    return jsonify({'success': True, 'completed': bool(new_status)})

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    db.commit()
    if cursor.rowcount == 0:
        return jsonify({'success': False, 'error': 'Task not found'})
    return jsonify({'success': True})

@app.route('/tasks')
def get_tasks():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
    tasks = cursor.fetchall()
    tasks_list = [dict(row) for row in tasks]
    return jsonify({'success': True, 'tasks': tasks_list})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
