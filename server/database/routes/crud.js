const express = require('express');
const { Sequelize } = require('sequelize');

/**
 * Build a generic CRUD router for a Sequelize model.
 *
 *   GET    /            list (optionally filtered by any column via query params,
 *                        e.g. ?user_id=3)
 *   GET    /:id         retrieve one
 *   POST   /            create
 *   PATCH  /:id         partial update
 *   DELETE /:id         delete
 *
 * This is a data-access layer only. It intentionally does NOT reimplement
 * the business logic that lives in djangoapp/services/* (budget spend
 * calculations, debt simplification, split generation, friend-request
 * auto-accept, etc.). Callers (Django) are responsible for that logic and
 * for authorization -- this API trusts whatever calls it with a valid
 * internal API key.
 */
function buildCrudRouter(model, { include } = {}) {
    const router = express.Router();
    const Op = Sequelize.Op;
    const attrs = model.rawAttributes || {};

    function resolveField(field) {
        if (attrs[field]) return field;
        if (attrs[`${field}_id`]) return `${field}_id`;
        return field;
    }

    function coerceQueryValue(val) {
        if (val === 'true' || val === 'True') return true;
        if (val === 'false' || val === 'False') return false;
        return val;
    }

    function normalizeBody(body) {
        if (!body || typeof body !== 'object') return body;
        const normalized = {};
        for (const [key, value] of Object.entries(body)) {
            normalized[resolveField(key)] = value;
        }
        return normalized;
    }

    function serializeRow(row) {
        if (!row) return row;
        const data = typeof row.toJSON === 'function' ? row.toJSON() : { ...row };
        for (const [key, value] of Object.entries(data)) {
            if (key.endsWith('_id')) {
                const baseKey = key.slice(0, -3);
                if (!(baseKey in data)) {
                    data[baseKey] = value;
                }
            }
        }
        return data;
    }

    router.get('/', async (req, res) => {
        try {
            // Convert Django-style query parameters to Sequelize operators
            const where = {};
            for (const [key, value] of Object.entries(req.query)) {
                if (key.includes('__')) {
                    // Handle Django-style lookups like date__gte, date__lte
                    const [rawField, operator] = key.split('__');
                    const field = resolveField(rawField);
                    if (!where[field]) {
                        where[field] = {};
                    }
                    // Map Django operators to Sequelize operators
                    switch (operator) {
                        case 'gte':
                            where[field][Op.gte] = value;
                            break;
                        case 'lte':
                            where[field][Op.lte] = value;
                            break;
                        case 'gt':
                            where[field][Op.gt] = value;
                            break;
                        case 'lt':
                            where[field][Op.lt] = value;
                            break;
                        case 'exact':
                            where[field][Op.eq] = value;
                            break;
                        case 'iexact':
                            where[field][Op.like] = value;
                            break;
                        case 'contains':
                            where[field][Op.substring] = value;
                            break;
                        case 'icontains':
                            where[field][Op.substring] = value;
                            break;
                        case 'in':
                            where[field][Op.in] = value.split(',');
                            break;
                        case 'startswith':
                            where[field][Op.startsWith] = value;
                            break;
                        case 'endswith':
                            where[field][Op.endsWith] = value;
                            break;
                        case 'isnull':
                            where[field][Op.eq] = value === 'true' ? null : value;
                            break;
                        default:
                            // Default to exact match if operator not recognized
                            where[field] = coerceQueryValue(value);
                    }
                } else {
                    // Direct field match
                    where[resolveField(key)] = coerceQueryValue(value);
                }
            }
            const rows = await model.findAll({ where, include });
            res.json(rows.map(serializeRow));
        } catch (err) {
            res.status(500).json({ error: err.message });
        }
    });

    router.get('/:id', async (req, res) => {
        try {
            const row = await model.findByPk(req.params.id, { include });
            if (!row) return res.status(404).json({ error: `${model.name} not found` });
            res.json(serializeRow(row));
        } catch (err) {
            res.status(500).json({ error: err.message });
        }
    });

    router.post('/', async (req, res) => {
        try {
            const row = await model.create(normalizeBody(req.body));
            res.status(201).json(serializeRow(row));
        } catch (err) {
            res.status(400).json({ error: err.message });
        }
    });

    router.patch('/:id', async (req, res) => {
        try {
            const row = await model.findByPk(req.params.id);
            if (!row) return res.status(404).json({ error: `${model.name} not found` });
            await row.update(normalizeBody(req.body));
            res.json(serializeRow(row));
        } catch (err) {
            res.status(400).json({ error: err.message });
        }
    });

    router.delete('/:id', async (req, res) => {
        try {
            const deleted = await model.destroy({ where: { id: req.params.id } });
            if (!deleted) return res.status(404).json({ error: `${model.name} not found` });
            res.json({ message: `${model.name} deleted`, deleted });
        } catch (err) {
            res.status(500).json({ error: err.message });
        }
    });

    return router;
}

module.exports = buildCrudRouter;