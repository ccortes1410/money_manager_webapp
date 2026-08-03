const { DataTypes } = require('sequelize');
const sequelize = require('./db');

const SharedExpense = sequelize.define('SharedExpense', {
    id: { type: DataTypes.BIGINT, primaryKey: true, autoIncrement: true },
    shared_budget_id: { type: DataTypes.BIGINT, allowNull: false },
    description: { type: DataTypes.STRING(200), allowNull: false },
    amount: { type: DataTypes.DECIMAL(12, 2), allowNull: false },
    paid_by_id: { type: DataTypes.INTEGER, allowNull: false },
    date: { type: DataTypes.DATEONLY, allowNull: false },
    category: { type: DataTypes.STRING(50), allowNull: true },
    created_at: { type: DataTypes.DATE },
    created_by_id: { type: DataTypes.INTEGER, allowNull: false },
    receipt_image: { type: DataTypes.STRING(255), allowNull: true },
    notes: { type: DataTypes.TEXT, allowNull: true },
}, {
    tableName: 'djangoapp_sharedexpense',
    timestamps: false,
});

module.exports = SharedExpense;