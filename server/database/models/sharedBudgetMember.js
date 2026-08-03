const { DataTypes } = require('sequelize');
const sequelize = require('./db');

const SharedBudgetMember = sequelize.define('SharedBudgetMember', {
    id: { type: DataTypes.BIGINT, primaryKey: true, autoIncrement: true },
    shared_budget_id: { type: DataTypes.BIGINT, allowNull: false },
    user_id: { type: DataTypes.INTEGER, allowNull: false },
    role: { type: DataTypes.STRING(20), defaultValue: 'editor' },
    contribution_percentage: { type: DataTypes.DECIMAL(5, 2), defaultValue: 0 },
    joined_at: { type: DataTypes.DATE },
}, {
    tableName: 'djangoapp_sharedbudgetmember',
    timestamps: false,
    indexes: [{ unique: true, fields: ['shared_budget_id', 'user_id'] }],
});

module.exports = SharedBudgetMember;
