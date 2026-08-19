import api from './api';

const scoringInquilinoService = {
  /**
   * Obtiene la evaluación y scoring de un inquilino / candidato por ID
   * @param {number|string} usuarioId
   */
  obtenerScoringInquilino: async (usuarioId) => {
    const response = await api.get(`/usuarios/scoring-inquilino/${usuarioId}/`);
    return response.data;
  },

  /**
   * Obtiene el propio pasaporte de scoring del usuario logueado
   */
  obtenerMiScoringPasaporte: async () => {
    const response = await api.get('/usuarios/mi-scoring-pasaporte/');
    return response.data;
  },

  /**
   * Descarga el PDF del Pasaporte Digital de un inquilino
   * @param {number|string} usuarioId
   */
  descargarPasaportePDF: async (usuarioId) => {
    const response = await api.get(`/usuarios/scoring-inquilino/${usuarioId}/pdf/`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Descarga el PDF del propio Pasaporte Digital del usuario logueado
   */
  descargarMiPasaportePDF: async () => {
    const response = await api.get('/usuarios/mi-scoring-pasaporte/pdf/', {
      responseType: 'blob',
    });
    return response.data;
  },
};

export default scoringInquilinoService;

