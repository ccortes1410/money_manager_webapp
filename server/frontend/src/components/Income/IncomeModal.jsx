import React, { useState, useEffect } from 'react';

const IncomeModal = ({ income, sources, onClose, onSave }) => {
    const getToday = () => new Date().toISOString().split('T')[0];

    const [ formData, setFormData ] = useState({
        amount: '',
        source: '',
        date_received: getToday(),
        period_start: '',
        period_end: '',
    });

    const [ errors, setErrors ] = useState({});

    const safeSourcesList = Array.isArray(sources) ? sources : [];

    useEffect(() => {
        if (income) {
            setFormData({
                amount: income.amount || '',
                source: income.source || '',
                date_received: income.date_received || getToday(),
                period_en: income.period_end || '',
            });
        }
    }, [income]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));

        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: ''}));
        }
    };

    const validate = () => {
        const newErrors = {};

        if (!formData.amount || parseFloat(formData.amount) <= 0) {
            newErrors.amount = 'Please enter a valid amount';
        }
        if (!formData.source.trim()) {
            newErrors.source = 'Source is required';
        }
        if (!formData.date_received) {
            newErrors.date_received = 'Date received is required';
        }
        if (!formData.period_start) {
            newErrors.period_start = 'Period start is required';
        }
        if (!formData.period_end) {
            newErrors.period_end = 'Period end is required';
        }
        if (formData.period_start && formData.period_end &&
            new Date(formData.period_end) < new Date(formData.period_start)) {
                newErrors.period_end = 'End date cannot be before start date';
        }
        
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!validate()) return;

        onSave({
            ...formData,
            amount: parseFloat(formData.amount),
        });
    };

    const setThisMonthPeriod = () => {
        const now = new Date();
        const start = new Date(now.getFullYear(), now.getMonth(), 1);
        const end = new Date(now.getFullYear(), now.getMonth() +1, 0);

        setFormData(prev => ({
            ...prev,
            period_start: start.toISOString().split('T')[0],
            period_end: end.toISOString().split('T')[0],
        }));
    };

    const setLastMonthPeriod = () => {
        const now = new Date();
        const start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        const end =new Date(now.getFullYear(), now.getMonth(), 0);

        setFormData(prev => ({
            ...prev,
            period_start: start.toISOString().split('T')[0],
            period_end: end.toISOString().split('T')[0],
        }));
    };

    const setBiweeklyPeriod = () => {
        const now = new Date();
        const start = new Date(now);
        const end = new Date(now)
        end.setDate(end.getDate() + 13);

        setFormData(prev => ({
            ...prev,
            period_start: start.toISOString().split('T')[0],
            period_end: end.toISOString().split('T')[0],
        }));
    };

    const setWeeklyPeriod = () => {
        const now = new Date();
        const start = new Date(now);
        const end = new Date(now)
        end.setDate(end.getDate() + 6);

        setFormData(prev => ({
            ...prev,
            period_start: start.toISOString().split('T')[0],
            period_end: end.toISOString().split('T')[0],
        }));
    };

    const getPeriodDuration = () => {
        if (!formData.period_start || !formData.period_end) return null;
        
        const start = new Date(formData.period_start);
        const end = new Date(formData.period_end);
        const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;
        
        if (days < 0) return 'Invalid period';
        if (days === 1) return '1 day';
        if (days < 7) return `${days} days`;
        if (days === 7) return '1 week';
        if (days < 30) return `${days} days (${(days / 7).toFixed(1)} weeks)`;
        if (days >= 28 && days <= 31) return '~1 month';
        return `${days} days (~${(days / 30).toFixed(1)} months)`;
    };

    const periodDuration = getPeriodDuration();

    return (
        <div className="income-modal-overlay" onClick={onClose}>
            <div className="income-modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="income-modal-header">
                    <h2>{income ? 'Edit Income' : 'Add Income'}</h2>
                    <button className="income-modal-close-btn" onClick={onClose}>×</button>
                </div>

                <form onSubmit={handleSubmit} className="income-modal-form">
                    {/* Amount */}
                    <div className="income-form-group">
                        <label htmlFor="amount">Amount *</label>
                        <div className="input-with-prefix">
                            <span className="input-prefix">$</span>
                            <input
                                type="number"
                                id="amount"
                                name="amount"
                                value={formData.amount}
                                onChange={handleChange}
                                placeholder="0.00"
                                step="0.01"
                                min="0"
                                className={errors.amount ? 'error' : ''}
                            />
                        </div>
                        {errors.amount && <span className="error-message">{errors.amount}</span>}
                    </div>

                    {/* Source */}
                    <div className="income-form-group">
                        <label htmlFor="source">Source *</label>
                        <input
                            type="text"
                            id="source"
                            name="source"
                            value={formData.source}
                            onChange={handleChange}
                            placeholder="e.g., Salary, Freelance, Dividends"
                            list="source-suggestions"
                            className={errors.source ? 'error' : ''}
                        />
                        {safeSourcesList.length > 0 && (
                        <datalist id="source-suggestions">
                            {safeSourcesList.map(src => (
                                <option key={src} value={src} />
                            ))}
                        </datalist>
                        )}
                        {errors.source && <span className="error-message">{errors.source}</span>}
                    </div>

                    {/* Date Received */}
                    <div className="income-form-group">
                        <label htmlFor="date_received">Date Received *</label>
                        <input
                            type="date"
                            id="date_received"
                            name="date_received"
                            value={formData.date_received}
                            onChange={handleChange}
                            className={errors.date_received ? 'error' : ''}
                        />
                        {errors.date_received && <span className="error-message">{errors.date_received}</span>}
                    </div>

                    {/* Period Presets */}
                    <div className="income-form-group">
                        <label>Period (what this income covers) *</label>
                        <div className="period-presets">
                            <button
                                type="button"
                                className="preset-btn"
                                onClick={setThisMonthPeriod}
                            >
                                This Month
                            </button>
                            <button
                                type="button"
                                className="preset-btn"
                                onClick={setLastMonthPeriod}
                            >
                                Last Month
                            </button>
                            <button
                                type="button"
                                className="preset-btn"
                                onClick={setBiweeklyPeriod}
                            >
                                Bi-weekly
                            </button>
                            <button
                                type="button"
                                className="preset-btn"
                                onClick={setWeeklyPeriod}
                            >
                                Weekly
                            </button>
                        </div>
                    </div>

                    {/* Period Start & End */}
                    <div className="income-form-row">
                        <div className="income-form-group">
                            <label htmlFor="period_start">Period Start *</label>
                            <input
                                type="date"
                                id="period_start"
                                name="period_start"
                                value={formData.period_start}
                                onChange={handleChange}
                                className={errors.period_start ? 'error' : ''}
                            />
                            {errors.period_start && <span className="error-message">{errors.period_start}</span>}
                        </div> 

                        <div className="income-form-group">
                            <label htmlFor="period_end">Period End *</label>
                            <input
                                type="date"
                                id="period_end"
                                name="period_end"
                                value={formData.period_end}
                                onChange={handleChange}
                                className={errors.period_end ? 'error' : ''}
                            />
                            {errors.period_end && <span className="error-message">{errors.period_end}</span>}
                        </div>
                    </div>

                    {/* Period Summary */}
                    {periodDuration && (
                        <div className="income-period-summary">
                            <span className="income-period-summary-label">Period Duration:</span>
                            <span className="income-period-summary-value">
                                {periodDuration}
                            </span>
                        </div>
                    )}

                    {/* Actions */}
                    <div className="income-modal-actions">
                        <button type="button" className="income-cancel-btn" onClick={onClose}>
                            Cancel
                        </button>
                        <button type="submit" className="income-save-btn">
                            {income ? 'Update Income' : 'Add Income'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default IncomeModal;