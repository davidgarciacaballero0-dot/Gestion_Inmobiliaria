'use strict';

const { simulateTransaction } = require('../config/ledger');
const { submitTransaction } = require('../config/fabric');

const SIMULATE = process.env.SIMULATE_BLOCKCHAIN !== 'false';

const contratosController = {
    crear: async (req, res) => {
        const { id, inmuebleId, propietarioId, inquilinoId, montoAlquiler, montoDeposito, fechaInicio, fechaFin } = req.body;
        if (!id || !inmuebleId || !propietarioId || !inquilinoId) {
            return res.status(400).json({ error: 'Faltan campos requeridos.' });
        }

        try {
            if (SIMULATE) {
                const result = simulateTransaction('crearContrato', { id, inmuebleId, propietarioId, inquilinoId, montoAlquiler, montoDeposito, fechaInicio, fechaFin });
                return res.status(201).json(result);
            } else {
                const result = await submitTransaction(
                    'crearContrato', 
                    id, 
                    inmuebleId, 
                    propietarioId, 
                    inquilinoId, 
                    (montoAlquiler || 0).toString(), 
                    (montoDeposito || 0).toString(), 
                    fechaInicio || '', 
                    fechaFin || ''
                );
                return res.status(201).json(result);
            }
        } catch (err) {
            res.status(500).json({ error: err.message });
        }
    },

    firmar: async (req, res) => {
        const { id, rolUsuario, hashFirmaDigital } = req.body;
        if (!id || !rolUsuario || !hashFirmaDigital) {
            return res.status(400).json({ error: 'Faltan campos requeridos.' });
        }

        try {
            if (SIMULATE) {
                const result = simulateTransaction('firmarContrato', { id, rolUsuario, hashFirmaDigital });
                return res.json(result);
            } else {
                const result = await submitTransaction('firmarContrato', id, rolUsuario, hashFirmaDigital);
                return res.json(result);
            }
        } catch (err) {
            res.status(500).json({ error: err.message });
        }
    }
};

module.exports = contratosController;
