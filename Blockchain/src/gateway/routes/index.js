'use strict';

const express = require('express');
const router = express.Router();

const inmueblesController = require('../controllers/inmuebles');
const contratosController = require('../controllers/contratos');
const pagosController = require('../controllers/pagos');
const auditController = require('../controllers/audit');

const SIMULATE = process.env.SIMULATE_BLOCKCHAIN !== 'false';

// Endpoint de prueba de conexión
router.get('/health', (req, res) => {
    res.json({
        status: 'UP',
        mode: SIMULATE ? 'SIMULADO (Ledger JSON)' : 'PRODUCCIÓN (Hyperledger Fabric gRPC)',
        timestamp: new Date().toISOString()
    });
});

// A. GESTIÓN DE INMUEBLES y TÍTULOS
router.post('/inmuebles', inmueblesController.registrar);
router.put('/inmuebles/transferir', inmueblesController.transferir);

// B. GESTIÓN DE CONTRATOS
router.post('/contratos', contratosController.crear);
router.put('/contratos/firmar', contratosController.firmar);

// C. AUDITORÍA DE PAGOS
router.post('/pagos', pagosController.registrar);

// D. CONSULTA DE AUDITORÍA
router.get('/stats', auditController.stats);
router.get('/consultar/:id', auditController.consultar);
router.get('/historial/:id', auditController.historial);

module.exports = router;
