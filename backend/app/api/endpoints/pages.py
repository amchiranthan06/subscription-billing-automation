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
        <title>Dashboard — Creation of Subscription Billing Automation System using Recurring Revenue Model</title>
        {COMMON_STYLES}
    </head>
    <body class="bg-slate-50 min-h-screen flex flex-col">
        <!-- Navigation Top Bar -->
        <nav class="bg-white border-b border-slate-200 px-6 py-3.5 flex items-center justify-between sticky top-0 z-30">
            <div class="flex items-center space-x-3">
                <div class="w-9 h-9 bg-purple-600 text-white rounded-xl flex items-center justify-center font-bold text-sm shadow-sm">BF</div>
                <div>
                    <span class="font-bold text-slate-900 text-sm md:text-base block leading-tight">BillFlow Billing Automation</span>
                    <span class="text-[11px] text-slate-500 hidden md:block">Creation of Subscription Billing Automation System using Recurring Revenue Model</span>
                </div>
            </div>
            <div class="flex items-center space-x-3">
                <span id="nav-user-badge" class="text-xs bg-slate-100 text-slate-700 px-3 py-1.5 rounded-lg font-medium border border-slate-200">Checking session...</span>
                <button onclick="logout()" class="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg transition shadow-sm">Sign Out</button>
            </div>
        </nav>

        <div class="flex flex-1">
            <!-- SIDEBAR -->
            <aside class="w-64 bg-white border-r border-slate-200 p-4 space-y-2 flex-shrink-0">
                <div class="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-3 py-1">Menu</div>
                
                <button id="nav-tab-profile" onclick="switchTab('profile')" class="w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-purple-600 bg-purple-50 transition text-left">
                    <span class="text-base">👤</span>
                    <span>User Profile</span>
                </button>

                <button id="nav-tab-invoices" onclick="switchTab('invoices')" class="w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition text-left">
                    <span class="text-base">📄</span>
                    <span>Invoices (M2-T1)</span>
                </button>
                
                <div class="pt-6 mt-6 border-t border-slate-100">
                    <div class="p-3 bg-purple-50/50 rounded-xl border border-purple-100 text-xs text-purple-800">
                        <div class="font-bold mb-1">Milestone 2 Active</div>
                        <div class="text-[11px] text-purple-600">Task 1: Automated Invoice Generation with PDF export & filters.</div>
                    </div>
                </div>
            </aside>

            <!-- MAIN CONTENT AREA -->
            <main class="flex-1 p-6 md:p-8 max-w-7xl">
                <div id="loading" class="text-center text-slate-500 py-12">Verifying JWT authentication...</div>

                <!-- 1. PROFILE SECTION -->
                <section id="section-profile" class="hidden space-y-6 max-w-2xl mx-auto">
                    <div class="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
                        <div class="w-12 h-12 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto mb-4 font-bold text-xl">✓</div>
                        <div class="text-center mb-6">
                            <span class="inline-block px-3 py-1 bg-emerald-50 text-emerald-700 text-xs font-semibold rounded-full border border-emerald-200 mb-2">
                                JWT Authenticated Session
                            </span>
                            <h1 class="text-2xl font-bold text-slate-800">Welcome, <span id="user-name">User</span>!</h1>
                            <p class="text-slate-500 text-xs mt-1">Authenticated user credentials:</p>
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
                </section>

                <!-- 2. INVOICES SECTION (Milestone 2 - Task 1) -->
                <section id="section-invoices" class="hidden space-y-6">
                    <!-- Page Header & Action -->
                    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                        <div>
                            <h1 class="text-xl sm:text-2xl font-bold text-slate-900">Invoices & Billing</h1>
                            <p class="text-xs sm:text-sm text-slate-500 mt-0.5">Automated recurring billing invoices, line items, and PDF statements.</p>
                        </div>
                        <button onclick="openGenerateModal()" class="inline-flex items-center space-x-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold rounded-xl shadow-sm transition">
                            <span>+</span>
                            <span>Generate Invoice</span>
                        </button>
                    </div>

                    <!-- Filter Controls -->
                    <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                        <div>
                            <label class="block text-[11px] font-semibold text-slate-600 uppercase mb-1">Search Invoice</label>
                            <input type="text" id="inv-search" oninput="loadInvoices()" placeholder="e.g. INV-202611, Customer..." class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-purple-500">
                        </div>
                        <div>
                            <label class="block text-[11px] font-semibold text-slate-600 uppercase mb-1">Status Filter</label>
                            <select id="inv-status" onchange="loadInvoices()" class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-purple-500 bg-white">
                                <option value="">All Statuses (Paid & Unpaid)</option>
                                <option value="unpaid">Unpaid</option>
                                <option value="paid">Paid</option>
                                <option value="draft">Draft</option>
                                <option value="void">Void</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-[11px] font-semibold text-slate-600 uppercase mb-1">Start Date</label>
                            <input type="date" id="inv-start-date" onchange="loadInvoices()" class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-purple-500">
                        </div>
                        <div>
                            <label class="block text-[11px] font-semibold text-slate-600 uppercase mb-1">End Date</label>
                            <input type="date" id="inv-end-date" onchange="loadInvoices()" class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-purple-500">
                        </div>
                    </div>

                    <!-- Invoices Table -->
                    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs">
                                <thead class="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                                    <tr>
                                        <th class="px-4 py-3.5">Invoice #</th>
                                        <th class="px-4 py-3.5">Customer</th>
                                        <th class="px-4 py-3.5">Plan</th>
                                        <th class="px-4 py-3.5">Date</th>
                                        <th class="px-4 py-3.5">Subtotal</th>
                                        <th class="px-4 py-3.5">Tax (10%)</th>
                                        <th class="px-4 py-3.5">Total</th>
                                        <th class="px-4 py-3.5">Status</th>
                                        <th class="px-4 py-3.5 text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="invoices-tbody" class="divide-y divide-slate-100 text-slate-700">
                                    <tr>
                                        <td colspan="9" class="px-4 py-8 text-center text-slate-400">Loading invoices...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </section>
            </main>
        </div>

        <!-- GENERATE INVOICE MODAL -->
        <div id="generate-modal" class="hidden fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
                <div class="flex justify-between items-center">
                    <h3 class="font-bold text-slate-900 text-base">Generate New Invoice</h3>
                    <button onclick="closeGenerateModal()" class="text-slate-400 hover:text-slate-600 text-lg">&times;</button>
                </div>
                <div id="gen-modal-error" class="hidden p-2.5 bg-red-50 text-red-600 text-xs rounded-xl border border-red-200"></div>
                <form id="generate-invoice-form" onsubmit="handleGenerateInvoice(event)" class="space-y-3">
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Select Active Subscription</label>
                        <select id="gen-sub-id" required class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-purple-500 bg-white">
                            <option value="">Loading subscriptions...</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Tax Rate (Default 0.10 for 10%)</label>
                        <input type="number" step="0.01" min="0" max="1" id="gen-tax-rate" value="0.10" class="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-purple-500">
                    </div>
                    <div class="flex justify-end space-x-2 pt-2">
                        <button type="button" onclick="closeGenerateModal()" class="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition">Cancel</button>
                        <button type="submit" class="px-4 py-2 text-xs font-semibold bg-purple-600 hover:bg-purple-700 text-white rounded-xl shadow-sm transition">Generate</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- VIEW INVOICE DETAIL MODAL -->
        <div id="view-modal" class="hidden fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto">
                <div class="flex justify-between items-start border-b border-slate-100 pb-3">
                    <div>
                        <h3 id="modal-inv-num" class="font-bold text-slate-900 text-base">INV-0000</h3>
                        <p id="modal-inv-date" class="text-xs text-slate-400">Date: -</p>
                    </div>
                    <button onclick="closeViewModal()" class="text-slate-400 hover:text-slate-600 text-lg">&times;</button>
                </div>
                
                <div class="space-y-3 text-xs">
                    <div class="grid grid-cols-2 gap-3 p-3 bg-slate-50 rounded-xl border border-slate-100">
                        <div>
                            <span class="text-slate-400 block font-medium">Customer:</span>
                            <span id="modal-customer" class="font-semibold text-slate-800">-</span>
                        </div>
                        <div>
                            <span class="text-slate-400 block font-medium">Status:</span>
                            <span id="modal-status" class="font-semibold">-</span>
                        </div>
                    </div>

                    <div>
                        <h4 class="font-semibold text-slate-700 mb-2">Itemized Line Items</h4>
                        <div id="modal-line-items" class="border border-slate-200 rounded-xl overflow-hidden divide-y divide-slate-100">
                            <!-- Items inserted here -->
                        </div>
                    </div>

                    <div class="p-3 bg-purple-50 rounded-xl space-y-1.5 font-semibold text-slate-800">
                        <div class="flex justify-between text-xs">
                            <span class="text-slate-500">Subtotal:</span>
                            <span id="modal-subtotal">$0.00</span>
                        </div>
                        <div class="flex justify-between text-xs">
                            <span class="text-slate-500">Tax:</span>
                            <span id="modal-tax">$0.00</span>
                        </div>
                        <div class="flex justify-between text-sm pt-1 border-t border-purple-200 text-purple-700 font-bold">
                            <span>Total Amount:</span>
                            <span id="modal-total">$0.00</span>
                        </div>
                    </div>
                </div>

                <div class="flex justify-between items-center pt-3 border-t border-slate-100">
                    <button type="button" onclick="closeViewModal()" class="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition">Close</button>
                    <a id="modal-download-btn" href="#" target="_blank" class="px-4 py-2 text-xs font-semibold bg-purple-600 hover:bg-purple-700 text-white rounded-xl shadow-sm transition inline-flex items-center space-x-1.5">
                        <span>⬇ Download PDF</span>
                    </a>
                </div>
            </div>
        </div>

        <script>
            let currentTab = 'profile';

            function switchTab(tab) {{
                currentTab = tab;
                const tabProfile = document.getElementById('nav-tab-profile');
                const tabInvoices = document.getElementById('nav-tab-invoices');
                const secProfile = document.getElementById('section-profile');
                const secInvoices = document.getElementById('section-invoices');

                if (tab === 'profile') {{
                    tabProfile.className = 'w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-purple-600 bg-purple-50 transition text-left';
                    tabInvoices.className = 'w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition text-left';
                    secProfile.classList.remove('hidden');
                    secInvoices.classList.add('hidden');
                }} else {{
                    tabProfile.className = 'w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition text-left';
                    tabInvoices.className = 'w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-purple-600 bg-purple-50 transition text-left';
                    secProfile.classList.add('hidden');
                    secInvoices.classList.remove('hidden');
                    loadInvoices();
                }}
            }}

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
                    document.getElementById('nav-user-badge').textContent = user.email;

                    document.getElementById('loading').classList.add('hidden');
                    document.getElementById('section-profile').classList.remove('hidden');
                }} catch (err) {{
                    localStorage.removeItem('billflow_token');
                    window.location.href = '/auth/signin';
                }}
            }}

            async function loadInvoices() {{
                const tbody = document.getElementById('invoices-tbody');
                const search = document.getElementById('inv-search').value.trim();
                const status = document.getElementById('inv-status').value.trim();
                const startDate = document.getElementById('inv-start-date').value.trim();
                const endDate = document.getElementById('inv-end-date').value.trim();

                const params = new URLSearchParams();
                if (search) params.append('search', search);
                if (status) params.append('status', status);
                if (startDate) params.append('start_date', startDate);
                if (endDate) params.append('end_date', endDate);

                try {{
                    const res = await fetch('/api/v1/invoices?' + params.toString());
                    const invoices = await res.json();

                    if (!Array.isArray(invoices) || invoices.length === 0) {{
                        tbody.innerHTML = `<tr><td colspan="9" class="px-4 py-8 text-center text-slate-400">No invoices found matching criteria.</td></tr>`;
                        return;
                    }}

                    tbody.innerHTML = invoices.map(inv => {{
                        const isPaid = (inv.status || '').toLowerCase() === 'paid';
                        const badgeColor = isPaid ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700';
                        const invDate = inv.invoice_date ? new Date(inv.invoice_date).toLocaleDateString() : '-';

                        return `
                            <tr class="hover:bg-slate-50/70 transition">
                                <td class="px-4 py-3 font-mono font-bold text-slate-900">${{inv.invoice_number}}</td>
                                <td class="px-4 py-3 font-medium text-slate-800">${{inv.customer_name || 'Customer ' + inv.customer_id.substring(0,6)}}</td>
                                <td class="px-4 py-3 text-slate-600">${{inv.plan_name || 'Subscription Plan'}}</td>
                                <td class="px-4 py-3 text-slate-500">${{invDate}}</td>
                                <td class="px-4 py-3 font-mono">$${{parseFloat(inv.subtotal).toFixed(2)}}</td>
                                <td class="px-4 py-3 font-mono text-slate-500">$${{parseFloat(inv.tax_amount).toFixed(2)}}</td>
                                <td class="px-4 py-3 font-mono font-bold text-slate-900">$${{parseFloat(inv.total_amount).toFixed(2)}}</td>
                                <td class="px-4 py-3">
                                    <span class="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${{badgeColor}}">${{inv.status}}</span>
                                </td>
                                <td class="px-4 py-3 text-right space-x-1.5 whitespace-nowrap">
                                    <button onclick="viewInvoice('${{inv.id}}')" class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition">View</button>
                                    <a href="/api/v1/invoices/${{inv.id}}/pdf" target="_blank" class="px-2.5 py-1 bg-purple-50 hover:bg-purple-100 text-purple-700 rounded-lg text-xs font-semibold transition inline-block">PDF</a>
                                </td>
                            </tr>
                        `;
                    }}).join('');
                }} catch (err) {{
                    tbody.innerHTML = `<tr><td colspan="9" class="px-4 py-8 text-center text-red-500">Failed to load invoices: ${{err.message}}</td></tr>`;
                }}
            }}

            async function viewInvoice(id) {{
                try {{
                    const res = await fetch('/api/v1/invoices/' + id);
                    if (!res.ok) throw new Error('Failed to fetch invoice details');
                    const inv = await res.json();

                    document.getElementById('modal-inv-num').textContent = inv.invoice_number;
                    document.getElementById('modal-inv-date').textContent = 'Date: ' + new Date(inv.invoice_date).toLocaleString();
                    document.getElementById('modal-customer').textContent = `${{inv.customer_name || 'Customer'}} (${{inv.customer_email || ''}})`;
                    
                    const isPaid = (inv.status || '').toLowerCase() === 'paid';
                    const badgeClass = isPaid ? 'text-emerald-600 bg-emerald-50' : 'text-amber-600 bg-amber-50';
                    document.getElementById('modal-status').innerHTML = `<span class="px-2 py-0.5 rounded text-[11px] font-bold uppercase ${{badgeClass}}">${{inv.status}}</span>`;
                    
                    document.getElementById('modal-subtotal').textContent = `$${{parseFloat(inv.subtotal).toFixed(2)}}`;
                    document.getElementById('modal-tax').textContent = `$${{parseFloat(inv.tax_amount).toFixed(2)}}`;
                    document.getElementById('modal-total').textContent = `$${{parseFloat(inv.total_amount).toFixed(2)}}`;
                    document.getElementById('modal-download-btn').href = `/api/v1/invoices/${{inv.id}}/pdf`;

                    const itemsContainer = document.getElementById('modal-line-items');
                    if (inv.line_items && inv.line_items.length > 0) {{
                        itemsContainer.innerHTML = inv.line_items.map(item => `
                            <div class="p-2.5 flex justify-between items-center text-xs">
                                <div>
                                    <div class="font-medium text-slate-800">${{item.description}}</div>
                                    <div class="text-[10px] text-slate-400 capitalize">${{item.line_item_type.replace('_', ' ')}}</div>
                                </div>
                                <div class="font-mono font-bold text-slate-900">$${{parseFloat(item.amount).toFixed(2)}}</div>
                            </div>
                        `).join('');
                    }} else {{
                        itemsContainer.innerHTML = `<div class="p-3 text-center text-slate-400">No line items recorded.</div>`;
                    }}

                    document.getElementById('view-modal').classList.remove('hidden');
                }} catch (err) {{
                    alert(err.message);
                }}
            }}

            function closeViewModal() {{
                document.getElementById('view-modal').classList.add('hidden');
            }}

            async function openGenerateModal() {{
                const modal = document.getElementById('generate-modal');
                const subSelect = document.getElementById('gen-sub-id');
                const errDiv = document.getElementById('gen-modal-error');
                errDiv.classList.add('hidden');
                modal.classList.remove('hidden');

                try {{
                    const res = await fetch('/api/v1/subscriptions');
                    if (!res.ok) throw new Error('Failed to load subscriptions');
                    const subs = await res.json();

                    if (!Array.isArray(subs) || subs.length === 0) {{
                        subSelect.innerHTML = `<option value="">No subscriptions available</option>`;
                        return;
                    }}

                    subSelect.innerHTML = subs.map(s => {{
                        const cust = s.customer ? s.customer.name : s.customer_id.substring(0,8);
                        const plan = s.plan ? s.plan.name : 'Plan';
                        const price = s.plan ? s.plan.price : '0';
                        return `<option value="${{s.id}}">Sub #${{s.id.substring(0,8)}} - ${{cust}} (${{plan}} - $${{price}})</option>`;
                    }}).join('');
                }} catch (err) {{
                    subSelect.innerHTML = `<option value="">Error: ${{err.message}}</option>`;
                }}
            }}

            function closeGenerateModal() {{
                document.getElementById('generate-modal').classList.add('hidden');
            }}

            async function handleGenerateInvoice(e) {{
                e.preventDefault();
                const subId = document.getElementById('gen-sub-id').value;
                const taxRate = parseFloat(document.getElementById('gen-tax-rate').value) || 0.10;
                const errDiv = document.getElementById('gen-modal-error');
                errDiv.classList.add('hidden');

                if (!subId) {{
                    errDiv.textContent = 'Please select a subscription';
                    errDiv.classList.remove('hidden');
                    return;
                }}

                try {{
                    const res = await fetch('/api/v1/invoices/generate', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ subscription_id: subId, tax_rate: taxRate }})
                    }});
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || 'Failed to generate invoice');

                    closeGenerateModal();
                    loadInvoices();
                    viewInvoice(data.id);
                }} catch (err) {{
                    errDiv.textContent = err.message;
                    errDiv.classList.remove('hidden');
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
