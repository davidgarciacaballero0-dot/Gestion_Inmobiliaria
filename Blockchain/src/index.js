'use strict';

const app = require('./gateway/app');

const PORT = process.env.PORT || 4000;
const SIMULATE = process.env.SIMULATE_BLOCKCHAIN !== 'false';

// Iniciar servidor API Gateway
app.listen(PORT, () => {
    console.log(`========================================================================`);
    console.log(`🚀 API Blockchain Gateway iniciada exitosamente en puerto ${PORT}`);
    console.log(`📢 MODO DE OPERACIÓN: ${SIMULATE ? '🗂️ SIMULACIÓN (Ledger JSON)' : '🔗 PRODUCTION (Fabric peer)'}`);
    console.log(`📁 ESTRUCTURA: Nueva Arquitectura Multicapa (src/gateway/)`);
    console.log(`========================================================================`);
});
