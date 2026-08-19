import api from './api';

const busquedaSemanticaService = {
  /**
   * Realiza búsqueda semántica o multimodal enviando texto y/o archivo de imagen
   * @param {Object} params { descripcion, foto (File), imagen_base64, tipo_oferta, precio_max }
   */
  buscarSemanticaIA: async (params) => {
    if (params.foto && params.foto instanceof File) {
      const formData = new FormData();
      formData.append('foto', params.foto);
      if (params.descripcion) formData.append('descripcion', params.descripcion);
      if (params.tipo_oferta) formData.append('tipo_oferta', params.tipo_oferta);
      if (params.precio_max) formData.append('precio_max', params.precio_max);

      const response = await api.post('/inmuebles/busqueda-semantica-ia/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } else {
      const response = await api.post('/inmuebles/busqueda-semantica-ia/', {
        descripcion: params.descripcion,
        imagen_base64: params.imagen_base64,
        tipo_oferta: params.tipo_oferta,
        precio_max: params.precio_max,
      });
      return response.data;
    }
  },
};

export default busquedaSemanticaService;
