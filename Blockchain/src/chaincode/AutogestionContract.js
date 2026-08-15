'use strict';

const { Contract } = require('fabric-contract-api');

/**
 * Contrato Inteligente principal para Autogestión Inmobiliaria.
 * Define la lógica de negocio para la gestión inmutable de:
 * 1. Inmuebles (Verificación legal de títulos y posesión)
 * 2. Contratos (Ciclo de vida y firmas digitales de arrendamiento)
 * 3. Pagos (Auditoría inmutable de transacciones físicas y Stripe)
 */
class AutogestionContract extends Contract {

    constructor() {
        // Nombre del contrato para ser invocado desde la red
        super('AutogestionContract');
    }

    // =========================================================================
    //  GESTIÓN DE INMUEBLES Y TÍTULOS DE PROPIEDAD
    // =========================================================================

    /**
     * Registra un nuevo inmueble con su respectivo título de propiedad en el ledger.
     */
    async registrarInmueble(ctx, id, titulo, propietarioId, direccion, hashTituloPropiedad) {
        const exists = await this.assetExists(ctx, id);
        if (exists) {
            throw new Error(`El inmueble con ID ${id} ya está registrado en la Blockchain.`);
        }

        const inmueble = {
            docType: 'inmueble',
            id,
            titulo,
            propietarioId,
            direccion,
            estado: 'disponible', // disponible, ocupado, oculto
            verificacionEstado: 'verificado',
            hashTituloPropiedad, // Hash criptográfico SHA-256 del documento de Alodial / Título
            timestamp: ctx.stub.getTxTimestamp().seconds.toString()
        };

        const buffer = Buffer.from(JSON.stringify(inmueble));
        await ctx.stub.putState(id, buffer);
        
        console.log(`Inmueble ${id} registrado exitosamente para el propietario ${propietarioId}`);
        return JSON.stringify(inmueble);
    }

    /**
     * Transfiere la propiedad de un inmueble (compraventa o traspaso).
     */
    async transferirPropiedad(ctx, id, nuevoPropietarioId, nuevoHashTitulo) {
        const inmueble = await this.queryAsset(ctx, id);
        if (inmueble.docType !== 'inmueble') {
            throw new Error(`El activo con ID ${id} no es del tipo Inmueble.`);
        }

        const propietarioAnterior = inmueble.propietarioId;
        inmueble.propietarioId = nuevoPropietarioId;
        inmueble.hashTituloPropiedad = nuevoHashTitulo;
        inmueble.timestamp = ctx.stub.getTxTimestamp().seconds.toString();

        const buffer = Buffer.from(JSON.stringify(inmueble));
        await ctx.stub.putState(id, buffer);

        console.log(`Propiedad del inmueble ${id} transferida de ${propietarioAnterior} a ${nuevoPropietarioId}`);
        return JSON.stringify(inmueble);
    }

    // =========================================================================
    //  GESTIÓN DE CONTRATOS (ALQUILER, ANTICRÉTICO, ETC.)
    // =========================================================================

    /**
     * Registra un nuevo contrato en borrador.
     */
    async crearContrato(ctx, id, inmuebleId, propietarioId, inquilinoId, montoAlquiler, montoDeposito, fechaInicio, fechaFin) {
        const exists = await this.assetExists(ctx, id);
        if (exists) {
            throw new Error(`El contrato con ID ${id} ya existe en el Ledger.`);
        }

        const contrato = {
            docType: 'contrato',
            id,
            inmuebleId,
            propietarioId,
            inquilinoId,
            montoAlquiler: parseFloat(montoAlquiler),
            montoDeposito: parseFloat(montoDeposito),
            fechaInicio,
            fechaFin,
            firmas: {
                propietario: '',
                inquilino: ''
            },
            estado: 'pendiente', // pendiente, activo, finalizado, cancelado
            timestamp: ctx.stub.getTxTimestamp().seconds.toString()
        };

        const buffer = Buffer.from(JSON.stringify(contrato));
        await ctx.stub.putState(id, buffer);
        return JSON.stringify(contrato);
    }

    /**
     * Registra la firma digital criptográfica de una de las partes.
     * Al registrar ambas firmas, el contrato pasa automáticamente a estado 'activo'.
     */
    async firmarContrato(ctx, id, rolUsuario, hashFirmaDigital) {
        const contrato = await this.queryAsset(ctx, id);
        if (contrato.docType !== 'contrato') {
            throw new Error(`El activo con ID ${id} no es un Contrato.`);
        }

        if (rolUsuario !== 'propietario' && rolUsuario !== 'inquilino') {
            throw new Error('El rol para la firma debe ser "propietario" o "inquilino".');
        }

        contrato.firmas[rolUsuario] = hashFirmaDigital;
        contrato.timestamp = ctx.stub.getTxTimestamp().seconds.toString();

        // Si ambas partes firmaron, se activa el contrato
        if (contrato.firmas.propietario && contrato.firmas.inquilino) {
            contrato.estado = 'activo';
            
            // Opcional: Se podría actualizar el estado del inmueble asociado a 'ocupado'
            try {
                const inmueble = await this.queryAsset(ctx, contrato.inmuebleId);
                inmueble.estado = 'ocupado';
                await ctx.stub.putState(contrato.inmuebleId, Buffer.from(JSON.stringify(inmueble)));
            } catch (err) {
                // Si falla, solo registramos advertencia pero no rompemos la transacción principal
                console.warn(`No se pudo actualizar el estado del inmueble ${contrato.inmuebleId}: ${err.message}`);
            }
        }

        const buffer = Buffer.from(JSON.stringify(contrato));
        await ctx.stub.putState(id, buffer);
        return JSON.stringify(contrato);
    }

