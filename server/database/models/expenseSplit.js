const { DataTypes } = require('sequelize');
const sequelize = require('./db');

const ExpenseSplit = sequelize.define('ExpenseSplit', {
    id: { type: DataTypes.BIGINT, primaryKey: true, autoIncrement: true },
    shared_expense_id: { type: DataTypes.BIGINT, allowNull: false },
    user_id: { type: DataTypes.INTEGER, allowNull: false},
    amount_owed: { type: DataTypes.DECIMAL(12, 2), allowNull: false },
    is_settled : { type: DataTypes.BOOLEAN, defaultValue: false },
    settled_at: { type: DataTypes.DATE, allowNull: true},
}, {
    tableName: 'djangoapp_expensesplit',
    timestamps: false,
    indexes: [{ unique: true, fields: ['shared_expense_id', 'user_id']}],
});

module.exports = ExpenseSplit;