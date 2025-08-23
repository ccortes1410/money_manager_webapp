/* jshint esversion: 8 */
const express = require('express');
const { Sequelize, DataTypes } = require('sequelize');
const fs = require('fs');
const cors = require('cors');

const app = express();
const port = 3030;

app.use(cors());
app.use(require('body-parser').urlencoded({ extended: false }));

const transaction_data = JSON.parse(fs.readFileSync('transactions.json', 'utf8'));

const sequelize = new Sequelize('money_manager_db', 'root', process.env.DB_SECRET_PASSWORD, {
    host: 'localhost',
    dialect: 'mysql'
});

const Use = sequelize.define('User', {
    username: {
        type: DataTypes.STRING,
        allowNull: false
    },
    password: {
        type: DataTypes.STRING,
        allowNull: false
    }
});

(async () => {
    try {
        await sequelize.authenticate();
        console.log('Connection has been established successfully.');
        await sequelize.sync();
        const admin = await User.create({ username: 'admin', password: 'admin' });
        console.log(admin.toJSON());
    } catch (error) {
        console.error('Unable to connect to the database:', error);
    }
})();