'use strict';

const { simulateTransaction } = require('../config/ledger');
const { submitTransaction } = require('../config/fabric');

const SIMULATE = process.env.SIMULATE_BLOCKCHAIN !== 'false';

const inmueblesController = {
    registrar: async (req, res) => {
        const { id, titulo, propietarioId, direccion, hashTituloPropiedad } = req.body;
        if (!id || !titulo || !propietarioId || !hashTituloPropiedad) {
            return res.status(400).json({ error: 'Faltan campos requeridos en el body.' });
        }

        try {
            if (SIMULATE) {
                const result = simulateTransaction('registrarInmueble', { id, titulo, propietarioId, direccion, hashTituloPropiedad });
                return res.status(201).json(result);
            } else {
                const result = await submitTransaction('registrarInmueble', id, titulo, propietarioId, direccion || '', hashTituloPropiedad);
                return res.status(201).json(result);
            }
        } catch (err) {
            res.status(500).json({ error: err.message });
        }
    },

    transferir: async (req, res) => {
        const { id, nuevoPropietarioId, nuevoHashTitulo } = req.body;
        if (!id || !nuevoPropietarioId || !nuevoHashTitulo) {
            return res.status(400).json({ error: 'Faltan campos requeridos.' });
        }

        try {
            if (SIMULATE) {
                const result = simulateTransaction('transferirPropiedad', { id, nuevoPropietarioId, nuevoHashTitulo });
                return res.json(result);
            } else {
                const result = await submitTransaction('transferirPropiedad', id, nuevoPropietarioId, nuevoHashTitulo);
                return res.json(result);
            }
        } catch (err) {
            res.status(500).json({ error: err.message });
        }
    }
};

module.exports = inmueblesController;
