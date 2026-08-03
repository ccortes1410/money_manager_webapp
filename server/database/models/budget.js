const { DataTypes } = require('sequelize');
const sequelize = require('./db');

const Budget = sequelize.define('Budget', {
    id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
    user_id: { type: DataTypes.INTEGER, allowNull: false },
    category: { type: DataTypes.STRING(100), allowNull: false },
    amount: { type: DataTypes.Decimal(10, 2), allowNull: false },
    period_start: { type: DataTypes.DATEONLY, allowNull: false },
    period_end: { type: DataTypes.DATEONLY, allowNull: false },
    recurrence: { type: DataTypes.STRING(10), allowNull: true },
    is_active: { type: DataTypes.BOOLEAN, defaultValue: true },
    is_recurring: { type: DataTypes.BOOLEAN, defaultValue: true },
    is_shared: { type: DataTypes.BOOLEAN, defaultValue: false },
    created_at: { type: DataTypes.DATEONLY },
}, {
    tableName: 'djangoapp_budget',
    timestamps: false,
    indexes: [{ unique: true, fields: ['category', 'user_id'] }],
});

module.exports = Budget;