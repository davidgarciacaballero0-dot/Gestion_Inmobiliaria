'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// Ruta al Ledger simulado en la raíz de la carpeta Blockchain
const LEDGER_FILE = path.join(__dirname, '..', '..', '..', 'simulated_ledger.json');

// Inicializar base de datos simulada en JSON si no existe
if (!fs.existsSync(LEDGER_FILE)) {
    fs.writeFileSync(LEDGER_FILE, JSON.stringify({
        blocks: [],
        worldState: {}
    }, null, 2));
}

function readSimulatedLedger() {
    return JSON.parse(fs.readFileSync(LEDGER_FILE, 'utf8'));
}

function writeSimulatedLedger(data) {
    fs.writeFileSync(LEDGER_FILE, JSON.stringify(data, null, 2));
}

function calculateBlockHash(block) {
    const dataStr = JSON.stringify(block.transactions) + block.prevHash + block.timestamp;
    return crypto.createHash('sha256').update(dataStr).digest('hex');
}

function simulateTransaction(txName, args) {
    const ledger = readSimulatedLedger();
    const txId = 'tx_' + crypto.randomBytes(16).toString('hex');
    const timestamp = new Date().toISOString();

    const transaction = {
        txId,
        timestamp,
        txName,
        args
    };

    const key = args.id;
    if (txName === 'registrarInmueble') {
        ledger.worldState[key] = {
            docType: 'inmueble',
            id: args.id,
            titulo: args.titulo,
            propietarioId: args.propietarioId,
            direccion: args.direccion,
            estado: 'disponible',
            verificacionEstado: 'verificado',
            hashTituloPropiedad: args.hashTituloPropiedad,
            timestamp
        };
    } else if (txName === 'transferirPropiedad') {
        if (ledger.worldState[key]) {
            ledger.worldState[key].propietarioId = args.nuevoPropietarioId;
            ledger.worldState[key].hashTituloPropiedad = args.nuevoHashTitulo;
            ledger.worldState[key].timestamp = timestamp;
        }
    } else if (txName === 'crearContrato') {
        ledger.worldState[key] = {
            docType: 'contrato',
            id: args.id,
            inmuebleId: args.inmuebleId,
            propietarioId: args.propietarioId,
            inquilinoId: args.inquilinoId,
            montoAlquiler: parseFloat(args.montoAlquiler),
            montoDeposito: parseFloat(args.montoDeposito),
            fechaInicio: args.fechaInicio,
            fechaFin: args.fechaFin,
            firmas: { propietario: '', inquilino: '' },
            estado: 'pendiente',
            timestamp
        };
    } else if (txName === 'firmarContrato') {
        if (ledger.worldState[key]) {
            ledger.worldState[key].firmas[args.rolUsuario] = args.hashFirmaDigital;
            ledger.worldState[key].timestamp = timestamp;
            if (ledger.worldState[key].firmas.propietario && ledger.worldState[key].firmas.inquilino) {
                ledger.worldState[key].estado = 'activo';
                const inmId = ledger.worldState[key].inmuebleId;
                if (ledger.worldState[inmId]) {
                    ledger.worldState[inmId].estado = 'ocupado';
                }
            }
        }
    } else if (txName === 'finalizarContrato') {
        if (ledger.worldState[key]) {
            ledger.worldState[key].estado = args.nuevoEstado || 'finalizado';
            ledger.worldState[key].timestamp = timestamp;
            const inmId = ledger.worldState[key].inmuebleId;
            if (ledger.worldState[inmId]) {
                ledger.worldState[inmId].estado = 'disponible';
            }
        }
    } else if (txName === 'registrarPago') {
        ledger.worldState[key] = {
            docType: 'pago',
            id: args.id,
            contratoId: args.contratoId,
            monto: parseFloat(args.monto),
            fecha: args.fecha,
            tipoPago: args.tipoPago,
            stripeTransactionId: args.stripeTransactionId,
            timestamp
        };
    }

    const blockNumber = ledger.blocks.length + 1;
    const prevHash = blockNumber > 1 ? ledger.blocks[ledger.blocks.length - 1].blockHash : '0000000000000000000000000000000000000000000000000000000000000000';
    
    const newBlock = {
        blockNumber,
        prevHash,
        timestamp,
        transactions: [transaction]
    };
    newBlock.blockHash = calculateBlockHash(newBlock);

    ledger.blocks.push(newBlock);
    writeSimulatedLedger(ledger);

    return {
        txId,
        blockNumber,
        blockHash: newBlock.blockHash,
        timestamp,
        asset: ledger.worldState[key]
    };
}

module.exports = {
    readSimulatedLedger,
    writeSimulatedLedger,
    simulateTransaction
};
