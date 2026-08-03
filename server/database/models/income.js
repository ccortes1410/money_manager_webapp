const { DataTypes } = require('sequelize');
const sequelize = require('./db');

const Income = sequelize.define('Income', {
    id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
    user_id: { type: DataTypes.INTEGER, allowNull: false },
    amount: { type: DataTypes.DECIMAL(10, 2), allowNull: false },
    source: { type: DataTypes.STRING(255), allowNull: false },
    date_received: { type: DataTypes.DATEONLY, allowNull: false },
    period_start: { type: DataTypes.DATEONLY, allowNull: false },
    period_end: { type: DataTypes.DATEONLY, allowNull: false },
}, {
    tableName: 'djangoapp_income',
    timestamps: false,
});

module.exports = Income;