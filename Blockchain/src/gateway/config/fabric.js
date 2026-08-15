'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const grpc = require('@grpc/grpc-js');
const { connect, signers } = require('@hyperledger/fabric-gateway');

const PEER_ENDPOINT = process.env.PEER_ENDPOINT || '34.133.189.201:7051';
const PEER_HOST_ALIAS = process.env.PEER_HOST_ALIAS || 'peer0.org1.autogestion.com';
const MSP_ID = process.env.PEER_MSPID || 'Org1MSP';
const CHANNEL_NAME = process.env.CHANNEL_NAME || 'autogestion-channel';
const CHAINCODE_NAME = process.env.CHAINCODE_NAME || 'autogestion';

// Rutas locales de los criptomateriales copiados
const CRYPTO_PATH = path.resolve(__dirname, '..', '..', '..', 'fabric-network', 'crypto-config');
const TLS_CERT_PATH = path.resolve(CRYPTO_PATH, 'peerOrganizations/org1.autogestion.com/peers/peer0.org1.autogestion.com/tls/ca.crt');

// Resolución dinámica para el certificado (soporta Admin@org1.autogestion.com-cert.pem o cert.pem)
const SIGN_CERTS_DIR = path.resolve(CRYPTO_PATH, 'peerOrganizations/org1.autogestion.com/users/Admin@org1.autogestion.com/msp/signcerts');
let CERT_PATH = '';
if (fs.existsSync(SIGN_CERTS_DIR)) {
    const files = fs.readdirSync(SIGN_CERTS_DIR);
    const pemFile = files.find(f => f.endsWith('.pem'));
    if (pemFile) {
        CERT_PATH = path.join(SIGN_CERTS_DIR, pemFile);
    }
}
if (!CERT_PATH) {
    CERT_PATH = path.resolve(SIGN_CERTS_DIR, 'cert.pem');
}

// Resolución dinámica para la llave privada en keystore (soporta priv_sk o hashes generados por cryptogen)
const KEYSTORE_DIR = path.resolve(CRYPTO_PATH, 'peerOrganizations/org1.autogestion.com/users/Admin@org1.autogestion.com/msp/keystore');
let KEY_PATH = '';
if (fs.existsSync(KEYSTORE_DIR)) {
    const files = fs.readdirSync(KEYSTORE_DIR);
    const skFile = files.find(f => f.endsWith('_sk') || f.includes('priv') || f.includes('key'));
    if (skFile) {
        KEY_PATH = path.join(KEYSTORE_DIR, skFile);
    } else if (files.length > 0) {
        KEY_PATH = path.join(KEYSTORE_DIR, files[0]);
    }
}
if (!KEY_PATH) {
    KEY_PATH = path.resolve(KEYSTORE_DIR, 'priv_sk');
}

let gatewayInstance = null;
let grpcClientInstance = null;

async function getGateway() {
    if (gatewayInstance) {
        return gatewayInstance;
    }

    try {
        if (!fs.existsSync(TLS_CERT_PATH) || !fs.existsSync(CERT_PATH) || !fs.existsSync(KEY_PATH)) {
            throw new Error(`Criptomateriales faltantes en las rutas especificadas. TLS: ${fs.existsSync(TLS_CERT_PATH)} (path: ${TLS_CERT_PATH}), Cert: ${fs.existsSync(CERT_PATH)} (path: ${CERT_PATH}), Key: ${fs.existsSync(KEY_PATH)} (path: ${KEY_PATH})`);
        }

        const tlsCert = fs.readFileSync(TLS_CERT_PATH);
        const credentials = grpc.credentials.createSsl(tlsCert);

        // Crear cliente gRPC
        grpcClientInstance = new grpc.Client(PEER_ENDPOINT, credentials, {
            'grpc.ssl_target_name_override': PEER_HOST_ALIAS,
            'grpc.default_authority': PEER_HOST_ALIAS
        });

        const certPem = fs.readFileSync(CERT_PATH).toString();
        const keyPem = fs.readFileSync(KEY_PATH).toString();

        const identity = { mspId: MSP_ID, credentials: Buffer.from(certPem) };
        const signer = signers.newPrivateKeySigner(crypto.createPrivateKey(keyPem));

        gatewayInstance = connect({
            client: grpcClientInstance,
            identity,
            signer,
            evaluateOptions: () => ({ deadline: Date.now() + 10000 }),
            endorseOptions: () => ({ deadline: Date.now() + 20000 }),
            submitOptions: () => ({ deadline: Date.now() + 10000 }),
            commitOptions: () => ({ deadline: Date.now() + 60000 }),
        });

        console.log(`⛓️ Conexión establecida exitosamente con el Gateway de Fabric en ${PEER_ENDPOINT}`);
        return gatewayInstance;
    } catch (err) {
        console.error(`❌ Error al conectar al Gateway de Fabric: ${err.message}`);
        throw err;
    }
}

async function getContract() {
    const gw = await getGateway();
    const network = gw.getNetwork(CHANNEL_NAME);
    return network.getContract(CHAINCODE_NAME);
}

/**
 * Envía una transacción de escritura al smart contract.
 */
async function submitTransaction(txName, ...args) {
    try {
        const contract = await getContract();
        console.log(`📤 Enviando transacción [${txName}] con argumentos:`, args);
        
        const commitResult = await contract.submitTransaction(txName, ...args);
        const utf8Decoder = new TextDecoder();
        const resultString = utf8Decoder.decode(commitResult);
        
        let asset = {};
        if (resultString) {
            try {
                asset = JSON.parse(resultString);
            } catch (e) {
                asset = resultString;
            }
        }
        
        return {
            success: true,
            txId: contract.chaincodeName, // o txId si es accesible
            timestamp: new Date().toISOString(),
            asset
        };
    } catch (err) {
        console.error(`❌ Error en submitTransaction [${txName}]: ${err.message}`);
        throw err;
    }
}

/**
 * Evalúa una transacción de lectura (consulta) del smart contract.
 */
async function evaluateTransaction(txName, ...args) {
    try {
        const contract = await getContract();
        console.log(`🔍 Evaluando consulta [${txName}] con argumentos:`, args);
        
        const resultBytes = await contract.evaluateTransaction(txName, ...args);
        const utf8Decoder = new TextDecoder();
        const resultString = utf8Decoder.decode(resultBytes);
        
        return JSON.parse(resultString);
    } catch (err) {
        console.error(`❌ Error en evaluateTransaction [${txName}]: ${err.message}`);
        throw err;
    }
}

module.exports = {
    submitTransaction,
    evaluateTransaction,
    getGateway
};
