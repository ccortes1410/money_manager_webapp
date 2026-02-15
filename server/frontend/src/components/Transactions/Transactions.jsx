import React, { useContext, useEffect, useState, useMemo } from 'react';
import { useNavigate } from "react-router-dom";
import { AuthContext } from '../../AuthContext';
import TransactionModal from './TransactionModal';
import "./Transactions.css";

const Transactions = () => {
    const [ transactions, setTransactions ] = useState([]);
    const [ loading, setLoading ] = useState(true);
    const [ showModal, setShowModal ] = useState(false);
    const [ editingTransaction, setEditingTransaction ] = useState(null);
    const [ selectedTransactions, setSelectedTransactions ] = useState([]);
    const [ searchQuery, setSearchQuery ] = useState("");
    const [ filter, setFilter ] = useState("all");
    const [ sortConfig, setSortConfig ] = useState({ key: 'date', direction: 'desc' });

    const { user } = useContext(AuthContext);
    const navigate = useNavigate();  

    const getToday = () => {
        const today = new Date();
        return today.toISOString().split('T')[0];
    }

    const transaction_url = "/djangoapp/transactions";

    const fetchTransactions = async () => {
        try {
            const res = await fetch(transaction_url, {
                method: 'GET',
                credentials: 'include'
            });

            const data = await res.json();
            if (data.transactions) {
                setTransactions(data.transactions);
            } else {
                setTransactions([]);
            }
        } catch (error) {
            console.error("Error fetching transactions:", error);
            setTransactions([]);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (transactionData) => {
        try {
            const res = await fetch(transaction_url+`/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(transactionData),
                credentials: 'include'
            });

            if (res.ok) {
                fetchTransactions();
                setShowModal(false);
            } else {
                console.error("Failed to add transaction");
            }
        } catch (error) {
            console.error("Error adding transaction:", error);
        }
    };

    const handleUpdate = async (id, transactionData) => {
        try{
            const res = await fetch(transaction_url+`/${id}/update`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(transactionData),
                credentials: 'include'
            });

            if (res.ok) {
                fetchTransactions();
                setShowModal(false);
                setEditingTransaction(null);
            } 
        } catch (error) {
            console.error("Error updating transaction:", error);
        }
    };

    const handleDelete = async () => {
        if (selectedTransactions.length === 0) return;
        if (!window.confirm(`Delete ${selectedTransactions.length} transaction(s)?`)) return;
        
        try {
            const res = await fetch(transaction_url+`/delete`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ ids: selectedTransactions })
            });

            if (res.ok) {
                fetchTransactions();
                setSelectedTransactions([]);
            } else {
                alert("Failed to delete transactions");
            }
        } catch (error) {
            console.error("Error deleting transactions:", error);
        }
    }

    const handleSelectTransaction = (transactionId) => {
        setSelectedTransactions((prev) => {
            // If already selected, remove it
            if (prev.includes(transactionId)) {
            return prev.filter((id) => id !== transactionId);
            }
            // Otherwise, add it
            return [...prev, transactionId];
        });
    };

    const handleSelectAll = () => {
        if (selectedTransactions.length === filteredAndSortedTransactions.length) {
            setSelectedTransactions([]);
        } else {
            setSelectedTransactions(filteredAndSortedTransactions.map(tx => tx.id));
        }
    };

    const handleEdit = (transaction) => {
        setEditingTransaction(transaction);
        setShowModal(true);
    }

    const handleSort = (key) => {
        setSortConfig(prev => ({
            key,
            direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
        }));
    };

    const categories = useMemo(() => {
        const cats = [...new Set(transactions.map(tx => tx.category))];
        return cats.filter(Boolean).sort();
    }, [transactions]);

    const filteredAndSortedTransactions = useMemo(() => {
        let result = [...transactions];

        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            result = result.filter(tx =>
                tx.description?.toLowerCase().includes(query) ||
                tx.category?.toLowerCase().includes(query) ||
                tx.amount?.toString().includes(query) ||
                tx.date?.includes(query)
            );
        }

        if (filter !== "all") {
            result = result.filter(tx => tx.category === filter);
        }

        // Apply sorting
        result.sort((a ,b) => {
            let aVal = a[sortConfig.key];
            let bVal = b[sortConfig.key];

            // Handle numeric sorting for amount
            if (sortConfig.key === 'amount') {
                aVal = parseFloat(aVal);
                bVal = parseFloat(bVal);
            }

            // Handle date sorting
            if (sortConfig.key === 'date') {
                aVal = new Date(aVal);
                bVal = new Date(bVal);
            }

            if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
            return 0;
        });

        return result;
    }, [transactions, searchQuery, filter, sortConfig]);

    // Calculate totals
    const totals = useMemo(() => {
        const total = transactions.reduce((sum, tx) => sum + parseFloat(tx.amount || 0), 0);
        const filteredTotal = filteredAndSortedTransactions.reduce(
            (sum, tx) => sum + parseFloat(tx.amount || 0), 0
        );
        const thisMonth = transactions.filter(tx => {
            const txDate = new Date(tx.date);
            const now = new Date();
            return txDate.getMonth() === now.getMonth() &&
                   txDate.getFullYear() === now.getFullYear();
        }).reduce((sum, tx) => sum + parseFloat(tx.amount || 0), 0);

        return {
            total,
            filteredTotal,
            thisMonth,
            count: transactions.length,
            filteredCount: filteredAndSortedTransactions.length
        };
    }, [transactions, filteredAndSortedTransactions]);

    useEffect(() => {
        fetchTransactions();
    }, []);

    useEffect(() => {
        if (user !== null && !user.is_authenticated) {
            navigate("/");
        }
    }, [user, navigate]);

    // Sort indicator component
    const SortIndicator = ({ columnKey}) => {
        if (sortConfig.key !== columnKey) return <span className="sort-icon">↕</span>;
        return <span className="sort-icon active">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
    };

    return (
        <div className="transactions-page">
            {/* Header */}
            <div className="transactions-header">
            <h1>Transactions</h1>
            <button
                className="transactions-add-btn"
                onClick={() => {
                    setEditingTransaction(null);
                    setShowModal(true);
                }}
            >
                + Add Transaction
            </button>
            </div>

            {/* Summary Cards */}
            <div className="transactions-summary">
                <div className="tx-summary-card total">
                    <span className="label">Total Spent</span>
                    <span className="value">${totals.total.toFixed(2)}</span>
                </div>
                <div className="tx-summary-card month">
                    <span className="label">This Month</span>
                    <span className="value">${totals.thisMonth.toFixed(2)}</span>
                </div>
                <div className="tx-summary-card count">
                    <span className="label">Transactions</span>
                    <span className="value">{totals.count}</span>
                </div>
                <div className="tx-summary-card filtered">
                    <span className="label">Showing</span>
                    <span className="value">
                        {totals.filteredCount} (${totals.filteredTotal.toFixed(2)})
                    </span>
                </div>
            </div>

            {/* Search and Filters */}
            <div className="transactions-controls">
                <div className="search-box">
                    <span className="search-icon">🔍</span>
                    <input
                        type="text"
                        placeholder="Search transactions..."
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
                        className="category-filter"
                    >
                        <option value="all">All Categories</option>
                        {categories.map(cat => (
                            <option key={cat} value={cat}>{cat}</option>
                        ))}
                    </select>

                    {selectedTransactions.length > 0 && (
                        <button
                            className="delete-selected-btn"
                            onClick={handleDelete}
                        >
                            🗑️ Delete ({selectedTransactions.length})
                        </button>
                    )}
                </div>
            </div>

            {/* Transactions Table */}
            <div className="transactions-table-container">
                {loading ? (
                    <div className="loading-state">Loading transactions...</div>
                ) : filteredAndSortedTransactions.length === 0 ? (
                    <div className="empty-state">
                        {searchQuery || filter !== "all"
                            ? "No tranasctions match your filters."
                            : "No transactions yet. Add your first one!"}
                    </div>
                ) : (
                    <table className="transactions-table">
                        <thead>
                            <tr>
                                <th className="checkbox-col">
                                    <input
                                        type="checkbox"
                                        checked={
                                            selectedTransactions.length ===
                                            filteredAndSortedTransactions.length &&
                                            filteredAndSortedTransactions.length > 0
                                        }
                                        onChange={handleSelectAll}
                                    />
                                </th>
                                <th 
                                    className="sortable"
                                    onClick={() => handleSort('date')}
                                >
                                    Date <SortIndicator columnKey="date" />
                                </th>
                                <th
                                    className="sortable"
                                    onClick={() => handleSort('description')}
                                >
                                    Description <SortIndicator columnKey="description" />
                                </th>
                                <th
                                    className="sortable"
                                    onClick={() => handleSort('category')}
                                >
                                    Cateogry <SortIndicator columnKey="category" />
                                </th>
                                <th
                                    className="sortable amount-col"
                                    onClick={() => handleSort('amount')}
                                >
                                    Amount <SortIndicator columnKey="amount" />
                                </th>
                                <th className="actions-col">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredAndSortedTransactions.map((tx) => (
                                <tr
                                    key={tx.id}
                                    className={selectedTransactions.includes(tx.id) ? "selected" : ""}
                                >
                                    <td className="checkbox-col">
                                        <input 
                                            type="checkbox"
                                            checked={selectedTransactions.includes(tx.id)}
                                            onChange={() => handleSelectTransaction(tx.id)}
                                        />
                                    </td>
                                    <td className="date-col">{tx.date}</td>
                                    <td className="description-col">{tx.description || '-'}</td>
                                    <td className="category-col">
                                        <span className="category-badge">{tx.category}</span>
                                    </td>
                                    <td className="amount-col">${parseFloat(tx.amount).toFixed(2)}</td>
                                    <td className="actions-col">
                                        <button
                                            className="edit-btn"
                                            onClick={() => handleEdit(tx)}
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
                                <td colSpan="4" className="total-label">
                                    Total ({filteredAndSortedTransactions.length} transactions)
                                </td>
                                <td className="total-amount">
                                    ${totals.filteredTotal.toFixed(2)}
                                </td>
                                <td></td>
                            </tr>
                        </tfoot>
                    </table>
                )}
            </div>

            {/* Modal */}
            {showModal && (
                <TransactionModal
                    transaction={editingTransaction}
                    categories={categories}
                    onClose={() => {
                        setShowModal(false);
                        setEditingTransaction(null);
                    }}
                    onSave={(data) => {
                        if (editingTransaction) {
                            handleUpdate(editingTransaction.id, data);
                        } else {
                            handleCreate(data);
                        }
                    }}
                />
            )}
        </div>
    );
};

export default Transactions;