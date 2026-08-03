const { DataTypes } = require('sequelize');
const sequelize = require('./db');

const SubscriptionPayment = sequelize.define('SubscriptionPayment', {
    id: { type: DataTypes.BIGINT, primaryKey: true, autoIncrement: true },
    subscription_id: { type: DataTypes.INTEGER, allowNull: false },
    amount: { type: DataTypes.DECIMAL(10, 2), allowNull: false },
    due_date: { type: DataTypes.DATEONLY, allowNull: false },
    is_paid: { type: DataTypes.BOOLEAN, defaultValue: false },
    paid_date: { type: DataTypes.DATEONLY, allowNull: true },
    created_at: { type: DataTypes.DATE },
}, {
    tableName: 'djangoapp_subscriptionpayment',
    timestamps: false,
    indexes: [{ unique: true, fields: ['subscription_id', 'due_date'] }],
});

module.exports = SubscriptionPayment;