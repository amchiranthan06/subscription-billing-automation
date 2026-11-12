from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/auth", tags=["Auth UI Pages (Task 3)"])

COMMON_STYLES = """
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>body { font-family: 'Inter', sans-serif; }</style>
"""

@router.get("/signup", response_class=HTMLResponse, include_in_schema=False)
def signup_page():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Sign Up — Creation of Subscription Billing Automation System using Recurring Revenue Model</title>
        {COMMON_STYLES}
    </head>
    <body class="bg-slate-50 min-h-screen flex items-center justify-center p-4">
        <div class="max-w-lg w-full bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
            <div class="w-12 h-12 bg-purple-100 text-purple-600 rounded-xl flex items-center justify-center mx-auto mb-4 font-bold text-xl">BF</div>
            <h1 class="text-xl font-bold text-slate-900 text-center leading-snug">Creation of Subscription Billing Automation System using Recurring Revenue Model</h1>
            <p class="text-xs font-semibold text-purple-600 uppercase tracking-wider text-center mt-2 mb-4">User Authentication — Sign Up</p>
            
            <div id="error-msg" class="hidden mb-4 p-3 bg-red-50 border border-red-200 text-red-600 text-xs rounded-lg"></div>

            <form id="signup-form" class="space-y-4">
                <div>
                    <label class="block text-xs font-semibold text-slate-600 uppercase mb-1">Full Name</label>
                    <input type="text" id="name" required class="w-full px-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" placeholder="Jane Doe">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-600 uppercase mb-1">Email Address</label>
                    <input type="email" id="email" required class="w-full px-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" placeholder="jane@example.com">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-600 uppercase mb-1">Password</label>
                    <input type="password" id="password" minlength="6" required class="w-full px-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" placeholder="••••••••">
                </div>
                <button type="submit" class="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-2.5 rounded-lg text-sm transition">Sign Up</button>
            </form>

            <p class="text-center text-xs text-slate-500 mt-6">
                Already have an account? <a href="/auth/signin" class="text-purple-600 font-semibold hover:underline">Sign In</a>
            </p>
        </div>

        <script>
            document.getElementById('signup-form').addEventListener('submit', async (e) => {{
                e.preventDefault();
                const errDiv = document.getElementById('error-msg');
                errDiv.classList.add('hidden');
                
                const name = document.getElementById('name').value;
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;

                try {{
                    const res = await fetch('/api/v1/auth/signup', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ name, email, password }})
                    }});
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || 'Sign up failed');
                    
                    localStorage.setItem('billflow_token', data.access_token);
                    window.location.href = '/auth/home';
                }} catch (err) {{
                    errDiv.textContent = err.message;
                    errDiv.classList.remove('hidden');
                }}
            }});
        </script>
    </body>
    </html>
    """

@router.get("/signin", response_class=HTMLResponse, include_in_schema=False)
def signin_page():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Sign In — Creation of Subscription Billing Automation System using Recurring Revenue Model</title>
        {COMMON_STYLES}
    </head>
    <body class="bg-slate-50 min-h-screen flex items-center justify-center p-4">
        <div class="max-w-lg w-full bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
            <div class="w-12 h-12 bg-purple-100 text-purple-600 rounded-xl flex items-center justify-center mx-auto mb-4 font-bold text-xl">BF</div>
            <h1 class="text-xl font-bold text-slate-900 text-center leading-snug">Creation of Subscription Billing Automation System using Recurring Revenue Model</h1>
            <p class="text-xs font-semibold text-purple-600 uppercase tracking-wider text-center mt-2 mb-4">User Authentication — Sign In</p>
            
            <div id="error-msg" class="hidden mb-4 p-3 bg-red-50 border border-red-200 text-red-600 text-xs rounded-lg"></div>

            <form id="signin-form" class="space-y-4">
                <div>
                    <label class="block text-xs font-semibold text-slate-600 uppercase mb-1">Email Address</label>
                    <input type="email" id="email" required class="w-full px-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" placeholder="jane@example.com">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-600 uppercase mb-1">Password</label>
                    <input type="password" id="password" required class="w-full px-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" placeholder="••••••••">
                </div>
                <button type="submit" class="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-2.5 rounded-lg text-sm transition">Sign In</button>
            </form>

            <p class="text-center text-xs text-slate-500 mt-6">
                Don't have an account? <a href="/auth/signup" class="text-purple-600 font-semibold hover:underline">Sign Up</a>
            </p>
        </div>

        <script>
            document.getElementById('signin-form').addEventListener('submit', async (e) => {{
                e.preventDefault();
                const errDiv = document.getElementById('error-msg');
                errDiv.classList.add('hidden');
                
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;

                try {{
                    const res = await fetch('/api/v1/auth/signin', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ email, password }})
                    }});
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || 'Sign in failed');
                    
                    localStorage.setItem('billflow_token', data.access_token);
                    window.location.href = '/auth/home';
                }} catch (err) {{
                    errDiv.textContent = err.message;
                    errDiv.classList.remove('hidden');
                }}
            }});
        </script>
    </body>
    </html>
    """

