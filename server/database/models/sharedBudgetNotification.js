const { DataTypes } = require('sequelize');
const sequelize = require('./db');

const SharedBudgetNotification = sequelize.define('SharedBudgetNotification', {
    id: { type: DataTypes.BIGINT, primaryKey: true, autoIncrement: true },
    user_id: { type: DataTypes.INTEGER, allowNull: false },
    from_user_id: { type: DataTypes.INTEGER, allowNull: false },
    notification_type: { type: DataTypes.STRING(30), allowNull: false },
    shared_budget_id: { type: DataTypes.BIGINT, allowNull: true },
    message: { type: DataTypes.STRING(255), allowNull: false },
    is_read: { type: DataTypes.BOOLEAN, defaultValue: false },
    created_at: { type: DataTypes.DATE },
}, {
    tableName: 'djangoapp_sharedbudgetnotification',
    timestamps: false,
});

module.exports = SharedBudgetNotification;