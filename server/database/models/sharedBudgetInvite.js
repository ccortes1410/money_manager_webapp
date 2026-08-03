const { DataTypes } = require('sequelize');
const sequelize = require('./db');

const SharedBudgetInvite = sequelize.define('SharedBudgetInvite', {
    id: { type: DataTypes.BIGINT, primaryKey: true, autoIncrement: true },
    shared_budget_id: { type: DataTypes.BIGINT, allowNull: false },
    invited_by_id: { type: DataTypes.INTEGER, allowNull: false },
    invited_user_id: { type: DataTypes.INTEGER, allowNull: false },
    role: { type: DataTypes.STRING(20), defaultValue: 'editor' },
    status: { type: DataTypes.STRING(20), defaultValue: 'pending' },
    message: { type: DataTypes.TEXT, allowNull: true },
    created_at: { type: DataTypes.DATE },
    responded_at: { type: DataTypes.DATE, allowNull: true },
}, {
    tableName: 'djangoapp_sharedbudgetinvite',
    timestamps: false,
    indexes: [{ unique: true, fields: ['shared_budget_id', 'invited_user_id']}],
});

module.exports = SharedBudgetInvite;
