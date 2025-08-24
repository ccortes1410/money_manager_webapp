const express = require('express');
const { Sequelize, DataTypes } = require('sequelize');
const fs = require('fs');
const cors = require('cors');
const { connect } = require('http2');

const app = express();
const port = 3030;

app.use(cors());
app.use(require('body-parser').urlencoded({ extended: false }));

console.log('DB_SECRET_PASSWORD:', process.env.DB_SECRET_PASSWORD);

const sequelize = new Sequelize(
    'money_manager_db',
    'root',
    process.env.DB_SECRET_PASSWORD,
    {
        host: 'mysql_db',
        port: 3306,
        dialect: 'mysql'
    }
);

// const transaction_data = JSON.parse(fs.readFileSync('transactions.js', 'utf8'));
async function connectWithRetry() {
    let retries = 5;
    while (retries) {
        try {
            await sequelize.authenticate();
            console.log('Database connection established successfully.');
            await sequelize.sync();
            break;
        } catch (error) {
            console.error('Database connection failed:', error);
            retries -= 1;
            console.log(`Retries left: ${retries}`);
            await new Promise(res => setTimeout(res, 5000));
        }
    }
    if (!retries) {
        console.error('Could not connect to the database after multiple attempts.');
        process.exit(1);
    }
}

connectWithRetry();



const User = sequelize.define('User', {
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

const Transactions = require('./transactions')(sequelize, DataTypes);

app.get('/', async (req, res) => {
    res.send("Welcome to the Money Manager API");
})

app.get('/fetchTransactions', async (req, res) => {
    try {
        const documents = await Transactions.findAll();
        res.json(documents);
    } catch (error) {
        console.log("Error fetching transactions:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
});

app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