    /**
     * Resuelve o da por finalizado un contrato de mutuo acuerdo o por expiración.
     */
    async finalizarContrato(ctx, id, nuevoEstado = 'finalizado') {
        const contrato = await this.queryAsset(ctx, id);
        if (contrato.docType !== 'contrato') {
            throw new Error(`El activo con ID ${id} no es un Contrato.`);
        }

        contrato.estado = nuevoEstado;
        contrato.timestamp = ctx.stub.getTxTimestamp().seconds.toString();

        // Liberar el inmueble asociado
        try {
            const inmueble = await this.queryAsset(ctx, contrato.inmuebleId);
            inmueble.estado = 'disponible';
            await ctx.stub.putState(contrato.inmuebleId, Buffer.from(JSON.stringify(inmueble)));
        } catch (err) {
            console.warn(`No se pudo liberar el estado del inmueble ${contrato.inmuebleId}: ${err.message}`);
        }

        const buffer = Buffer.from(JSON.stringify(contrato));
        await ctx.stub.putState(id, buffer);
        return JSON.stringify(contrato);
    }

    // =========================================================================
    //  AUDITORÍA DE PAGOS (REGISTRO CRONOLÓGICO INMUTABLE)
    // =========================================================================

    /**
     * Registra un pago inmutablemente para auditoría cruzada.
     */
    async registrarPago(ctx, id, contratoId, monto, fecha, tipoPago, stripeTransactionId) {
        const exists = await this.assetExists(ctx, id);
        if (exists) {
            throw new Error(`El recibo de pago con ID ${id} ya existe en el Ledger.`);
        }

        const pago = {
            docType: 'pago',
            id,
            contratoId,
            monto: parseFloat(monto),
            fecha,
            tipoPago,
            stripeTransactionId, // Código de transacción del procesador externo
            timestamp: ctx.stub.getTxTimestamp().seconds.toString()
        };

        const buffer = Buffer.from(JSON.stringify(pago));
        await ctx.stub.putState(id, buffer);
        return JSON.stringify(pago);
    }

    // =========================================================================
    //  FUNCIONES AUXILIARES DE CONSULTA Y UTILITARIOS
    // =========================================================================

    /**
     * Retorna un activo específico por su ID.
     */
    async queryAsset(ctx, id) {
        const assetBytes = await ctx.stub.getState(id);
        if (!assetBytes || assetBytes.length === 0) {
            throw new Error(`El activo con ID ${id} no existe en el Ledger.`);
        }
        return JSON.parse(assetBytes.toString());
    }

    /**
     * Verifica si un activo existe en el Ledger.
     */
    async assetExists(ctx, id) {
        const assetBytes = await ctx.stub.getState(id);
        return assetBytes && assetBytes.length > 0;
    }

    /**
     * Retorna todo el historial cronológico de cambios de un activo (Auditoría Blockchain).
     */
    async obtenerHistorialActivo(ctx, id) {
        const iterator = await ctx.stub.getHistoryForKey(id);
        const results = [];
        let res = await iterator.next();
        
        while (!res.done) {
            if (res.value) {
                const value = res.value;
                const record = {};
                record.txId = value.txId;
                record.isDelete = value.isDelete;
                
                // Formatear timestamp de la transacción de forma robusta
                let seconds = 0;
                if (value.timestamp && value.timestamp.seconds) {
                    if (typeof value.timestamp.seconds.low === 'number') {
                        seconds = value.timestamp.seconds.low;
                    } else if (typeof value.timestamp.seconds.toNumber === 'function') {
                        seconds = value.timestamp.seconds.toNumber();
                    } else {
                        seconds = parseInt(value.timestamp.seconds, 10) || 0;
                    }
                }
                const date = new Date(seconds * 1000);
                record.timestamp = isNaN(date.getTime()) ? new Date().toISOString() : date.toISOString();
                
                try {
                    record.data = JSON.parse(value.value.toString('utf8'));
                } catch (err) {
                    record.data = value.value.toString('utf8');
                }
                
                results.push(record);
            }
            res = await iterator.next();
        }
        
        await iterator.close();
        return JSON.stringify(results);
    }
}

module.exports = AutogestionContract;
