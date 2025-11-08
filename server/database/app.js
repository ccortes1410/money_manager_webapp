const express = require('express');
const { Sequelize, DataTypes } = require('sequelize');
const fs = require('fs');
const cors = require('cors');
const { connect } = require('http2');
const { BADFAMILY } = require('dns');

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

const Transactions = require('./transactions')(sequelize, DataTypes);
const Budget = require('./budget')(sequelize, DataTypes);
const Subscription = require('./subscriptions')(sequelize, DataTypes);

// const transaction_data = JSON.parse(fs.readFileSync('transactions.js', 'utf8'));
async function connectWithRetry() {
    let retries = 5;
    while (retries) {
        try {
            await sequelize.authenticate();
            console.log('Database connection established successfully.');
            // await sequelize.sync();
            console.log('Starting app.js...');
            console.log('Connected to database:', sequelize.config.database);
            console.log(Object.keys(Transactions.rawAttributes)); // Should include 'user_id'

            app.get('/', async (req, res) => {
                res.send("Welcome to the Money Manager API");
            });

            app.get('/fetchTransactions', async (req, res) => {
                try {
                    const documents = await Transactions.findAll();
                    console.log("Fetched transactions:", JSON.stringify(documents, null, 4));
                    res.json(documents);
                } catch (error) {
                    console.log("Error fetching transactions:", error);
                    res.status(500).json({ error: "Internal Server Error" });
                }
            });

            app.get('/fetchBudgets', async (req, res) => {
                try {
                    const documents = await Budget.findAll();
                    console.log("Fetched budget:", JSON.stringify(documents, null, 4));
                    res.json(documents);
                } catch (error) {
                    console.log("Error fetching budget:", error);
                    res.status(500).json({ error: "Internal Server Error" });
                }
            })

            app.get('/fetchBudget/:id', async (req, res) => {
                try {
                    const documents = await Budget.findAll({
                        where: {
                            id: req.params.id
                        }
                    });
                    res.json(documents);
                } catch (error) {
                    console.log("Error fetching budget:", error);
                    res.status(500).json({ error: "Internal Server Error" });
                }
            })

            app.post('/addBudget', async (req, res) => {
                const { name, amount, period } = req.body;
                try {
                    const newBudget = await Budget.create({ name, amount, period });
                    res.status(201).json(newBudget);
                } catch (error) {
                    console.log("Error adding budget:", error);
                    res.status(500).json({ error: "Internal Server Error" });
                }
            });

            app.get('/fetchSubscriptions', async (req, res) => {
                try {
                    const documents = await Subscription.findAll();
                    console.log("Fetched subscriptions:", JSON.stringify(documents, null, 4));
                    res.json(documents);
                } catch (error) {
                    console.log("Error fetching subscriptions:", error);
                    res.status(500).json({ error: "Internal Server Error" });
                }
            });
            
            app.listen(port, () => {
                console.log(`Server is running on http://localhost:${port}`);
            });
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
