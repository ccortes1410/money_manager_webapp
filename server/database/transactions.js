// const sequelize = require('sequelize');

module.exports = (sequelize, DataTypes) => {
    return sequelize.define('Transaction', {
        id: {
            type: DataTypes.INTEGER,
            primaryKey: true,
            autoIncrement: true
        },
        user_id: {
            type: DataTypes.INTEGER,
            allowNull: false
        },
        amount: {
            type: DataTypes.DECIMAL(10, 2),
            allowNull: false
        },
        description: {
            type: DataTypes.STRING,
            allowNull: false
        },
        category: {
            type: DataTypes.STRING,
            allowNull: true
        },
        date: {
            type: DataTypes.DATEONLY,
            allowNull: false
        },
        // recurring_source: {
        //     type: DataTypes.INTEGER,
        //     allowNull: true,
        //     references: {
        //         model: 'RecurringTransaction',
        //         key: 'id'
        //     }
        // }
        
    }, {
        tableName: 'djangoapp_transaction',
        timestamps: false
    });
};
