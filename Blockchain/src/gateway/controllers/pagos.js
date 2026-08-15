'use strict';

const { simulateTransaction } = require('../config/ledger');
const { submitTransaction } = require('../config/fabric');

const SIMULATE = process.env.SIMULATE_BLOCKCHAIN !== 'false';

const pagosController = {
    registrar: async (req, res) => {
        const { id, contratoId, monto, fecha, tipoPago, stripeTransactionId } = req.body;
        if (!id || !contratoId || !monto) {
            return res.status(400).json({ error: 'Faltan campos requeridos.' });
        }

        try {
            if (SIMULATE) {
                const result = simulateTransaction('registrarPago', { id, contratoId, monto, fecha, tipoPago, stripeTransactionId });
                return res.status(201).json(result);
            } else {
                const result = await submitTransaction(
                    'registrarPago', 
                    id, 
                    contratoId, 
                    monto.toString(), 
                    fecha || '', 
                    tipoPago || '', 
                    stripeTransactionId || ''
                );
                return res.status(201).json(result);
            }
        } catch (err) {
            res.status(500).json({ error: err.message });
        }
    }
};

module.exports = pagosController;
