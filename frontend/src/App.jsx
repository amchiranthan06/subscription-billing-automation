import React, { useState, useEffect } from 'react';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export default function App() {
  const [activeTab, setActiveTab] = useState('signin'); // 'signin' | 'signup'
  const [navSection, setNavSection] = useState('subscriptions'); // 'subscriptions' | 'invoices' | 'profile'
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Form states for Auth
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Invoice States (Task 1)
  const [invoices, setInvoices] = useState([]);
  const [invLoading, setInvLoading] = useState(false);
  const [searchFilter, setSearchFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [startDateFilter, setStartDateFilter] = useState('');
  const [endDateFilter, setEndDateFilter] = useState('');
  const [selectedInvoice, setSelectedInvoice] = useState(null);

  // Generate Invoice Modal
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
  const [selectedSubId, setSelectedSubId] = useState('');
  const [taxRate, setTaxRate] = useState('0.10');
  const [genLoading, setGenLoading] = useState(false);
  const [genError, setGenError] = useState('');

  // Subscriptions & Proration States (Task 2)
  const [subscriptions, setSubscriptions] = useState([]);
  const [plans, setPlans] = useState([]);
  const [subsLoading, setSubsLoading] = useState(false);
  const [isPlanChangeModalOpen, setIsPlanChangeModalOpen] = useState(false);
  const [selectedSubForChange, setSelectedSubForChange] = useState(null);
  const [targetPlanId, setTargetPlanId] = useState('');
  const [prorationPreview, setProrationPreview] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [planChangeError, setPlanChangeError] = useState('');
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [planHistory, setPlanHistory] = useState([]);

  // Payment Gateway & Webhook States (Task 3)
  const [payments, setPayments] = useState([]);
  const [payLoading, setPayLoading] = useState(false);
  const [payStatusFilter, setPayStatusFilter] = useState('');
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [isProcessModalOpen, setIsProcessModalOpen] = useState(false);
  const [processInvoiceId, setProcessInvoiceId] = useState('');
  const [processAmount, setProcessAmount] = useState('');
  const [simulateMode, setSimulateMode] = useState('random'); // 'random' | 'success' | 'failure'
  const [processLoading, setProcessLoading] = useState(false);
  const [processResult, setProcessResult] = useState(null);
  const [processError, setProcessError] = useState('');

  // Check for saved token on load
  useEffect(() => {
    const token = localStorage.getItem('billflow_token');
    if (token) {
      fetchUserProfile(token);
    }
  }, []);

  // Fetch data when authenticated
  useEffect(() => {
    if (user) {
      if (navSection === 'invoices') {
        fetchInvoices();
      } else if (navSection === 'subscriptions') {
        fetchSubscriptionsAndPlans();
      } else if (navSection === 'payments') {
        fetchPayments();
        fetchInvoices();
      }
    }
  }, [user, navSection, searchFilter, statusFilter, startDateFilter, endDateFilter, payStatusFilter]);

  const fetchUserProfile = async (token) => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
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
      if (!res.ok) throw new Error(data.detail || 'Sign in failed.');

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
      if (!res.ok) throw new Error(data.detail || 'Registration failed.');

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

  const fetchSubscriptionsAndPlans = async () => {
    try {
      setSubsLoading(true);
      const [subsRes, plansRes] = await Promise.all([
        fetch(`${API_BASE_URL}/subscriptions`),
        fetch(`${API_BASE_URL}/plans`)
      ]);
      if (subsRes.ok && plansRes.ok) {
        const subsData = await subsRes.json();
        const plansData = await plansRes.json();
        setSubscriptions(subsData);
        setPlans(plansData);
        if (subsData.length > 0) {
          fetchPlanHistory(subsData[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to load subscriptions & plans:', err);
    } finally {
      setSubsLoading(false);
    }
  };

  const fetchPlanHistory = async (subId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/subscriptions/${subId}/plan-history`);
      if (res.ok) {
        const historyData = await res.json();
        setPlanHistory(historyData);
      }
    } catch (err) {
      console.error('Failed to load plan history:', err);
    }
  };

  const openPlanChangeModal = (sub) => {
    setSelectedSubForChange(sub);
    setTargetPlanId('');
    setProrationPreview(null);
    setPlanChangeError('');
    setIsPlanChangeModalOpen(true);
  };

  const handleTargetPlanSelect = async (newPlanId) => {
    setTargetPlanId(newPlanId);
    setPlanChangeError('');
    setProrationPreview(null);
    setPreviewLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/subscriptions/${selectedSubForChange.id}/proration-preview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_plan_id: newPlanId })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to calculate proration preview');
      setProrationPreview(data);
    } catch (err) {
      setPlanChangeError(err.message);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleConfirmPlanChange = async () => {
    if (!selectedSubForChange || !targetPlanId) return;
    setPlanChangeError('');
    setConfirmLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/subscriptions/${selectedSubForChange.id}/change-plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_plan_id: targetPlanId, prorate: true })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Plan upgrade failed');

      setIsPlanChangeModalOpen(false);
      await fetchSubscriptionsAndPlans();
      fetchPlanHistory(selectedSubForChange.id);
    } catch (err) {
      setPlanChangeError(err.message);
    } finally {
      setConfirmLoading(false);
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

  const fetchPayments = async () => {
    try {
      setPayLoading(true);
      const params = new URLSearchParams();
      if (payStatusFilter.trim()) params.append('status', payStatusFilter.trim());
      const res = await fetch(`${API_BASE_URL}/payments?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setPayments(data);
      }
    } catch (err) {
      console.error('Failed to fetch payments:', err);
    } finally {
      setPayLoading(false);
    }
  };

  const openProcessPaymentModal = (invoice = null) => {
    if (invoice) {
      setProcessInvoiceId(String(invoice.id));
      setProcessAmount(parseFloat(invoice.total_amount).toFixed(2));
    } else {
      setProcessInvoiceId('');
      setProcessAmount('');
    }
    setSimulateMode('random');
    setProcessResult(null);
    setProcessError('');
    setIsProcessModalOpen(true);
  };

  const handleProcessPaymentSubmit = async (e) => {
    e.preventDefault();
    if (!processInvoiceId || !processAmount) {
      setProcessError('Invoice ID and Amount are required');
      return;
    }
    setProcessLoading(true);
    setProcessError('');
    setProcessResult(null);

    try {
      const res = await fetch(`${API_BASE_URL}/payments/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          invoice_id: parseInt(processInvoiceId),
          amount: parseFloat(processAmount),
          simulate_mode: simulateMode
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Payment processing failed');
      setProcessResult(data);
      fetchPayments();
      fetchInvoices();
    } catch (err) {
      setProcessError(err.message);
    } finally {
      setProcessLoading(false);
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
              Milestone 2: Recurring Revenue, Invoicing & Prorated Plan Operations
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
        <div className="flex flex-1">
          {/* SIDEBAR */}
          <aside className="w-64 bg-white border-r border-slate-200 p-4 space-y-2 flex-shrink-0">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-3 py-1">
              Navigation
            </div>

            <button
              onClick={() => setNavSection('subscriptions')}
              className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition text-left ${
                navSection === 'subscriptions'
                  ? 'text-indigo-600 bg-indigo-50'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <span className="text-base">🔁</span>
              <span>Proration & Plans (M2-T2)</span>
            </button>

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
              onClick={() => setNavSection('payments')}
              className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition text-left ${
                navSection === 'payments'
                  ? 'text-indigo-600 bg-indigo-50'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <span className="text-base">💳</span>
              <span>Payments & Webhooks (M2-T3)</span>
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
                  Task 3: Mock Payment Gateway (80/20 probability) & Automated Webhook Lifecycle.
                </div>
              </div>
            </div>
          </aside>

          {/* MAIN WORKSPACE */}
          <main className="flex-1 p-6 md:p-8 max-w-7xl overflow-y-auto">
            {navSection === 'subscriptions' ? (
              /* SUBSCRIPTIONS & PRORATION SECTION (Task 2) */
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-slate-900">Subscription & Proration Engine</h2>
                  <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                    Upgrade or downgrade subscription plans mid-cycle with mathematically fair credit and debit adjustments.
                  </p>
                </div>

                {/* Subscriptions Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  {subsLoading ? (
                    <div className="col-span-2 p-8 text-center text-slate-400 bg-white rounded-2xl border border-slate-200">
                      Loading subscriptions...
                    </div>
                  ) : subscriptions.length === 0 ? (
                    <div className="col-span-2 p-8 text-center text-slate-400 bg-white rounded-2xl border border-slate-200">
                      No subscriptions found.
                    </div>
                  ) : (
                    subscriptions.map((s) => {
                      const custName = s.customer ? s.customer.name : `Customer ${s.customer_id.substring(0, 6)}`;
                      const planName = s.plan ? s.plan.name : 'Current Plan';
                      const planPrice = s.plan ? parseFloat(s.plan.price).toFixed(2) : '0.00';
                      const interval = s.plan ? s.plan.billing_interval : 'month';

                      return (
                        <div key={s.id} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
                          <div className="flex justify-between items-start">
                            <div>
                              <span className="text-[11px] font-semibold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full uppercase tracking-wider">
                                Sub #{s.id.substring(0, 8)}
                              </span>
                              <h3 className="font-bold text-slate-900 text-base mt-2">{custName}</h3>
                              <p className="text-xs text-slate-500">
                                Renewal: {new Date(s.end_date).toLocaleDateString()}
                              </p>
                            </div>
                            <div className="text-right">
                              <div className="text-lg font-mono font-extrabold text-slate-900">${planPrice}</div>
                              <div className="text-[10px] text-slate-400 uppercase">per {interval}</div>
                            </div>
                          </div>

                          <div className="p-3 bg-slate-50 rounded-xl flex justify-between items-center text-xs">
                            <span className="text-slate-500 font-medium">Current Plan:</span>
                            <span className="font-bold text-indigo-700">{planName}</span>
                          </div>

                          <div className="flex justify-between items-center pt-2">
                            <button
                              onClick={() => fetchPlanHistory(s.id)}
                              className="text-xs text-slate-500 hover:text-slate-700 font-semibold underline"
                            >
                              View History
                            </button>
                            <button
                              onClick={() => openPlanChangeModal(s)}
                              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-sm transition"
                            >
                              Upgrade / Change Plan
                            </button>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>

                {/* Previous Plan Changes Timeline */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                    <h3 className="font-bold text-slate-900 text-sm md:text-base flex items-center space-x-2">
                      <span>📜</span>
                      <span>Previous Plan Changes</span>
                    </h3>
                    <span className="text-xs text-slate-400">Audit-backed history</span>
                  </div>

                  <div className="space-y-3">
                    {planHistory.length === 0 ? (
                      <p className="text-xs text-slate-400 py-3">
                        No previous plan changes recorded for this subscription. Try upgrading a plan above!
                      </p>
                    ) : (
                      planHistory.map((item, idx) => {
                        const adj = parseFloat(item.net_adjustment || 0);
                        const adjClass = adj >= 0 ? 'text-indigo-700 bg-indigo-50' : 'text-emerald-700 bg-emerald-50';

                        return (
                          <div
                            key={idx}
                            className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-xs"
                          >
                            <div className="flex items-center space-x-3">
                              <span className="w-2.5 h-2.5 rounded-full bg-indigo-600"></span>
                              <div>
                                <span className="font-bold text-slate-800">
                                  {item.from_plan} → {item.to_plan}
                                </span>
                                <span className="text-slate-400 text-[11px] ml-2">
                                  {item.date ? new Date(item.date).toLocaleDateString() : '-'}
                                </span>
                              </div>
                            </div>
                            <div className="flex items-center space-x-3">
                              <span className={`font-mono font-bold px-2.5 py-1 rounded-lg ${adjClass}`}>
                                Adjustment: ${adj.toFixed(2)}
                              </span>
                              {item.invoice_number && (
                                <span className="text-[10px] font-mono text-slate-400">
                                  ({item.invoice_number})
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              </div>
            ) : navSection === 'invoices' ? (
              /* INVOICES SECTION (Task 1) */
              <div className="space-y-6">
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
                    <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">Search</label>
                    <input
                      type="text"
                      value={searchFilter}
                      onChange={(e) => setSearchFilter(e.target.value)}
                      placeholder="Invoice # or customer..."
                      className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">Status</label>
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
                    <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">Start Date</label>
                    <input
                      type="date"
                      value={startDateFilter}
                      onChange={(e) => setStartDateFilter(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">End Date</label>
                    <input
                      type="date"
                      value={endDateFilter}
                      onChange={(e) => setEndDateFilter(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>

                {/* Invoices Table */}
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
                            <td colSpan="9" className="px-4 py-8 text-center text-slate-400">Loading invoices...</td>
                          </tr>
                        ) : invoices.length === 0 ? (
                          <tr>
                            <td colSpan="9" className="px-4 py-8 text-center text-slate-400">No invoices found.</td>
                          </tr>
                        ) : (
                          invoices.map((inv) => {
                            const isPaid = (inv.status || '').toLowerCase() === 'paid';
                            const badgeColor = isPaid ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700';

                            return (
                              <tr key={inv.id} className="hover:bg-slate-50/70 transition">
                                <td className="px-4 py-3 font-mono font-bold text-slate-900">{inv.invoice_number}</td>
                                <td className="px-4 py-3 font-medium text-slate-800">{inv.customer_name || 'Customer'}</td>
                                <td className="px-4 py-3 text-slate-600">{inv.plan_name || 'Standard Plan'}</td>
                                <td className="px-4 py-3 text-slate-500">{inv.invoice_date ? new Date(inv.invoice_date).toLocaleDateString() : '-'}</td>
                                <td className="px-4 py-3 font-mono">${parseFloat(inv.subtotal).toFixed(2)}</td>
                                <td className="px-4 py-3 font-mono text-slate-500">${parseFloat(inv.tax_amount).toFixed(2)}</td>
                                <td className="px-4 py-3 font-mono font-bold text-slate-900">${parseFloat(inv.total_amount).toFixed(2)}</td>
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
                                  {(inv.status || '').toLowerCase() === 'unpaid' && (
                                    <button
                                      onClick={() => { openProcessPaymentModal(inv); setNavSection('payments'); }}
                                      className="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 rounded-lg text-xs font-semibold transition"
                                    >
                                      💳 Pay
                                    </button>
                                  )}
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
            ) : navSection === 'payments' ? (
              /* PAYMENTS & WEBHOOKS SECTION (Task 3) */
              <div className="space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div>
                    <h2 className="text-2xl font-bold text-slate-900">Payment Gateway & Webhooks</h2>
                    <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                      Mock payment processor: 80% success / 20% failure simulation with webhook-driven invoice &amp; subscription updates.
                    </p>
                  </div>
                  <button
                    onClick={() => openProcessPaymentModal()}
                    className="inline-flex items-center space-x-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl shadow-sm transition"
                  >
                    <span>💳</span>
                    <span>Process Payment</span>
                  </button>
                </div>

                {/* Status Filter Bar */}
                <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center gap-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">Filter by Status</label>
                    <select
                      value={payStatusFilter}
                      onChange={(e) => { setPayStatusFilter(e.target.value); fetchPayments(); }}
                      className="w-full sm:w-48 px-3 py-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
                    >
                      <option value="">All Statuses</option>
                      <option value="success">Success</option>
                      <option value="failed">Failed</option>
                      <option value="refunded">Refunded</option>
                    </select>
                  </div>
                  <div className="mt-4 sm:mt-5">
                    <button
                      onClick={fetchPayments}
                      className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition"
                    >
                      🔄 Refresh
                    </button>
                  </div>
                </div>

                {/* Payment Dashboard Table */}
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                        <tr>
                          <th className="px-4 py-3.5">Transaction ID</th>
                          <th className="px-4 py-3.5">Invoice #</th>
                          <th className="px-4 py-3.5">Amount</th>
                          <th className="px-4 py-3.5">Status</th>
                          <th className="px-4 py-3.5">Date</th>
                          <th className="px-4 py-3.5 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 text-slate-700">
                        {payLoading ? (
                          <tr>
                            <td colSpan="6" className="px-4 py-8 text-center text-slate-400">Loading payments...</td>
                          </tr>
                        ) : payments.length === 0 ? (
                          <tr>
                            <td colSpan="6" className="px-4 py-8 text-center text-slate-400">
                              No payment transactions found. Use "Process Payment" to simulate one.
                            </td>
                          </tr>
                        ) : (
                          payments.map((pmt) => {
                            const st = (pmt.status || '').toLowerCase();
                            const badge =
                              st === 'success' ? 'bg-emerald-100 text-emerald-700' :
                              st === 'failed' ? 'bg-rose-100 text-rose-700' :
                              st === 'refunded' ? 'bg-amber-100 text-amber-700' :
                              'bg-slate-100 text-slate-600';
                            return (
                              <tr key={pmt.id} className="hover:bg-slate-50/70 transition">
                                <td className="px-4 py-3 font-mono font-bold text-slate-900 text-[11px]">{pmt.payment_reference || pmt.id}</td>
                                <td className="px-4 py-3 font-mono text-slate-700">{pmt.invoice_number || `INV-${pmt.invoice_id}`}</td>
                                <td className="px-4 py-3 font-mono font-bold text-slate-900">₹{parseFloat(pmt.amount).toFixed(2)}</td>
                                <td className="px-4 py-3">
                                  <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${badge}`}>
                                    {pmt.status}
                                  </span>
                                </td>
                                <td className="px-4 py-3 text-slate-500">{pmt.created_at ? new Date(pmt.created_at).toLocaleDateString() : '-'}</td>
                                <td className="px-4 py-3 text-right">
                                  <button
                                    onClick={() => setSelectedPayment(pmt)}
                                    className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition"
                                  >
                                    Details
                                  </button>
                                </td>
                              </tr>
                            );
                          })
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Quick Pay Buttons from pending invoices */}
                {invoices.filter(inv => (inv.status || '').toLowerCase() === 'unpaid').length > 0 && (
                  <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
                    <h3 className="text-sm font-bold text-slate-800">⚡ Quick Pay — Pending Invoices</h3>
                    <div className="space-y-2">
                      {invoices.filter(inv => (inv.status || '').toLowerCase() === 'unpaid').map(inv => (
                        <div key={inv.id} className="flex items-center justify-between p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs">
                          <div>
                            <span className="font-mono font-bold text-slate-900">{inv.invoice_number}</span>
                            <span className="text-slate-500 ml-2">—  ₹{parseFloat(inv.total_amount).toFixed(2)}</span>
                            <span className="ml-2 text-amber-600 font-semibold">Unpaid</span>
                          </div>
                          <button
                            onClick={() => openProcessPaymentModal(inv)}
                            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition"
                          >
                            Pay Now
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Workflow Info Card */}
                <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                  <h3 className="text-sm font-bold text-slate-800 mb-3">📊 Payment Workflow</h3>
                  <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 text-xs text-slate-600">
                    {['Invoice Generated','Process Payment','80% Success / 20% Failure','Webhook Sent','Invoice & Subscription Updated'].map((step, idx, arr) => (
                      <React.Fragment key={step}>
                        <span className="px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-lg font-semibold border border-indigo-100">{step}</span>
                        {idx < arr.length - 1 && <span className="text-slate-400 font-bold hidden sm:inline">→</span>}
                      </React.Fragment>
                    ))}
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
                  <h2 className="text-xl font-bold text-center text-slate-800">JWT Session Authenticated</h2>
                  <p className="text-center text-xs text-slate-500 mt-1 mb-6">Active Session Token verified via JWT Bearer</p>

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

      {/* PLAN CHANGE & PRORATION MODAL (Task 2) */}
      {isPlanChangeModalOpen && selectedSubForChange && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div>
                <h3 className="font-bold text-slate-900 text-base">Plan Change Screen</h3>
                <p className="text-xs text-slate-500">Upgrade or downgrade with fair mid-cycle proration</p>
              </div>
              <button
                onClick={() => setIsPlanChangeModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 text-lg"
              >
                &times;
              </button>
            </div>

            {planChangeError && (
              <div className="p-3 bg-rose-50 text-rose-700 text-xs rounded-xl border border-rose-200">
                {planChangeError}
              </div>
            )}

            {/* Current Plan Card */}
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex justify-between items-center">
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Current Plan
                </span>
                <div className="font-bold text-slate-900 text-sm">
                  {selectedSubForChange.plan ? selectedSubForChange.plan.name : 'Current Plan'}
                </div>
                <div className="text-xs text-slate-500">
                  Renewal: {new Date(selectedSubForChange.end_date).toLocaleDateString()}
                </div>
              </div>
              <div className="text-base font-bold text-slate-900 font-mono">
                ${selectedSubForChange.plan ? parseFloat(selectedSubForChange.plan.price).toFixed(2) : '0.00'}/month
              </div>
            </div>

            {/* Select New Plan */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                Select New Plan
              </label>
              <div className="space-y-2">
                {plans
                  .filter((p) => p.id !== selectedSubForChange.plan_id && p.is_active)
                  .map((p) => (
                    <label
                      key={p.id}
                      className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition ${
                        targetPlanId === p.id
                          ? 'border-indigo-600 bg-indigo-50/40 ring-1 ring-indigo-500'
                          : 'border-slate-200 hover:border-indigo-200 hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <input
                          type="radio"
                          name="target-plan"
                          value={p.id}
                          checked={targetPlanId === p.id}
                          onChange={() => handleTargetPlanSelect(p.id)}
                          className="text-indigo-600 focus:ring-indigo-500"
                        />
                        <div>
                          <div className="text-xs font-bold text-slate-800">{p.name}</div>
                          <div className="text-[10px] text-slate-400 capitalize">{p.billing_interval} billing</div>
                        </div>
                      </div>
                      <div className="text-xs font-mono font-bold text-slate-900">
                        ${parseFloat(p.price).toFixed(2)}/mo
                      </div>
                    </label>
                  ))}
              </div>
            </div>

            {/* Proration Preview (Before Confirming) */}
            {previewLoading ? (
              <div className="p-4 text-center text-xs text-slate-400">Calculating proration...</div>
            ) : prorationPreview ? (
              <div className="p-4 bg-indigo-50/70 rounded-xl border border-indigo-200 space-y-2.5">
                <div className="flex items-center justify-between border-b border-indigo-200 pb-2">
                  <span className="text-xs font-bold text-indigo-950 uppercase tracking-wider">
                    Plan Upgrade Summary
                  </span>
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-200 text-indigo-800 font-semibold">
                    {prorationPreview.proration.remaining_days} Days Remaining
                  </span>
                </div>

                <div className="space-y-1.5 text-xs text-slate-700">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-600">Unused Plan Credit:</span>
                    <span className="font-mono font-bold text-emerald-600">
                      -${parseFloat(prorationPreview.proration.unused_credit).toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-600">New Plan Charge:</span>
                    <span className="font-mono font-bold text-slate-900">
                      +${parseFloat(prorationPreview.proration.new_charge).toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center pt-2 border-t border-indigo-200 text-sm font-bold text-indigo-950">
                    <span>Amount Due:</span>
                    <span className="font-mono font-extrabold text-indigo-700">
                      ${parseFloat(prorationPreview.proration.net_amount_due).toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            ) : null}

            <div className="flex justify-end space-x-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsPlanChangeModalOpen(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={confirmLoading || !targetPlanId || !prorationPreview}
                onClick={handleConfirmPlanChange}
                className="px-4 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-sm transition disabled:opacity-50"
              >
                {confirmLoading ? 'Applying...' : 'Confirm Upgrade'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PROCESS PAYMENT MODAL (Task 3) */}
      {isProcessModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div>
                <h3 className="font-bold text-slate-900 text-base">💳 Process Payment</h3>
                <p className="text-xs text-slate-500">Simulate payment via mock gateway (80% success / 20% failure)</p>
              </div>
              <button
                onClick={() => { setIsProcessModalOpen(false); setProcessResult(null); setProcessError(''); }}
                className="text-slate-400 hover:text-slate-600 text-lg"
              >
                &times;
              </button>
            </div>

            {processResult ? (
              <div className={`p-4 rounded-xl border space-y-3 ${processResult.status === 'success' ? 'bg-emerald-50 border-emerald-200' : 'bg-rose-50 border-rose-200'}`}>
                <div className="flex items-center space-x-2">
                  <span className="text-xl">{processResult.status === 'success' ? '✅' : '❌'}</span>
                  <span className={`font-bold text-sm ${processResult.status === 'success' ? 'text-emerald-800' : 'text-rose-800'}`}>
                    Payment {processResult.status === 'success' ? 'Successful' : 'Failed'}
                  </span>
                </div>
                <div className="text-xs space-y-1.5 text-slate-700">
                  <div className="flex justify-between"><span className="text-slate-500">Transaction ID:</span><span className="font-mono font-bold">{processResult.payment_reference}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Amount:</span><span className="font-mono font-bold">₹{parseFloat(processResult.amount).toFixed(2)}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Invoice ID:</span><span className="font-mono">{processResult.invoice_id}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Webhook Event:</span><span className="font-semibold text-indigo-700">{processResult.webhook_event}</span></div>
                  {processResult.message && (
                    <div className="mt-2 text-[11px] text-slate-500 italic">{processResult.message}</div>
                  )}
                </div>
                <button
                  onClick={() => { setIsProcessModalOpen(false); setProcessResult(null); }}
                  className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold transition"
                >
                  Close
                </button>
              </div>
            ) : (
              <form onSubmit={handleProcessPaymentSubmit} className="space-y-4">
                {processError && (
                  <div className="p-3 bg-rose-50 text-rose-700 text-xs rounded-xl border border-rose-200">{processError}</div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Invoice ID</label>
                  <input
                    type="number"
                    min="1"
                    value={processInvoiceId}
                    onChange={(e) => setProcessInvoiceId(e.target.value)}
                    placeholder="e.g. 1"
                    required
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Amount (₹)</label>
                  <input
                    type="number"
                    min="0.01"
                    step="0.01"
                    value={processAmount}
                    onChange={(e) => setProcessAmount(e.target.value)}
                    placeholder="e.g. 499"
                    required
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-2">Simulation Mode</label>
                  <div className="space-y-2">
                    {[
                      { value: 'random', label: '🎲 Random (80% success, 20% fail)', badge: 'Default' },
                      { value: 'success', label: '✅ Force Success', badge: null },
                      { value: 'failure', label: '❌ Force Failure', badge: null }
                    ].map((opt) => (
                      <label
                        key={opt.value}
                        className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer text-xs transition ${
                          simulateMode === opt.value
                            ? 'border-emerald-500 bg-emerald-50/40 ring-1 ring-emerald-500'
                            : 'border-slate-200 hover:border-emerald-200 hover:bg-slate-50'
                        }`}
                      >
                        <div className="flex items-center space-x-2">
                          <input
                            type="radio"
                            name="sim-mode"
                            value={opt.value}
                            checked={simulateMode === opt.value}
                            onChange={() => setSimulateMode(opt.value)}
                            className="text-emerald-600"
                          />
                          <span className="text-slate-800 font-medium">{opt.label}</span>
                        </div>
                        {opt.badge && (
                          <span className="text-[10px] px-2 py-0.5 bg-slate-200 text-slate-600 rounded-full font-semibold">{opt.badge}</span>
                        )}
                      </label>
                    ))}
                  </div>
                </div>

                <div className="flex justify-end space-x-2 pt-2 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => { setIsProcessModalOpen(false); setProcessError(''); }}
                    className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={processLoading}
                    className="px-4 py-2 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl shadow-sm transition disabled:opacity-50"
                  >
                    {processLoading ? 'Processing...' : 'Process Payment'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* PAYMENT DETAILS MODAL (Task 3) */}
      {selectedPayment && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div>
                <h3 className="font-bold text-slate-900 text-base">Payment Details</h3>
                <p className="text-xs text-slate-500">Transaction record and status</p>
              </div>
              <button onClick={() => setSelectedPayment(null)} className="text-slate-400 hover:text-slate-600 text-lg">&times;</button>
            </div>
            <div className="space-y-2.5 text-sm">
              {[
                { label: 'Invoice No', value: selectedPayment.invoice_number || `INV-${selectedPayment.invoice_id}`, mono: true },
                { label: 'Amount', value: `₹${parseFloat(selectedPayment.amount).toFixed(2)}`, mono: true },
                { label: 'Status', value: selectedPayment.status },
                { label: 'Transaction ID', value: selectedPayment.payment_reference || selectedPayment.id, mono: true },
                { label: 'Date of Payment', value: selectedPayment.created_at ? new Date(selectedPayment.created_at).toLocaleString() : '-' },
              ].map(({ label, value, mono }) => (
                <div key={label} className="flex justify-between items-center py-2 border-b border-slate-100 last:border-0">
                  <span className="text-slate-500 text-xs font-medium">{label}:</span>
                  <span className={`${mono ? 'font-mono font-bold text-slate-900' : 'font-semibold text-slate-800'} text-xs`}>{value}</span>
                </div>
              ))}
            </div>
            <button
              onClick={() => setSelectedPayment(null)}
              className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
            >
              Close
            </button>
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
