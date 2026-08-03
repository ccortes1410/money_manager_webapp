const { DataTypes } = require('sequelize');
const sequelize = require('./db');

// Django owns this table (auth_user) via its own migrations. This service
// never creates, alters, or syncs it -- it's defined here only so we can
// set up associations (belongsTo/hasMany) and include user data in
// responses.
const User = sequelize.define('User', {
    id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
    username: DataTypes.STRING(150),
    email: DataTypes.STRING(254),
    first_name: DataTypes.STRING(150),
    last_name: DataTypes.STRING(150),
}, {
    tableName: 'auth_user',
    timestamps: false,
});

module.exports = User;