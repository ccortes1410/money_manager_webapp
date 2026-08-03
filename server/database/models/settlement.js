const { DataTypes } = require('sequelize');
const sequelize = require('./db');

const Settlement = sequelize.define('Settlement', {
    id: { type: DataTypes.BIGINT, primaryKey: true, autoIncrement: true },
    shared_budget_id: { type: DataTypes.BIGINT, allowNull: false },
    payer_id: { type: DataTypes.INTEGER, allowNull: false },
    receiver_id: { type: DataTypes.INTEGER, allowNull: false },
    amount: { type: DataTypes.DECIMAL(12, 2), allowNull: false },
    date: { type: DataTypes.DATEONLY, allowNull: false },
    notes: { type: DataTypes.TEXT, allowNull: true },
    created_at: { type: DataTypes.DATE },
}, {
    tableName: 'djangoapp_settlement',
    timestamps: false,
});

module.exports = Settlement;