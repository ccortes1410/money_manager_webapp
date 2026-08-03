/**
 * Simple shared-secret check. This API is meant to be called
 * server-to-server by Django, not directly from a browser, so a static
 * header is enough as a first line of defense. Put both containers on a
 * private Docker network and don't publish this port to the public
 * internet in production.
 */
module.exports = function requireInteralApiKey(req, res, next) {
    const expected = process.env.INTERNAL_API_KEY;

    if (!expected) {
        // Fail closed: if it isn't configured, don't silently allow everything through.
        return res.status(500).json({ error: 'INTERNAL_API_KEY not configured on the server' });
    }

    const provided = req.header('x-internal-api-key');
    if (provided !== expected) {
        return res.status(401).json({ error: 'Unauthorized' });
    }

    next();
};