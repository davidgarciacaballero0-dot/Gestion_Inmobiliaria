import api from './api';

/**
 * Servicio para búsqueda geoespacial por mapa con Puntos de Interés e IA (RF-C2-06).
 */
const mapaBusquedaService = {
  /**
   * Realiza la búsqueda espacial en mapa calculando score de conveniencia y justificación IA.
   * @param {Object} searchPayload - { lat, lng, radio_km, puntos_interes, tipo_oferta, precio_max }
   * @returns {Promise<Object>} Resultado con total, centro, y lista de inmuebles procesados
   */
  buscarPorMapaIA: async (searchPayload) => {
    const { data } = await api.post('/inmuebles/busqueda-mapa-ia/', searchPayload);
    return data;
  },
};

export default mapaBusquedaService;
