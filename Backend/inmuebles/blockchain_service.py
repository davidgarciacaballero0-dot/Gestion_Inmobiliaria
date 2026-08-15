import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# URL por defecto del API Gateway de Blockchain en puerto 4000
BLOCKCHAIN_URL = getattr(settings, 'BLOCKCHAIN_GATEWAY_URL', 'http://localhost:4000/api/blockchain')

class BlockchainService:
    """
    Cliente de Servicio para comunicar el Backend Django con la Red Blockchain
    vía el API Blockchain Gateway en Node.js.
    """

    @staticmethod
    def _post(endpoint, payload):
        try:
            url = f"{BLOCKCHAIN_URL}/{endpoint}"
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"Error en Blockchain Gateway [{endpoint}]: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Blockchain Gateway offline o lento para [{endpoint}]: {str(e)}")
            return None

    @staticmethod
    def _put(endpoint, payload):
        try:
            url = f"{BLOCKCHAIN_URL}/{endpoint}"
            response = requests.put(url, json=payload, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error en Blockchain Gateway [{endpoint}]: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Blockchain Gateway offline o lento para [{endpoint}]: {str(e)}")
            return None

    @staticmethod
    def registrar_inmueble(inmueble_id, titulo, propietario_id, direccion_str, hash_titulo):
        """
        Registra el título de propiedad verificado criptográficamente en la Blockchain.
        """
        payload = {
            "id": f"INM-{inmueble_id}",
            "titulo": titulo,
            "propietarioId": f"USR-{propietario_id}",
            "direccion": direccion_str,
            "hashTituloPropiedad": hash_titulo
        }
        logger.info(f"Sincronizando inmueble {inmueble_id} con Blockchain...")
        return BlockchainService._post("inmuebles", payload)

    @staticmethod
    def transferir_propiedad(inmueble_id, nuevo_propietario_id, nuevo_hash_titulo):
        """
        Registra la transferencia de dominio de un inmueble en la Blockchain.
        """
        payload = {
            "id": f"INM-{inmueble_id}",
            "nuevoPropietarioId": f"USR-{nuevo_propietario_id}",
            "nuevoHashTitulo": nuevo_hash_titulo
        }
        logger.info(f"Sincronizando transferencia de propiedad de inmueble {inmueble_id}...")
        return BlockchainService._put("inmuebles/transferir", payload)

    @staticmethod
    def registrar_contrato(contrato_id, inmueble_id, propietario_id, inquilino_id, monto, deposito, inicio_str, fin_str):
        """
        Registra los términos de un borrador de contrato de arrendamiento en la Blockchain.
        """
        payload = {
            "id": f"CON-{contrato_id}",
            "inmuebleId": f"INM-{inmueble_id}",
            "propietarioId": f"USR-{propietario_id}",
            "inquilinoId": f"USR-{inquilino_id}",
            "montoAlquiler": float(monto),
            "montoDeposito": float(deposito),
            "fechaInicio": str(inicio_str),
            "fechaFin": str(fin_str) if fin_str else ""
        }
        logger.info(f"Sincronizando borrador de contrato {contrato_id} con Blockchain...")
        return BlockchainService._post("contratos", payload)

    @staticmethod
    def registrar_firma_contrato(contrato_id, rol_usuario, hash_firma_digital):
        """
        Registra la firma criptográfica digital de un propietario o inquilino en la Blockchain.
        """
        payload = {
            "id": f"CON-{contrato_id}",
            "rolUsuario": rol_usuario, # 'propietario' o 'inquilino'
            "hashFirmaDigital": hash_firma_digital
        }
        logger.info(f"Sincronizando firma digital del {rol_usuario} para contrato {contrato_id}...")
        return BlockchainService._put("contratos/firmar", payload)

    @staticmethod
    def registrar_pago(pago_id, contrato_id, monto, fecha_str, tipo_pago, transaction_id):
        """
        Registra de manera inmutable el recibo de un pago verificado (Stripe, Efectivo, QR).
        """
        payload = {
            "id": f"PAG-{pago_id}",
            "contratoId": f"CON-{contrato_id}",
            "monto": float(monto),
            "fecha": str(fecha_str),
            "tipoPago": tipo_pago,
            "stripeTransactionId": transaction_id or ""
        }
        logger.info(f"Sincronizando recibo de pago {pago_id} en Blockchain...")
        return BlockchainService._post("pagos", payload)

    @staticmethod
    def obtener_historial(asset_id):
        """
        Lee el historial de auditoría inmutable de un activo (Inmueble, Contrato o Recibo).
        """
        try:
            url = f"{BLOCKCHAIN_URL}/historial/{asset_id}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error consultando historial blockchain para {asset_id}: {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            logger.warning(f"No se pudo conectar al Blockchain Gateway para historial de {asset_id}: {str(e)}")
            return []

    @staticmethod
    def obtener_stats():
        """
        Obtiene las estadísticas generales de la red blockchain (bloques, estado de conexión, etc.).
        """
        try:
            url = f"{BLOCKCHAIN_URL}/stats"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error consultando estadísticas blockchain: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"No se pudo conectar al Blockchain Gateway para estadísticas: {str(e)}")
            return None
