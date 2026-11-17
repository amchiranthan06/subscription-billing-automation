import React, { useState, useEffect } from 'react';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export default function App() {
  const [activeTab, setActiveTab] = useState('signin'); // 'signin' | 'signup'
  const [navSection, setNavSection] = useState('invoices'); // 'profile' | 'invoices'
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Form states for Auth
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Invoice States
  const [invoices, setInvoices] = useState([]);
  const [invLoading, setInvLoading] = useState(false);
  const [searchFilter, setSearchFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [startDateFilter, setStartDateFilter] = useState('');
  const [endDateFilter, setEndDateFilter] = useState('');
  const [selectedInvoice, setSelectedInvoice] = useState(null);

  // Generate Invoice Modal
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
  const [subscriptions, setSubscriptions] = useState([]);
  const [selectedSubId, setSelectedSubId] = useState('');
  const [taxRate, setTaxRate] = useState('0.10');
  const [genLoading, setGenLoading] = useState(false);
  const [genError, setGenError] = useState('');

  // Check for saved token on load
  useEffect(() => {
    const token = localStorage.getItem('billflow_token');
    if (token) {
      fetchUserProfile(token);
    }
  }, []);

  // Fetch invoices when authenticated
  useEffect(() => {
    if (user) {
      fetchInvoices();
    }
  }, [user, searchFilter, statusFilter, startDateFilter, endDateFilter]);

  const fetchUserProfile = async (token) => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        const userData = await res.json();
        setUser(userData);
      } else {
        localStorage.removeItem('billflow_token');
        setUser(null);
      }
    } catch (err) {
      console.error('Error fetching user profile:', err);
      localStorage.removeItem('billflow_token');
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSignIn = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/auth/signin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Sign in failed. Please check your credentials.');
      }

      localStorage.setItem('billflow_token', data.access_token);
      setUser(data.user);
      setPassword('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Registration failed.');
      }

      localStorage.setItem('billflow_token', data.access_token);
      setUser(data.user);
      setName('');
      setEmail('');
      setPassword('');
      setSuccessMsg('Account registered successfully!');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = () => {
    localStorage.removeItem('billflow_token');
    setUser(null);
    setError('');
    setSuccessMsg('');
    setActiveTab('signin');
  };

  const fetchInvoices = async () => {
    try {
      setInvLoading(true);
      const params = new URLSearchParams();
      if (searchFilter.trim()) params.append('search', searchFilter.trim());
      if (statusFilter.trim()) params.append('status', statusFilter.trim());
      if (startDateFilter.trim()) params.append('start_date', startDateFilter.trim());
      if (endDateFilter.trim()) params.append('end_date', endDateFilter.trim());

      const res = await fetch(`${API_BASE_URL}/invoices?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setInvoices(data);
      }
    } catch (err) {
      console.error('Failed to fetch invoices:', err);
    } finally {
      setInvLoading(false);
    }
  };

  const openGenerateModal = async () => {
    setGenError('');
    setIsGenerateModalOpen(true);
    try {
      const res = await fetch(`${API_BASE_URL}/subscriptions`);
      if (res.ok) {
        const data = await res.json();
        setSubscriptions(data);
        if (data.length > 0) setSelectedSubId(data[0].id);
      }
    } catch (err) {
      setGenError('Failed to load subscriptions');
    }
  };

  const handleGenerateInvoice = async (e) => {
    e.preventDefault();
    setGenError('');
    setGenLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/invoices/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subscription_id: selectedSubId,
          tax_rate: parseFloat(taxRate) || 0.10
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Invoice generation failed');

      setIsGenerateModalOpen(false);
      fetchInvoices();
      setSelectedInvoice(data);
    } catch (err) {
      setGenError(err.message);
    } finally {
      setGenLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* 1. TOP NAVBAR */}
      <header className="bg-white border-b border-slate-200 px-6 py-3.5 flex items-center justify-between sticky top-0 z-30 shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 bg-indigo-600 text-white rounded-xl flex items-center justify-center font-bold text-sm shadow-sm">
            BF
          </div>
          <div>
            <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
              BillFlow Subscription Billing Automation System
            </h1>
            <p className="text-[11px] text-slate-500 hidden sm:block">
              Milestone 2: Recurring Revenue, Invoicing & Financial Operations
            </p>
          </div>
        </div>

        {user && (
          <div className="flex items-center space-x-3">
            <span className="text-xs bg-slate-100 text-slate-700 px-3 py-1.5 rounded-lg font-medium border border-slate-200 hidden sm:inline-block">
              {user.email}
            </span>
            <button
              onClick={handleSignOut}
              className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg transition shadow-sm"
            >
              Sign Out
            </button>
          </div>
        )}
      </header>

      {/* 2. BODY CONTENT */}
      {user ? (
        /* AUTHENTICATED DASHBOARD WITH SIDEBAR */
        <div className="flex flex-1">
          {/* SIDEBAR */}
          <aside className="w-60 bg-white border-r border-slate-200 p-4 space-y-2 flex-shrink-0">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-3 py-1">
              Navigation
            </div>

            <button
              onClick={() => setNavSection('invoices')}
              className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition text-left ${
                navSection === 'invoices'
                  ? 'text-indigo-600 bg-indigo-50'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <span className="text-base">📄</span>
              <span>Invoices (M2-T1)</span>
            </button>

            <button
              onClick={() => setNavSection('profile')}
              className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition text-left ${
                navSection === 'profile'
                  ? 'text-indigo-600 bg-indigo-50'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <span className="text-base">👤</span>
              <span>User Profile</span>
            </button>

            <div className="pt-6 mt-6 border-t border-slate-100">
              <div className="p-3 bg-indigo-50/60 rounded-xl border border-indigo-100 text-xs text-indigo-900">
                <div className="font-bold mb-1">Milestone 2 Active</div>
                <div className="text-[11px] text-indigo-700">
                  Task 1: Automated Invoice Generation, Subtotal/Tax calculation & PDF exports.
                </div>
              </div>
            </div>
          </aside>

          {/* MAIN WORKSPACE */}
          <main className="flex-1 p-6 md:p-8 max-w-7xl overflow-y-auto">
            {navSection === 'invoices' ? (
              /* INVOICES SECTION */
              <div className="space-y-6">
                {/* Header & Generate Button */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div>
                    <h2 className="text-2xl font-bold text-slate-900">Invoices & Billing</h2>
                    <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                      Itemized invoices generated per billing cycle with automated tax and PDF generation.
                    </p>
                  </div>
                  <button
                    onClick={openGenerateModal}
                    className="inline-flex items-center space-x-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-sm transition"
                  >
                    <span>+</span>
                    <span>Generate Invoice</span>
                  </button>
                </div>

                {/* Filter Bar */}
                <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                      Search
                    </label>
                    <input
                      type="text"
                      value={searchFilter}
                      onChange={(e) => setSearchFilter(e.target.value)}
                      placeholder="Invoice # or customer..."
                      className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                      Status
                    </label>
                    <select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                    >
                      <option value="">All Statuses</option>
                      <option value="unpaid">Unpaid</option>
                      <option value="paid">Paid</option>
                      <option value="draft">Draft</option>
                      <option value="void">Void</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={startDateFilter}
                      onChange={(e) => setStartDateFilter(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                      End Date
                    </label>
                    <input
                      type="date"
                      value={endDateFilter}
                      onChange={(e) => setEndDateFilter(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>

                {/* Table */}
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                        <tr>
                          <th className="px-4 py-3.5">Invoice #</th>
                          <th className="px-4 py-3.5">Customer</th>
                          <th className="px-4 py-3.5">Plan</th>
                          <th className="px-4 py-3.5">Issue Date</th>
                          <th className="px-4 py-3.5">Subtotal</th>
                          <th className="px-4 py-3.5">Tax</th>
                          <th className="px-4 py-3.5">Total</th>
                          <th className="px-4 py-3.5">Status</th>
                          <th className="px-4 py-3.5 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 text-slate-700">
                        {invLoading ? (
                          <tr>
                            <td colSpan="9" className="px-4 py-8 text-center text-slate-400">
                              Loading invoices...
                            </td>
                          </tr>
                        ) : invoices.length === 0 ? (
                          <tr>
                            <td colSpan="9" className="px-4 py-8 text-center text-slate-400">
                              No invoices found. Click "+ Generate Invoice" to create one.
                            </td>
                          </tr>
                        ) : (
                          invoices.map((inv) => {
                            const isPaid = (inv.status || '').toLowerCase() === 'paid';
                            const badgeColor = isPaid
                              ? 'bg-emerald-100 text-emerald-700'
                              : 'bg-amber-100 text-amber-700';

                            return (
                              <tr key={inv.id} className="hover:bg-slate-50/70 transition">
                                <td className="px-4 py-3 font-mono font-bold text-slate-900">
                                  {inv.invoice_number}
                                </td>
                                <td className="px-4 py-3 font-medium text-slate-800">
                                  {inv.customer_name || `Customer ${inv.customer_id.substring(0, 6)}`}
                                </td>
                                <td className="px-4 py-3 text-slate-600">
                                  {inv.plan_name || 'Standard Plan'}
                                </td>
                                <td className="px-4 py-3 text-slate-500">
                                  {inv.invoice_date ? new Date(inv.invoice_date).toLocaleDateString() : '-'}
                                </td>
                                <td className="px-4 py-3 font-mono">
                                  ${parseFloat(inv.subtotal).toFixed(2)}
                                </td>
                                <td className="px-4 py-3 font-mono text-slate-500">
                                  ${parseFloat(inv.tax_amount).toFixed(2)}
                                </td>
                                <td className="px-4 py-3 font-mono font-bold text-slate-900">
                                  ${parseFloat(inv.total_amount).toFixed(2)}
                                </td>
                                <td className="px-4 py-3">
                                  <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${badgeColor}`}>
                                    {inv.status}
                                  </span>
                                </td>
                                <td className="px-4 py-3 text-right space-x-1.5 whitespace-nowrap">
                                  <button
                                    onClick={() => setSelectedInvoice(inv)}
                                    className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition"
                                  >
                                    View
                                  </button>
                                  <a
                                    href={`${API_BASE_URL}/invoices/${inv.id}/pdf`}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-semibold transition inline-block"
                                  >
                                    PDF ⬇
                                  </a>
                                </td>
                              </tr>
                            );
                          })
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : (
              /* PROFILE SECTION */
              <div className="max-w-2xl mx-auto space-y-6">
                <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
                  <div className="w-14 h-14 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto mb-4 font-bold text-xl">
                    ✓
                  </div>
                  <h2 className="text-xl font-bold text-center text-slate-800">
                    JWT Session Authenticated
                  </h2>
                  <p className="text-center text-xs text-slate-500 mt-1 mb-6">
                    Active Session Token verified via JWT Bearer
                  </p>

                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-3">
                    <div className="flex justify-between items-center text-sm border-b border-slate-200 pb-2">
                      <span className="text-slate-500 font-medium">User Name:</span>
                      <span className="font-semibold text-slate-800">{user.name}</span>
                    </div>
                    <div className="flex justify-between items-center text-sm border-b border-slate-200 pb-2">
                      <span className="text-slate-500 font-medium">Email Address:</span>
                      <span className="font-semibold text-slate-800">{user.email}</span>
                    </div>
                    <div className="flex justify-between items-center text-sm border-b border-slate-200 pb-2">
                      <span className="text-slate-500 font-medium">Account Role:</span>
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-700 uppercase">
                        {user.role || 'customer'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-slate-500 font-medium">User ID:</span>
                      <span className="font-mono text-xs text-slate-600">{user.id}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </main>
        </div>
      ) : (
        /* UNAUTHENTICATED SIGN IN / SIGN UP */
        <main className="max-w-md mx-auto w-full my-auto py-12 px-4">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            {/* Tab Selector */}
            <div className="grid grid-cols-2 border-b border-slate-200 bg-slate-50/50">
              <button
                type="button"
                onClick={() => { setActiveTab('signin'); setError(''); }}
                className={`py-3.5 text-sm font-semibold text-center transition border-b-2 ${
                  activeTab === 'signin'
                    ? 'border-indigo-600 text-indigo-600 bg-white'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => { setActiveTab('signup'); setError(''); }}
                className={`py-3.5 text-sm font-semibold text-center transition border-b-2 ${
                  activeTab === 'signup'
                    ? 'border-indigo-600 text-indigo-600 bg-white'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                Sign Up
              </button>
            </div>

            <div className="p-8">
              {error && (
                <div className="mb-5 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
                  ⚠️ {error}
                </div>
              )}
              {successMsg && (
                <div className="mb-5 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-medium">
                  ✅ {successMsg}
                </div>
              )}

              {activeTab === 'signin' ? (
                <form onSubmit={handleSignIn} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      Email Address
                    </label>
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="user@example.com"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      Password
                    </label>
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                  >
                    {loading ? 'Authenticating...' : 'Sign In'}
                  </button>
                </form>
              ) : (
                <form onSubmit={handleSignUp} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      Full Name
                    </label>
                    <input
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Jane Doe"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      Email Address
                    </label>
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="jane@example.com"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      Password (min 6 characters)
                    </label>
                    <input
                      type="password"
                      required
                      minLength={6}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                  >
                    {loading ? 'Creating Account...' : 'Create Account'}
                  </button>
                </form>
              )}
            </div>
          </div>
        </main>
      )}

      {/* GENERATE INVOICE MODAL */}
      {isGenerateModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-bold text-slate-900 text-base">Generate New Invoice</h3>
              <button
                onClick={() => setIsGenerateModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 text-lg"
              >
                &times;
              </button>
            </div>

            {genError && (
              <div className="p-2.5 bg-rose-50 text-rose-700 text-xs rounded-xl border border-rose-200">
                {genError}
              </div>
            )}

            <form onSubmit={handleGenerateInvoice} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">
                  Select Subscription
                </label>
                <select
                  required
                  value={selectedSubId}
                  onChange={(e) => setSelectedSubId(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                >
                  {subscriptions.length === 0 ? (
                    <option value="">No subscriptions available</option>
                  ) : (
                    subscriptions.map((s) => {
                      const custName = s.customer ? s.customer.name : s.customer_id.substring(0, 8);
                      const planName = s.plan ? s.plan.name : 'Plan';
                      return (
                        <option key={s.id} value={s.id}>
                          Sub #{s.id.substring(0, 8)} - {custName} ({planName})
                        </option>
                      );
                    })
                  )}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">
                  Tax Rate (0.10 = 10%)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  value={taxRate}
                  onChange={(e) => setTaxRate(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsGenerateModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={genLoading || !selectedSubId}
                  className="px-4 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-sm transition disabled:opacity-50"
                >
                  {genLoading ? 'Generating...' : 'Generate Invoice'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* VIEW INVOICE MODAL */}
      {selectedInvoice && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start border-b border-slate-100 pb-3">
              <div>
                <h3 className="font-bold text-slate-900 text-base">
                  {selectedInvoice.invoice_number}
                </h3>
                <p className="text-xs text-slate-400">
                  Issued: {new Date(selectedInvoice.invoice_date).toLocaleString()}
                </p>
              </div>
              <button
                onClick={() => setSelectedInvoice(null)}
                className="text-slate-400 hover:text-slate-600 text-lg"
              >
                &times;
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 rounded-xl border border-slate-100">
                <div>
                  <span className="text-slate-400 block font-medium">Customer:</span>
                  <span className="font-semibold text-slate-800">
                    {selectedInvoice.customer_name || selectedInvoice.customer_id}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block font-medium">Status:</span>
                  <span
                    className={`inline-block px-2 py-0.5 rounded text-[11px] font-bold uppercase ${
                      (selectedInvoice.status || '').toLowerCase() === 'paid'
                        ? 'text-emerald-700 bg-emerald-100'
                        : 'text-amber-700 bg-amber-100'
                    }`}
                  >
                    {selectedInvoice.status}
                  </span>
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-slate-700 mb-2">Itemized Breakdown</h4>
                <div className="border border-slate-200 rounded-xl overflow-hidden divide-y divide-slate-100">
                  {selectedInvoice.line_items && selectedInvoice.line_items.length > 0 ? (
                    selectedInvoice.line_items.map((item) => (
                      <div key={item.id} className="p-2.5 flex justify-between items-center text-xs">
                        <div>
                          <div className="font-medium text-slate-800">{item.description}</div>
                          <div className="text-[10px] text-slate-400 capitalize">
                            {item.line_item_type.replace('_', ' ')}
                          </div>
                        </div>
                        <div className="font-mono font-bold text-slate-900">
                          ${parseFloat(item.amount).toFixed(2)}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-3 text-center text-slate-400">
                      Standard Subscription Plan Fee
                    </div>
                  )}
                </div>
              </div>

              <div className="p-3 bg-indigo-50/70 rounded-xl space-y-1.5 font-semibold text-slate-800">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">Subtotal:</span>
                  <span>${parseFloat(selectedInvoice.subtotal).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">Tax Amount:</span>
                  <span>${parseFloat(selectedInvoice.tax_amount).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm pt-1 border-t border-indigo-200 text-indigo-700 font-bold">
                  <span>Total Amount:</span>
                  <span>${parseFloat(selectedInvoice.total_amount).toFixed(2)}</span>
                </div>
              </div>
            </div>

            <div className="flex justify-between items-center pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setSelectedInvoice(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition"
              >
                Close
              </button>
              <a
                href={`${API_BASE_URL}/invoices/${selectedInvoice.id}/pdf`}
                target="_blank"
                rel="noreferrer"
                className="px-4 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-sm transition inline-flex items-center space-x-1.5"
              >
                <span>⬇ Download PDF</span>
              </a>
            </div>
          </div>
        </div>
      )}

      {/* FOOTER */}
      <footer className="text-center text-xs text-slate-400 py-4 mt-auto border-t border-slate-200 bg-white">
        BillFlow — Subscription Billing Automation System &copy; {new Date().getFullYear()}
      </footer>
    </div>
  );
}
