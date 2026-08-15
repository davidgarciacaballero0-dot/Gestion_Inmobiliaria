'use strict';

const { readSimulatedLedger } = require('../config/ledger');
const { evaluateTransaction } = require('../config/fabric');

const SIMULATE = process.env.SIMULATE_BLOCKCHAIN !== 'false';

const auditController = {
    consultar: async (req, res) => {
        const { id } = req.params;
        try {
            if (SIMULATE) {
                const ledger = readSimulatedLedger();
                const asset = ledger.worldState[id];
                if (!asset) {
                    return res.status(404).json({ error: `El activo con ID ${id} no existe.` });
                }
                return res.json(asset);
            } else {
                const result = await evaluateTransaction('queryAsset', id);
                return res.json(result);
            }
        } catch (err) {
            res.status(500).json({ error: err.message });
        }
    },

    historial: async (req, res) => {
        const { id } = req.params;
        try {
            if (SIMULATE) {
                const ledger = readSimulatedLedger();
                
                // Buscar todas las transacciones asociadas a este ID en los bloques
                const history = [];
                ledger.blocks.forEach(block => {
                    block.transactions.forEach(tx => {
                        if (tx.args.id === id) {
                            history.push({
                                txId: tx.txId,
                                timestamp: tx.timestamp,
                                blockNumber: block.blockNumber,
                                blockHash: block.blockHash,
                                txName: tx.txName,
                                data: tx.args
                            });
                        }
                    });
                });

                return res.json(history);
            } else {
                const result = await evaluateTransaction('obtenerHistorialActivo', id);
                return res.json(result);
            }
        } catch (err) {
            res.status(500).json({ error: err.message });
        }
    },

    stats: async (req, res) => {
        try {
            if (SIMULATE) {
                const ledger = readSimulatedLedger();
                const totalBlocks = ledger.blocks.length;
                const assets = Object.values(ledger.worldState);
                
                const stats = {
                    status: 'UP',
                    mode: 'SIMULADO (Ledger JSON)',
                    totalBlocks,
                    totalInmuebles: assets.filter(a => a.docType === 'inmueble').length,
                    totalContratos: assets.filter(a => a.docType === 'contrato').length,
                    totalPagos: assets.filter(a => a.docType === 'pago').length,
                    blocks: ledger.blocks.map(b => ({
                        blockNumber: b.blockNumber,
                        prevHash: b.prevHash,
                        blockHash: b.blockHash,
                        timestamp: b.timestamp,
                        transactions: b.transactions.map(t => ({
                            txId: t.txId,
                            txName: t.txName,
                            assetId: t.args.id,
                            args: t.args
                        }))
                    })).reverse()
                };
                return res.json(stats);
            } else {
                return res.json({
                    status: 'UP',
                    mode: 'PRODUCCIÓN (Hyperledger Fabric gRPC GKE)',
                    totalBlocks: 'N/A (Consulta a través de CLI de K8s)',
                    totalInmuebles: 'N/A',
                    totalContratos: 'N/A',
                    totalPagos: 'N/A',
                    blocks: []
                });
            }
        } catch (err) {
            res.status(500).json({ error: err.message });
        }
    }
};

module.exports = auditController;
