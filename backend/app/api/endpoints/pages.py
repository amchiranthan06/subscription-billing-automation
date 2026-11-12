from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/auth", tags=["Auth UI Pages (Task 3)"])

COMMON_STYLES = """
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Inter', sans-serif; }</style>
"""

@router.get("/signup", response_class=HTMLResponse, include_in_schema=False)
def signup_page():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Sign Up — BillFlow</title>
        {COMMON_STYLES}
    </head>
    <body class="bg-slate-50 min-h-screen flex items-center justify-center p-4">
        <div class="max-w-md w-full bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
            <div class="w-12 h-12 bg-purple-100 text-purple-600 rounded-xl flex items-center justify-center mx-auto mb-4 font-bold text-xl">BF</div>
            <h2 class="text-2xl font-bold text-slate-800 text-center">Create an Account</h2>
            <p class="text-slate-500 text-sm text-center mt-1">Sign up to access BillFlow Subscription Manager</p>
            
            <div id="error-msg" class="hidden mt-4 p-3 bg-red-50 border border-red-200 text-red-600 text-xs rounded-lg"></div>

            <form id="signup-form" class="mt-6 space-y-4">
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
        <title>Sign In — BillFlow</title>
        {COMMON_STYLES}
    </head>
    <body class="bg-slate-50 min-h-screen flex items-center justify-center p-4">
        <div class="max-w-md w-full bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
            <div class="w-12 h-12 bg-purple-100 text-purple-600 rounded-xl flex items-center justify-center mx-auto mb-4 font-bold text-xl">BF</div>
            <h2 class="text-2xl font-bold text-slate-800 text-center">Welcome Back</h2>
            <p class="text-slate-500 text-sm text-center mt-1">Sign in to your BillFlow account</p>
            
            <div id="error-msg" class="hidden mt-4 p-3 bg-red-50 border border-red-200 text-red-600 text-xs rounded-lg"></div>

            <form id="signin-form" class="mt-6 space-y-4">
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
        <title>Home — BillFlow</title>
        {COMMON_STYLES}
    </head>
    <body class="bg-slate-50 min-h-screen">
        <!-- Navigation Bar -->
        <nav class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-9 h-9 bg-purple-600 text-white rounded-lg flex items-center justify-center font-bold text-sm">BF</div>
                <span class="font-bold text-slate-800 text-lg">BillFlow</span>
            </div>
            <div class="flex items-center space-x-4">
                <a href="/docs" target="_blank" class="text-xs text-purple-600 font-semibold hover:underline">Open API Docs ↗</a>
                <button onclick="logout()" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition">Sign Out</button>
            </div>
        </nav>

        <!-- Main Content Container -->
        <main class="max-w-4xl mx-auto py-12 px-4">
            <div id="loading" class="text-center text-slate-500 py-12">Verifying JWT authentication...</div>

            <div id="content" class="hidden space-y-6">
                <!-- Welcome Card -->
                <div class="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
                    <div class="inline-block px-3 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded-full mb-3">
                        ✓ JWT Authenticated Session
                    </div>
                    <h1 class="text-2xl font-bold text-slate-800">Welcome, <span id="user-name">User</span>!</h1>
                    <p class="text-slate-500 text-sm mt-1">You are securely signed in using JSON Web Token (JWT) authentication.</p>
                    
                    <div class="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-slate-100">
                        <div class="p-4 bg-slate-50 rounded-xl">
                            <span class="block text-xs font-semibold text-slate-500 uppercase">User Email</span>
                            <span id="user-email" class="font-medium text-slate-800 text-sm break-all">-</span>
                        </div>
                        <div class="p-4 bg-slate-50 rounded-xl">
                            <span class="block text-xs font-semibold text-slate-500 uppercase">Account Role</span>
                            <span id="user-role" class="font-medium text-slate-800 text-sm capitalize">-</span>
                        </div>
                        <div class="p-4 bg-slate-50 rounded-xl">
                            <span class="block text-xs font-semibold text-slate-500 uppercase">Member Since</span>
                            <span id="user-created" class="font-medium text-slate-800 text-sm">-</span>
                        </div>
                    </div>
                </div>

                <!-- Next Tasks Quick Links -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                        <h3 class="font-bold text-slate-800 text-sm">📋 Interactive Swagger UI</h3>
                        <p class="text-xs text-slate-500 mt-1">Test your live API routes directly from the interactive docs.</p>
                        <a href="/docs" target="_blank" class="inline-block mt-4 text-xs font-semibold text-purple-600 hover:underline">Explore APIs →</a>
                    </div>
                    <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                        <h3 class="font-bold text-slate-800 text-sm">🔒 Token Security Details</h3>
                        <p class="text-xs text-slate-500 mt-1">Algorithm: HS256 • Stored in Browser localStorage • Valid 24 Hours</p>
                        <span class="inline-block mt-4 text-xs font-semibold text-green-600">Active & Valid</span>
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
