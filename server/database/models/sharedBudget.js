const { DataTypes } = require('sequelize');
const sequelize = require('./db');

const SharedBudget = sequelize.define('SharedBudget', {
    id: { type: DataTypes.BIGINT, primaryKey: true, autoIncrement: true },
    name: { type: DataTypes.STRING(100), allowNull: false },
    description: { type: DataTypes.TEXT, allowNull: true },
    total_amount: { type: DataTypes.DECIMAL(12, 2), allowNull: false },
    category: { type: DataTypes.STRING(50), allowNull: true },
    created_by_id: { type: DataTypes.INTEGER, allowNull: false },
    created_at: { type: DataTypes.DATE },
    updated_at: { type: DataTypes.DATE },
    period_start: { type: DataTypes.DATEONLY, allowNull: false },
    period_end: { type: DataTypes.DATEONLY, allowNull: false },
    is_active: { type: DataTypes.BOOLEAN, defaultValue: true },
    default_split_type: { type: DataTypes.STRING(20), defaultValue: 'equal' },
}, {
    tableName: 'djangoapp_sharedbudget',
    timestamps: false,
});

module.exports = SharedBudget;