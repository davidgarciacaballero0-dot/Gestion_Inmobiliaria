import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import {
  ShieldCheck,
  ShieldAlert,
  DollarSign,
  FileText,
  Calendar,
  Sparkles,
  X,
  CheckCircle2,
  AlertCircle,
  UserCheck,
  Clock,
  Award,
  Download,
  Percent,
  Check,
} from 'lucide-react';
import scoringInquilinoService from '../services/scoringInquilinoService';
import './ScoringInquilinoModal.css';

export default function ScoringInquilinoModal({ usuarioId, onClose }) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [descargandoPdf, setDescargandoPdf] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // Bloquear scroll de la página de fondo al abrir el modal
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  useEffect(() => {
    const cargarScoring = async () => {
      setLoading(true);
      setErrorMsg(null);
      try {
        let resp;
        if (usuarioId) {
          resp = await scoringInquilinoService.obtenerScoringInquilino(usuarioId);
        } else {
          resp = await scoringInquilinoService.obtenerMiScoringPasaporte();
        }
        setData(resp);
      } catch (err) {
        console.error('Error cargando scoring de inquilino:', err);
        setErrorMsg('No se pudo obtener el reporte de scoring de este perfil.');
      } finally {
        setLoading(false);
      }
    };

    cargarScoring();
  }, [usuarioId]);

  // Manejador de descarga de PDF oficial
  const handleDescargarPDF = async () => {
    setDescargandoPdf(true);
    try {
      let blob;
      if (usuarioId) {
        blob = await scoringInquilinoService.descargarPasaportePDF(usuarioId);
      } else {
        blob = await scoringInquilinoService.descargarMiPasaportePDF();
      }

      const url = window.URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Pasaporte_Digital_Inquilino_${data?.nombre_completo || 'Reporte'}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error descargando PDF de pasaporte:', err);
      alert('No se pudo generar el documento PDF en este momento.');
    } finally {
      setDescargandoPdf(false);
    }
  };

  return createPortal(
    <div className="scoring-modal-overlay">
      <div className="scoring-modal-card">
        {/* Header */}
        <div className="scoring-modal-header">
          <div className="header-brand-box">
            <div className="header-icon-shield">
              <ShieldCheck size={24} />
            </div>
            <div>
              <h3>Pasaporte Digital & Evaluación de Inquilino</h3>
              <p>Score de Confiabilidad y Análisis Financiero respaldado por Inteligencia Artificial</p>
            </div>
          </div>
          <button className="btn-close-scoring" onClick={onClose} title="Cerrar modal">
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="scoring-modal-body">
          {loading && (
            <div className="scoring-loading-state">
              <Sparkles size={36} className="scoring-spin-svg" />
              <p>Consultando antecedentes de pago, identidad y comportamiento...</p>
            </div>
          )}

          {errorMsg && (
            <div className="scoring-error-banner">
              <AlertCircle size={18} />
              <span>{errorMsg}</span>
            </div>
          )}

          {data && !loading && (
            <div className="scoring-content-layout">
              {/* Tarjeta Principal de Puntuación Global */}
              <div className="score-hero-card">
                <div className="score-gauge-box">
                  <div className={`score-circle-badge ${data.color_badge}`}>
                    <span className="score-number">{data.score_total}</span>
                    <span className="score-scale">/ 100 pts</span>
                  </div>
                </div>

                <div className="score-hero-details">
                  <div className="risk-level-row">
                    <span className="candidate-name-badge">{data.nombre_completo}</span>
                    <span className={`risk-tag ${data.color_badge}`}>
                      Riesgo {data.nivel_riesgo}
                    </span>
                    <span className="recommendation-pill">
                      {data.recomendacion_estado}
                    </span>
                  </div>

                  {/* Dictamen de IA (Groq Llama 3.3) */}
                  <div className="ai-dictamen-container">
                    <div className="ai-dictamen-header">
                      <Sparkles size={14} />
                      <span>Dictamen Ejecutivo de Riesgo (IA):</span>
                    </div>
                    <p>{data.justificacion_ia}</p>
                  </div>
                </div>
              </div>

              {/* Recomendación de Garantía Dinámica & Esfuerzo Financiero */}
              <div className="guarantee-dynamic-card">
                <div className="guarantee-card-header">
                  <DollarSign size={16} />
                  <h5>Recomendación Contractual y Garantía Dinámica:</h5>
                </div>
                <div className="guarantee-grid">
                  <div className="guarantee-item">
                    <span className="guarantee-item-label">Garantía Sugerida:</span>
                    <p className="guarantee-item-val">{data.garantia_sugerida}</p>
                  </div>
                  <div className="guarantee-item">
                    <span className="guarantee-item-label">Capacidad de Pago:</span>
                    <p className="guarantee-item-val highlight">{data.esfuerzo_financiero}</p>
                  </div>
                  <div className="guarantee-item">
                    <span className="guarantee-item-label">Beneficio Comercial:</span>
                    <p className="guarantee-item-val">{data.descuento_garantia_sugerido}</p>
                  </div>
                </div>
              </div>

              {/* Desglose de los 4 Pilares */}
              <div className="pillars-grid">
                {/* Pilar 1: Pagos */}
                <div className="pillar-card">
                  <div className="pillar-header">
                    <div className="pillar-icon-box green">
                      <DollarSign size={16} />
                    </div>
                    <div>
                      <h6>Historial de Pagos</h6>
                      <span className="pillar-score">
                        {data.pilares?.pagos?.score} / {data.pilares?.pagos?.maximo} pts
                      </span>
                    </div>
                  </div>
                  <div className="progress-bar-bg">
                    <div
                      className="progress-bar-fill green"
                      style={{
                        width: `${(data.pilares?.pagos?.score / data.pilares?.pagos?.maximo) * 100}%`,
                      }}
                    />
                  </div>
                  <p className="pillar-desc">{data.pilares?.pagos?.detalle}</p>
                </div>

                {/* Pilar 2: Documentos */}
                <div className="pillar-card">
                  <div className="pillar-header">
                    <div className="pillar-icon-box blue">
                      <FileText size={16} />
                    </div>
                    <div>
                      <h6>Identidad y Verificación</h6>
                      <span className="pillar-score">
                        {data.pilares?.documentos?.score} / {data.pilares?.documentos?.maximo} pts
                      </span>
                    </div>
                  </div>
                  <div className="progress-bar-bg">
                    <div
                      className="progress-bar-fill blue"
                      style={{
                        width: `${(data.pilares?.documentos?.score / data.pilares?.documentos?.maximo) * 100}%`,
                      }}
                    />
                  </div>
                  <div className="doc-tags-list">
                    {Array.isArray(data.pilares?.documentos?.detalle) &&
                      data.pilares.documentos.detalle.map((doc, idx) => (
                        <span key={idx} className="doc-tag">
                          ✓ {doc}
                        </span>
                      ))}
                  </div>
                </div>

                {/* Pilar 3: Comportamiento */}
                <div className="pillar-card">
                  <div className="pillar-header">
                    <div className="pillar-icon-box purple">
                      <Calendar size={16} />
                    </div>
                    <div>
                      <h6>Citas y Cumplimiento</h6>
                      <span className="pillar-score">
                        {data.pilares?.comportamiento?.score} / {data.pilares?.comportamiento?.maximo} pts
                      </span>
                    </div>
                  </div>
                  <div className="progress-bar-bg">
                    <div
                      className="progress-bar-fill purple"
                      style={{
                        width: `${(data.pilares?.comportamiento?.score / data.pilares?.comportamiento?.maximo) * 100}%`,
                      }}
                    />
                  </div>
                  <p className="pillar-desc">{data.pilares?.comportamiento?.detalle}</p>
                </div>

                {/* Pilar 4: Antigüedad */}
                <div className="pillar-card">
                  <div className="pillar-header">
                    <div className="pillar-icon-box amber">
                      <Clock size={16} />
                    </div>
                    <div>
                      <h6>Estabilidad y Antigüedad</h6>
                      <span className="pillar-score">
                        {data.pilares?.antiguedad?.score} / {data.pilares?.antiguedad?.maximo} pts
                      </span>
                    </div>
                  </div>
                  <div className="progress-bar-bg">
                    <div
                      className="progress-bar-fill amber"
                      style={{
                        width: `${(data.pilares?.antiguedad?.score / data.pilares?.antiguedad?.maximo) * 100}%`,
                      }}
                    />
                  </div>
                  <p className="pillar-desc">{data.pilares?.antiguedad?.detalle}</p>
                </div>
              </div>

              {/* Insignias de Confiabilidad */}
              <div className="badges-section">
                <h6>Insignias de Verificación del Inquilino:</h6>
                <div className="badges-chips-row">
                  {data.insignias?.map((badge, idx) => (
                    <div
                      key={idx}
                      className={`badge-chip-pro ${badge.activa ? 'active' : 'inactive'}`}
                    >
                      <Award size={14} />
                      <span>{badge.titulo}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer con Acción de Descarga PDF */}
        <div className="scoring-modal-footer">
          {data && (
            <button
              type="button"
              className="btn-download-passport-pdf"
              onClick={handleDescargarPDF}
              disabled={descargandoPdf}
            >
              <Download size={16} />
              <span>{descargandoPdf ? 'Generando PDF...' : 'Descargar Pasaporte Digital (PDF)'}</span>
            </button>
          )}
          <button type="button" className="btn-close-action" onClick={onClose}>
            Entendido
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
