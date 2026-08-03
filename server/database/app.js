require('dotenv').config();
const express = require('express');
const cors = require('cors');

const db = require('./models');
const apiRoutes = require('./routes');
const requireInternalApiKey = require('./middleware/auth');

const app = express();
const port = process.env.PORT || 3030;

app.use(cors());
app.use(express.json());

app.get('/', (req, res) => {
    res.send('Money Manager database API is running');
});

app.get('/health', async(req, res) => {
    try {
        awaitdb.sequelize.authenticate();
        res.json({ status: 'ok', database: 'connected'});
    } catch(err) {
        res.status(503).json({ status: 'error', database: 'unreachable', detail: err.message });
    }
});

// Everything under /api/* requires the shared secret header.
app.use('/api', requireInternalApiKey, apiRoutes);

// NOTE: we deliberately never all db.sequelize.sync() here. Django's
// migrations are the single source of truth for the scema -- this
// service only reads/writes rows, it never creates or alters tables.
async function start() {
    const maxRetries = 10;
    let attempt = 0;

    while (attempt < maxRetries) {
        try {
            await db.sequelize.authenticate();
            console.log('Database connection established succesfully.');
            break;
        } catch (err) {
            attempt += 1;
            console.error(`DB connection failed (attempt ${attempt}/${maxRetries}):`, err.message);
            if (attempt >= maxRetries) {
                console.error('Could not connect to the database after multiple attempts. Exiting.');
                process.exit(1);
            }
            await new Promise((resolve) => setTimeout(resolve, 5000));
        }
    }

    app.listen(port, () => {
        console.log(`Money Manager database API listenting on port ${port}`);
    });
}

start();