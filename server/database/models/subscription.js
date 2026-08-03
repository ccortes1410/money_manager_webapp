const { DataTypes } = require('sequelize');
const sequelize = require('./db');

const Subscription = sequelize.define('Subscription', {
    id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
    user_id: { type: DataTypes.INTEGER, allowNull: false },
    name: { type: DataTypes.STRING(100), allowNull: false },
    amount: { type: DataTypes.DECIMAL(10, 2), allowNull: false },
    category: { type: DataTypes.STRING(100), allowNull: false },
    billing_cycle: { type: DataTypes.STRING(20), defaultValue: 'monthly' },
    billing_day: { type: DataTypes.INTEGER, defaultValue: 1 },
    start_date: { type: DataTypes.DATEONLY, allowNull: false },
    end_date: { type: DataTypes.DATEONLY, allowNull: true },
    status: { type: DataTypes.STRING(20), defaultValue: 'active' },
    description: { type: DataTypes.STRING(255), allowNull: true, defaultValue: '' },
    created_at: { type: DataTypes.DATE },
    updated_at: { type: DataTypes.DATE },
}, {
    tableName: 'djangoapp_subscription',
    timestamps: false,
});

module.exports = Subscription;