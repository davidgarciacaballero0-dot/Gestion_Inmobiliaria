import api from './api';

/**
 * Servicio para gestionar versiones amobladas virtualmente con IA (Virtual Staging 360° y 2D).
 */
const stagingService = {
  /**
   * Obtiene todos los amoblados virtuales de un inmueble.
   * @param {number} inmuebleId 
   * @param {string} [tipo] 'foto_2d' | 'panorama360'
   */
  getByInmueble: async (inmuebleId, tipo = null) => {
    const params = { inmueble: inmuebleId };
    if (tipo) params.tipo = tipo;
    const response = await api.get('/inmuebles/amoblados/', { params });
    return response.data?.results || response.data || [];
  },

  /**
   * Genera una nueva versión amoblada con IA para una foto 2D o panorama 360°.
   * Acepta tanto un objeto { inmueble_id, multimedia_id, estilo, tipo } como argumentos posicionales.
   */
  generarAmoblado: async (paramsOrId, multimediaId = null, estilo = 'moderno', tipo = 'foto_2d') => {
    let payload = {};
    if (typeof paramsOrId === 'object' && paramsOrId !== null) {
      payload = {
        inmueble_id: paramsOrId.inmueble_id || paramsOrId.inmuebleId || paramsOrId.inmueble,
        multimedia_id: paramsOrId.multimedia_id || paramsOrId.multimediaId || null,
        estilo: paramsOrId.estilo || 'moderno',
        tipo: paramsOrId.tipo || 'foto_2d',
      };
    } else {
      payload = {
        inmueble_id: paramsOrId,
        multimedia_id: multimediaId,
        estilo,
        tipo,
      };
    }
    const response = await api.post('/inmuebles/amoblados/generar/', payload);
    return response.data?.data || response.data;
  },

  /**
   * Alias de generarAmoblado para compatibilidad
   */
  generar: async (...args) => {
    return stagingService.generarAmoblado(...args);
  },
};

export default stagingService;
