const express = require('express');

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

    router.get('/', async (req, res) => {
        try {
            const where = { ...req.query };
            const rows = await model.findAll({ where, include });
            res.json(rows);
        } catch (err) {
            res.status(500).json({ error: err.message });
        }
    });

    router.get('/:id', async (req, res) => {
        try {
            const row = await model.findByPk(req.params.id, { include });
            if (!row) return res.status(404).json({ error: `${model.name} not found` });
            res.json(row);
        } catch (err) {
            res.status(500).json({ error: err.message });
        }
    });

    router.post('/', async (req, res) => {
        try {
            const row = await model.create(req.body);
            res.status(201).json(row);
        } catch (err) {
            res.status(400).json({ error: err.message });
        }
    });

    router.patch('/:id', async (req, res) => {
        try {
            const row = await model.findByPk(req.params.id);
            if (!row) return res.status(404).json({ error: `${model.name} not found` });
            await row.update(req.body);
            res.json(row);
        } catch (err) {
            res.status(400).json({ error: err.message });
        }
    });

    router.delete('/:id', async (req, res) => {
        try {
            const deleted = await model.destroy({ where: { id: req.params.id } });
            if (!deleted) return res.status(404).json({ error: `${model.name} not found` });
        } catch (err) {
            res.status(500).json({ error: err.message });
        }
    });

    return router;
}

module.exports = buildCrudRouter;