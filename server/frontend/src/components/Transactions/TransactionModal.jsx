import React, { useState, useEffect } from 'react';

const TransactionModal = ({ transaction, cateogries, onClose, onSave }) => {
    const getToday = () => new Date().toISOString().split('T')[0];

    const [ formData, setFormData ] = useState({
        amount: '',
        description: '',
        category: '',
        date: getToday(),
    });

    const [ errors, setErrors ] = useState({});

    useEffect(() => {
        if (transaction) {
            setFormData({
                amount: transaction.amount || '',
                description: transaction.description || '',
                category: transaction.category || '',
                date: transaction.date || getToday(),
            });
        }
    }, [transaction]);

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
        if (!formData.category.trim()) {
            newErrors.category = 'Category is required';
        }
        if (!formData.date) {
            newErrors.date = 'Date is required';
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
            description: formData.description || 'General',
        });
    };

    return (
        <div className="tx-modal-overlay" onClick={onClose}>
            <div className="tx-modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="tx-modal-header">
                    <h2>{transaction ? 'Edit Transaction' : 'Add Transaction'}</h2>
                    <button className="tx-modal-close-btn" onClick={onClose}>×</button>
                </div>

                <form onSubmit={handleSubmit} className="tx-modal-form">
                    <div className="tx-form-group">
                        <label htmlFor="amount">Amount *</label>
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
                            required
                        />
                        {errors.amount && <span className="error-message">{errors.amount}</span>}
                    </div>

                    <div className="tx-form-group">
                        <label htmlFor="description">Description</label>
                        <input
                            type="text"
                            id="description"
                            name="description"
                            value={formData.description}
                            onChange={handleChange}
                            placeholder="What was this for?"
                        />
                    </div>

                    <div className="tx-form-group">
                        <label htmlFor="category">Category *</label>
                        <input
                            type="text"
                            id="category"
                            name="category"
                            value={formData.category}
                            onChange={handleChange}
                            className={errors.category ? 'error' : ''}
                        />
                        {errors.category && <span className="error-message">{errors.category}</span>}
                    </div>


                    <div className="tx-form-group">
                        <label htmlFor="date">Date</label>
                            <input
                                type="date"
                                id="date"
                                name="date"
                                value={formData.date}
                                onChange={handleChange}
                                className={errors.date ? 'error' : ''}
                            />
                            {errors.date && <span className="error-message">{errors.date}</span>}
                    </div>

                    <div className="tx-modal-actions">
                        <button type="button" className="tx-cancel-btn" onClick={onClose}>
                            Cancel
                        </button>
                        <button type="submit" className="tx-save-btn">
                            {transaction ? 'Update' : 'Add Transaction'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default TransactionModal;