@router.get("/home", response_class=HTMLResponse, include_in_schema=False)
def home_page():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>User Profile — Creation of Subscription Billing Automation System using Recurring Revenue Model</title>
        {COMMON_STYLES}
    </head>
    <body class="bg-slate-50 min-h-screen">
        <!-- Navigation Bar -->
        <nav class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-9 h-9 bg-purple-600 text-white rounded-lg flex items-center justify-center font-bold text-sm">BF</div>
                <span class="font-bold text-slate-900 text-sm md:text-base">Creation of Subscription Billing Automation System using Recurring Revenue Model</span>
            </div>
            <button onclick="logout()" class="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg transition">Sign Out</button>
        </nav>

        <!-- Main Content Container: ONLY User Authentication Profile -->
        <main class="max-w-2xl mx-auto py-12 px-4">
            <div id="loading" class="text-center text-slate-500 py-12">Verifying JWT authentication...</div>

            <div id="content" class="hidden space-y-6">
                <!-- User Profile Card -->
                <div class="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
                    <div class="w-12 h-12 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto mb-4 font-bold text-xl">✓</div>
                    <div class="text-center mb-6">
                        <span class="inline-block px-3 py-1 bg-emerald-50 text-emerald-700 text-xs font-semibold rounded-full border border-emerald-200 mb-2">
                            JWT Authenticated Session
                        </span>
                        <h1 class="text-2xl font-bold text-slate-800">Welcome, <span id="user-name">User</span>!</h1>
                        <p class="text-slate-500 text-xs mt-1">Authenticated user details:</p>
                    </div>
                    
                    <div class="space-y-3 pt-4 border-t border-slate-100 text-sm">
                        <div class="flex justify-between items-center p-3 bg-slate-50 rounded-xl">
                            <span class="text-slate-500 font-medium">User Email</span>
                            <span id="user-email" class="font-semibold text-slate-800 break-all">-</span>
                        </div>
                        <div class="flex justify-between items-center p-3 bg-slate-50 rounded-xl">
                            <span class="text-slate-500 font-medium">Account Role</span>
                            <span id="user-role" class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-100 text-purple-700 uppercase">-</span>
                        </div>
                        <div class="flex justify-between items-center p-3 bg-slate-50 rounded-xl">
                            <span class="text-slate-500 font-medium">Account Created</span>
                            <span id="user-created" class="font-semibold text-slate-800">-</span>
                        </div>
                    </div>
                </div>
            </div>
        </main>

        <script>
            async function checkAuth() {{
                const token = localStorage.getItem('billflow_token');
                if (!token) {{
                    window.location.href = '/auth/signin';
                    return;
                }}

                try {{
                    const res = await fetch('/api/v1/auth/me', {{
                        headers: {{ 'Authorization': 'Bearer ' + token }}
                    }});
                    if (!res.ok) throw new Error('Token expired or invalid');
                    const user = await res.json();
                    
                    document.getElementById('user-name').textContent = user.name;
                    document.getElementById('user-email').textContent = user.email;
                    document.getElementById('user-role').textContent = user.role;
                    document.getElementById('user-created').textContent = new Date(user.created_at).toLocaleDateString();

                    document.getElementById('loading').classList.add('hidden');
                    document.getElementById('content').classList.remove('hidden');
                }} catch (err) {{
                    localStorage.removeItem('billflow_token');
                    window.location.href = '/auth/signin';
                }}
            }}

            function logout() {{
                localStorage.removeItem('billflow_token');
                window.location.href = '/auth/signin';
            }}

            checkAuth();
        </script>
    </body>
    </html>
    """
