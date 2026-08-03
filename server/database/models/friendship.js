const { DataTypes } = require('sequelize');
const sequelize = require('./db');

const Friendship = sequelize.define('Friendship', {
    id: { type: DataTypes.BIGINT, primaryKey: true, autoIncrement: true },
    sender_id: { type: DataTypes.INTEGER, allowNull: false },
    receiver_id: { type: DataTypes.INTEGER, allowNull: false },
    status: { type: DataTypes.STRING(20), defaultValue: 'pending' },
    created_at: { type: DataTypes.DATE },
    updated_at: { type: DataTypes.DATE },
}, {
    tableName: 'djangoapp_friendship',
    timestamps: false,
    indexes: [{ unique: true, fields: ['sender_id', 'receiver_id'] }],
});

module.exports = Friendship;