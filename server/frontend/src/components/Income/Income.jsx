import React, { useRef, useState, useEffect, useContext, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../../AuthContext";
import IncomeModal from './IncomeModal';
import "./Income.css";

const Income = () => {
    const [ income, setIncome ] = useState([]);
    const [ summary, setSummary ] = useState({
        total_income: 0,
        total_spent: 0,
        transaction_spent: 0,
        subscription_spent: 0,
        remaining: 0,
        percent_remaining: 0,
        is_negative: false,
        this_month: {
            income: 0,
            spent: 0,
            transaction_spent: 0,
            subscription_spent: 0,
            remaining: 0,
            percent_remaining: 0,
            is_negative: false,
        }
    });
    const [ bySource, setBySource ] = useState([]);
    const [ loading, setLoading ] = useState(true);
    const [ showModal, setShowModal ] = useState(false);
    const [ editingIncome, setEditingIncome ] = useState(null);
    const [ selectedIncome, setSelectedIncome ] = useState(null);
    const [ selectedIncomeIds, setSelectedIncomeIds ] = useState([]);
    const [ filter, setFilter ] = useState("all");
    const [ searchQuery, setSearchQuery ] = useState("");

    const { user } = useContext(AuthContext);
    const navigate = useNavigate();
    const monthsRefs = useRef({}); 
    
    const income_url = "/djangoapp/incomes";

    // Fetch income data for the logged-in user
    const fetchIncome = async () => {
        try {
            const res = await fetch(income_url, {
                method: "GET",
                credentials: "include",
            });

            const data = await res.json();
            if (data.incomes && Array.isArray(data.incomes)) {
                setIncome(data.incomes);
            } else {
                setIncome([]);
            }

            if (data.summary) {
                setSummary(data.summary)
            }

            if (data.by_source) {
                setBySource(data.by_source)
            }
        } catch (error) {
            console.error("Error fetching income data:", error);
            setIncome([]);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (incomeData) => {
        try {
            const res = await fetch(income_url+`/create`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(incomeData),
            });

            const data = await res.json();

            if (res.ok) {
                fetchIncome();
                setShowModal(false);
            } else {
                console.error("Error adding income:", data.error);
                alert(data.error || "Faile to add income");
            }
        } catch (error) {
            console.error("Error adding income:", error);
        }
    };

    const handleUpdate = async (id, incomeData) => {
        try {
            const res = await fetch(income_url+`/${id}/update`, {
                method: "PATCH",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(incomeData),
            });

            const data = await res.json();

            if (res.ok) {
                fetchIncome();
                setShowModal(false);
                setEditingIncome(null);
            } else {
                console.error("Error updating income:", data.error);
                alert(data.error || "Failed to update income");
            }
        } catch (error) {
            console.error("Error updating income:", error);
        }
    };

    const handleDelete = async () => {
        if (selectedIncomeIds.length === 0) return;
        if (!window.confirm(`Delete ${selectedIncomeIds.length} income record(s)?`)) return;

        try {
            const res = await fetch(income_url+`delete`, {
                method: 'DELETE',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ income_ids: selectedIncomeIds }),
            });

            const data = await res.json();

            if (res.ok) {
                fetchIncome();
                setSelectedIncomeIds([]);
                setSelectedIncome(null);
            } else {
                alert(data.error || "Failed to delete income");
            }
        } catch (error) {
            console.error("Error deleting income:", error);
        }
    };

    const handleToggleSelect = (incomeId) => {
        setSelectedIncomeIds(prev => {
            if (prev.includes(incomeId)) {
                return prev.filter(id => id !== incomeId);
            }
            return [...prev, incomeId];
        });
    };

    const handleSelectAll = () => {
        if(selectedIncomeIds.length === filteredIncome.length) {
            setSelectedIncomeIds([]);
        } else {
            setSelectedIncomeIds(filteredIncome.map(inc => inc.id));
        }
    };

    const handleSelectForCalendar = (inc) => {
        setSelectedIncome(prev => prev?.id === inc.id ? null : inc);
    };

    const handleEdit = (inc) => {
        setEditingIncome(inc);
        setShowModal(true);
    };

    const sources = useMemo(() => {
        return bySource.map(item => item.source);
    }, [bySource]);

    const filteredIncome = useMemo(() => {
        let result = [...income];

        if (searchQuery) {
            const query = searchQuery.toLocaleLowerCase();
            result = result.filter(inc =>
                inc.source?.toLocaleLowerCase().includes(query) ||
                inc.amount?.toString().includes(query) ||
                inc.date_received?.includes(query)
            );
        }

        if (filter !== "all") {
            result = result.filter(inc => inc.source === filter);
        }

        return result;
    }, [income, searchQuery, filter]);

    const filteredTotal = useMemo(() => {
        return filteredIncome.reduce((sum, inc) => sum + parseFloat(inc.amount || 0), 0);
    }, [filteredIncome]);

    const calendarYears = useMemo(() => {
        if (!income.length) {
            const currentYear = new Date().getFullYear();
            return [currentYear - 1, currentYear, currentYear + 1];
        }

        const years = income.flatMap(inc => {
            const startYear = new Date(inc.period_start).getFullYear();
            const endYear = new Date(inc.period_end).getFullYear();
            return [startYear, endYear];
        }).filter(y => !isNaN(y));

        if (!years.length) {
            const currentYear = new Date().getFullYear();
            return [currentYear - 1, currentYear, currentYear + 1];
        }

        const minYear = Math.min(...years);
        const maxYear = Math.max(...years);

        return Array.from({ length: maxYear - minYear + 1 }, (_, i) => minYear + i);
    }, [income]);

    const MONTHS = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];


    const isMonthInPeriod = (year, monthIndex) => {
        if (!selectedIncome) return false;

        const start = new Date(selectedIncome.period_start);
        const end = new Date(selectedIncome.period_end);

        const monthStart = new Date(year, monthIndex, 1);
        const monthEnd = new Date(year, monthIndex + 1, 0);

        return monthStart <= end && monthEnd >= start;
    };

    const isCurrentMonth = (year, monthIndex) => {
        const now = new Date();
        return year === now.getFullYear() && monthIndex === now.getMonth();
    };

    useEffect(() => {
        if (!selectedIncome) return;

        const start = new Date(selectedIncome.period_start);
        const key = `${start.getFullYear()}-${start.getMonth()}`;
        const el = monthsRefs.current[key];

        if (el) {
            el.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    }, [selectedIncome]);

    useEffect(() => {
        fetchIncome();
    }, []);

    useEffect(() => {
        if (user !== null && !user.is_authenticated) {
            navigate("/");
        }
    }, [user]);

    const formatCurrency = (value) => {
        const num = parseFloat(value) || 0;
        return num.toFixed(2);
    };

    return (
        <div className="income-page">
            {/* Header */}
            <div className="income-header">
                <h1>Income</h1>
                <button
                    className="income-add-btn"
                    onClick={() => {
                        setEditingIncome(null);
                        setShowModal(true);
                    }}
                >
                    + Add Income
                </button>
            </div>

            {/* Summary Cards */}
            <div className="income-summary">
                <div className="inc-summary-card total-income">
                    <span className="label">Total Income</span>
                    <span className="value">${formatCurrency(summary.total_income)}</span>
                </div>
                <div className="inc-summary-card this-month">
                    <span className="label">This Month Income</span>
                    <span className="value">${formatCurrency(summary.this_month)}</span>
                </div>
                <div className="inc-summary-card spent">
                    <span className="label">Total Spent</span>
                    <span className="value">${formatCurrency(summary.total_spent)}</span>
                    <div className="inc-breakdown">
                        <span className="inc-breakdown-item">
                            <span className="inc-breakdown-dot transactions"></span>
                            Transactions: ${formatCurrency(summary.transaction_spent)}
                        </span>
                        <span className="inc-breakdown-item">
                            <span className="inc-breakdown-dot subscriptions"></span>
                            Susbcriptions: ${formatCurrency(summary.subscription_spent)}
                        </span>
                    </div>
                </div>
                <div className="inc-summary-card remaining">
                    <span className="label">Remaining</span>
                    <span className={`value ${summary.is_negative ? 'negative' : ''}`}>
                        ${formatCurrency(summary.remaining)}
                    </span>
                    <span className="inc-percent">
                        {summary.percent_remaining?.toFixed(1) || 0}% of income
                    </span>
                </div>
            </div>

            {/* This Month Summary */}
            <div className="inc-this-month-summary">
                <h3>This Month Overview</h3>
                <div className="inc-this-month-cards">
                    <div className="mini-card">
                        <span className="mini-label">Income</span>
                        <span className="mini-value positive">
                            ${formatCurrency(summary.this_month?.income)}
                        </span>
                    </div>
                    <div className="mini-card">
                        <span className="mini-label">Transactions</span>
                        <span className="mini-value negative">
                            ${formatCurrency(summary.this_month?.transaction_spent)}
                        </span>
                    </div>
                    <div className="mini-card">
                        <span className="mini-label">Subscriptions</span>
                        <span className="mini-value negative">
                            ${formatCurrency(summary.this_month?.subscription_spent)}
                        </span>
                    </div>
                    <div className="mini-card">
                        <span className="mini-label">Remaining</span>
                        <span className={`mini-value ${summary.this_month?.is_negative ? 'negative' : 'positive'}`}>
                            ${formatCurrency(summary.this_month?.remaining)}
                        </span>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="income-content">
                {/* Left: Calendar */}
                <div className="income-calendar-panel">
                    <h2>Income Calendar</h2>
                    <p className="calendar-hint">
                        {selectedIncome
                            ? `Showing: ${selectedIncome.source}`
                            : "Select an income to highlight its period"}
                    </p>

                    <div className="calendar-container">
                        {calendarYears.map(year => (
                            <div key={year} className="calendar-year">
                                <div className="year-label">{year}</div>
                                <div className="months-grid">
                                    {MONTHS.map((month, index) => {
                                        const isHighlighted = isMonthInPeriod(year, index);
                                        const isCurrent = isCurrentMonth(year, index);

                                        return (
                                            <div 
                                                key={`${year}-${index}`}
                                                ref={el => {
                                                    if (el) monthsRefs.current[`${year}-${index}`] = el;
                                                }}
                                                className={`month-cell
                                                    ${isHighlighted ? 'highlighted' : ''}
                                                    ${isCurrent ? 'current' : ''}`}
                                            >
                                                {month}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Spending Breakdown */}
                    <div className="spending-breakdown-section">
                        <h3>Spending Breakdown</h3>
                        <div className="breakdown-bars">
                            <div className="breakdown-bar-item">
                                <div className="breakdown-bar-header">
                                    <span className="breakdown-bar-label">Transactions</span>
                                    <span className="breakdown-bar-value">
                                        ${formatCurrency(summary.transaction_spent)}
                                    </span>
                                </div>
                                <div className="breakdown-bar">
                                    <div 
                                        className="breakdown-bar-fill transactions"
                                        style={{
                                            width: `${summary.total_spent > 0
                                                ? ((summary.transaction_spent || 0) / summary.total_spent) * 100
                                                : 0}%`
                                        }}
                                    />
                                </div>
                            </div>
                            <div className="breakdown-bar-item">
                                <div className="breakdown-bar-header">
                                    <span className="breakdown-bar-label">Subscriptions</span>
                                    <span className="breakdown-bar-value">
                                        ${formatCurrency(summary.subscription_spent)}
                                    </span>
                                </div>
                                <div className="breakdown-bar">
                                    <div
                                        className="breakdown-bar-fill subscriptions"
                                        style={{
                                            width: `${summary.total_spent > 0
                                                ? ((summary.subscription_spent || 0) / summary.total_spent) * 100
                                                : 0}%`
                                        }}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Income by Source */}
                    {bySource.length > 0 && (
                        <div className="income-by-source">
                            <h3>Income by Source</h3>
                            <ul className="source-list">
                                {bySource.map(item => (
                                    <li key={item.source} className="source-item">
                                        <span className="source-name">{item.source}</span>
                                        <span className="source-amount">
                                            ${formatCurrency(item.total)}
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>

                {/* Funds Progress Bar */}
                <div className="income-progress-divider">
                    <div className="inc-progress-bar-vertical">
                        <div
                            className={`inc-progress-fill ${summary.is_negative ? 'negative' : ''}`}
                            style={{ height: `${Math.min(Math.max(summary.percent_remaining || 0, 0), 100)}%`}}
                        />
                    </div>
                    <span className="inc-progress-label">
                        {(summary.percent_remaining || 0).toFixed(1)}%
                    </span>
                    <span className="inc-progress-sublabel">remaining</span>
                </div>

                {/* Right: Income Table */}
                <div className="income-table-panel">
                    {/* Controls */}
                    <div className="income-controls">
                        <div className="search-box">
                            <span className="search-icon">🔍</span>
                            <input
                                type="text"
                                placeholder="Search income..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                            {searchQuery && (
                                <button
                                className="clear-search"
                                onClick={() => setSearchQuery("")}
                                >
                                    ✕
                                </button>
                            )}
                        </div>

                        <div className="filter-controls">
                            <select
                                value={filter}
                                onChange={(e) => setFilter(e.target.value)}
                                className="source-filter"
                            >
                                <option value="all">All Sources</option>
                                {sources.map(source => (
                                    <option key={source} value={source}>{source}</option>
                                ))}
                            </select>

                            {selectedIncomeIds.length > 0 && (
                                <button
                                    className="delete-selected-btn"
                                    onClick={handleDelete}
                                >
                                    🗑️ Delete ({selectedIncomeIds.length})
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Table */}
                    <div className="income-table-container">

                        {loading ? (
                            <div className="loading-state">Loading income data...</div>
                        ) : filteredIncome.length === 0 ? (
                            <div className="empty-state">
                                {searchQuery || filter !== "all"
                                    ? "No income matches your filters."
                                    : "No income records yet. Add your first one!"}
                            </div>
                        ) : (
                            <table className="income-table">
                                <thead>
                                    <tr>
                                        <th className="checkbox-col">
                                            <input
                                                type="checkbox"
                                                checked={
                                                    selectedIncomeIds.length === filteredIncome &&
                                                    filteredIncome.length > 0
                                                }
                                                onChange={handleSelectAll}
                                            />
                                        </th>
                                        <th>Source</th>
                                        <th>Amount</th>
                                        <th>Date Received</th>
                                        <th>Period</th>
                                        <th className="actions-col">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredIncome.map(inc => (
                                        <tr
                                            key={inc.id}
                                            className={`
                                                ${selectedIncomeIds.includes(inc.id) ? 'selected' : ''}
                                                ${selectedIncome?.id === inc.id ? 'highlighted' : ''}
                                                `}
                                        >
                                            <td className="checkbox-col">
                                                <input
                                                    type="checkbox"
                                                    checked={selectedIncomeIds.includes(inc.id)}
                                                    onChange={() => handleToggleSelect(inc.id)}
                                                />
                                            </td>
                                            <td className="source-col">
                                                <span className="source-badge">{inc.source}</span>
                                            </td>
                                            <td clasName="amount-col">
                                                ${formatCurrency(inc.amount)}
                                            </td>
                                            <td className="date-col">{inc.date_received}</td>
                                            <td className="period-col">
                                                <span className="period-text">
                                                    {inc.period_start} → {inc.period_end}
                                                </span>
                                            </td>
                                            <td className="actions-col">
                                                <button
                                                    className="calendar-btn"
                                                    onClick={() => handleSelectForCalendar(inc)}
                                                    title="Show in Calendar"
                                                >
                                                    📅
                                                </button>
                                                <button
                                                    className="edit-btn"
                                                    onClick={() => handleEdit(inc)}
                                                    title="Edit"
                                                >
                                                    ✏️
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                                <tfoot>
                                    <tr>
                                        <td colSpan="2" className="total-label">
                                            Total ({filteredIncome.length} records)
                                        </td>
                                        <td className="total-amount">
                                            ${formatCurrency(filteredTotal)}
                                        </td>
                                        <td colSpan="3"></td>
                                    </tr>
                                </tfoot>
                            </table>
                        )}
                    </div>
                </div>
            </div>

            {/* Modal*/}
            {showModal && (
                <IncomeModal
                    income={editingIncome}
                    sources={sources}
                    onClose={() => {
                        setShowModal(false);
                        setEditingIncome(null);
                    }}
                    onSave={(data) => {
                        if (editingIncome) {
                            handleUpdate(editingIncome.id, data);
                        } else {
                            handleCreate(data);
                        }
                    }}
                />
            )}
        </div>
    )
}

export default Income;

