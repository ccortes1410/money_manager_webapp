const { DataTypes } = require('sequelize');
const sequelize = require('./db');

const FriendshipNotification = sequelize.define('FriendshipNotification', {
    id: { type: DataTypes.BIGINT, primaryKey: true, autoIncrement: true },
    user_id: { type: DataTypes.INTEGER, allowNull: false },
    from_user_id: { type: DataTypes.INTEGER, allowNull: false },
    notification_type: { type: DataTypes.STRING(30), allowNull: false },
    friendship_id: { type: DataTypes.BIGINT, allowNull: true },
    message: { type: DataTypes.STRING(255), allowNull: false },
    is_read: { type: DataTypes.BOOLEAN, defaultValue: false },
    created_at: { type: DataTypes.DATE },
}, {
    tableName: 'djangoapp_friendshipnotification',
    timestamps: false,
});

module.exports = FriendshipNotification;