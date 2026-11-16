try { require('dotenv').config(); } catch (_) {}
const { Sequelize } = require('sequelize');
const mysql2 = require('mysql2');

const dbHost = process.env.DB_HOST || 'mysql_db';
const useSsl =
    process.env.DB_SSL === 'true' ||
    dbHost.includes('tidbcloud.com');

const sequelize = new Sequelize(
    process.env.DB_NAME,
    process.env.DB_USER,
    process.env.DB_PASSWORD,
    {
        host: dbHost,
        port: Number(process.env.DB_PORT) || 3306,
        dialect: 'mysql',
        dialectModule: mysql2,
        logging: false,
        dialectOptions: useSsl
            ? {
                  ssl: {
                      minVersion: 'TLSv1.2',
                      rejectUnauthorized: true,
                  },
              }
            : {},
    }
);

module.exports = sequelize;