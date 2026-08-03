const { DataTypes } = require('sequelize');
const sequelize = require('./db');

const Transaction = sequelize.define('Transaction', {
    id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
    user_id: { type: DataTypes.INTEGER, allowNull: false },
    amount: { type: DataTypes.DECIMAL(10, 2), allowNull: false },
    description: { type: DataTypes.STRING(255), allowNull: false },
    category: { type: DataTypes.STRING(100), allowNull: true },
    date: { type: DataTypes.DATEONLY, allowNull: false },
}, {
    tableName: 'djangoapp_transaction',
    timestamps: false,
});

module.exports = Transaction;