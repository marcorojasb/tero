"""Batería de pruebas de perfiles docentes chilenos (Teacher Personas).

Evalúa el comportamiento del asistente ante distintos roles y necesidades reales:
1. Profesora de Lenguaje y Comunicación (4° básico): Evaluación formativa, pauta y Decreto 67.
2. Profesor de Historia y Ciencias Sociales (8° básico): Trabajo con fuentes y catálogo curricular.
3. Educadora Diferencial (PIE): Adecuación NEE según Decreto 83/2015 (acceso vs objetivos).
4. Profesor Rural Multigrado: Aula unitaria, fotocopia y trabajo con material local sin conexión.
"""

from __future__ import annotations

from tero.types import ArtifactType, Encargo
from tero.workspace import Workspace
from tests.support import artifact_paths, open_session, rel


class TestProfesoraLenguaje:
    """Perfil 1: Profesora de Lenguaje y Comunicación de Enseñanza Básica."""

    def test_creacion_evaluacion_formativa_con_pauta_y_citas(self, workspace: Workspace):
        """Docente pide evaluación de comprensión lectora con pauta de corrección."""
        encargo = Encargo(
            curso="4° básico",
            asignatura="Lenguaje y Comunicación",
            oa="LEN-4B-OA04",
            duracion="45 min",
            tipo=ArtifactType.EVALUACION,
        )
        events: list[dict] = []
        session = open_session(workspace, encargo=encargo, events=events)

        # Primer turno: docente pide evaluación con pauta de corrección
        prompt = (
            "Necesito una evaluación de 45 minutos sobre el cuento de la carpeta. "
            "Debe incluir preguntas de extracción explícita y de inferencia, "
            "con una pauta de corrección detallada para retroalimentar según Decreto 67."
        )
        turn = session.start_turn(prompt)

        # El agente propone en memoria, no escribe directo
        assert session.phase == "esperando_aprobacion"
        assert turn.propuesta is not None
        assert turn.propuesta.accion == "crear"
        assert turn.propuesta.tipo in {ArtifactType.EVALUACION, ArtifactType.GUIA}
        assert turn.propuesta.vista_previa.strip()

        # Debe contener citas verificadas de las fuentes de la carpeta
        assert len(turn.propuesta.evidencias) >= 1
        assert any(e.verified for e in turn.propuesta.evidencias)

        # Sin aprobación, la carpeta sigue intacta
        assert artifact_paths(workspace) == []

        # Docente aprueba la propuesta
        result = session.aprobar()
        assert result.path is not None
        assert result.path.exists()
        assert result.path.parent.name == "derivados"

        # Verificar contenido de la evaluación escrita
        contenido = result.path.read_text(encoding="utf-8")
        assert "cuento" in contenido.lower() or "condor" in contenido.lower() or "huemul" in contenido.lower()


class TestProfesorHistoria:
    """Perfil 2: Profesor de Historia, Geografía y Ciencias Sociales."""

    def test_consulta_de_fuentes_locales_y_pensamiento_critico(self, workspace: Workspace):
        """Docente pregunta primero por las fuentes disponibles antes de encargar material."""
        encargo = Encargo(
            curso="8° básico",
            asignatura="Historia, Geografía y Ciencias Sociales",
        )
        events: list[dict] = []
        session = open_session(workspace, encargo=encargo, events=events)

        # Intención a: responder pregunta diagnóstica de la carpeta
        turn = session.start_turn("¿Qué documentos históricos o fuentes tengo disponibles en mi carpeta?")

        assert session.phase == "idle"
        assert turn.propuesta is None
        assert turn.respuesta.strip()
        assert "fuentes/" in turn.respuesta or "cuento" in turn.respuesta or "carpeta" in turn.respuesta.lower()
        assert artifact_paths(workspace) == []

    def test_catalogo_curricular_honesto(self, workspace: Workspace):
        """Docente consulta por un OA que no existe en el catálogo cargado."""
        encargo = Encargo(curso="8° básico", asignatura="Historia")
        session = open_session(workspace, encargo=encargo)

        turn = session.start_turn("¿Cuál es el OA 99 de Historia para 8° básico?")
        assert session.phase == "idle"
        assert turn.propuesta is None
        # No inventa una propuesta y responde en lenguaje natural
        assert turn.respuesta.strip()


class TestEducadoraDiferencialPIE:
    """Perfil 3: Educadora Diferencial aplicando Decreto 83/2015."""

    def test_adaptacion_nee_prioriza_acceso_antes_de_objetivos(self, workspace: Workspace):
        """Educadora adapta material existente especificando apoyos de acceso."""
        # Creamos primero una planificación base
        session1 = open_session(workspace)
        t1 = session1.start_turn("Prepara una planificación del cuento para 4° básico.")
        assert t1.propuesta is not None
        res = session1.aprobar()
        ruta_base = rel(workspace, res.path)

        # Educadora solicita adaptar para estudiante con TEA / TDAH
        events: list[dict] = []
        session2 = open_session(workspace, events=events)
        prompt_nee = (
            f"Adapta {ruta_base} para un estudiante con TDAH. Necesito adecuación de acceso "
            "con tiempo extendido y consignas paso a paso, manteniendo el objetivo intacto según Decreto 83."
        )
        turn_nee = session2.start_turn(prompt_nee)

        assert session2.phase == "esperando_aprobacion"
        assert turn_nee.propuesta is not None
        assert turn_nee.propuesta.accion == "adaptar"
        assert turn_nee.propuesta.origen == ruta_base

        # Validar notas NEE con estructura de Decreto 83
        assert len(turn_nee.propuesta.notas_nee) >= 1
        criterios = " ".join(turn_nee.propuesta.notas_nee).lower()
        assert any(palabra in criterios for palabra in ["acceso", "tiempo", "presentación", "paso"])

        # Aprobar y validar que se guardó en derivados como archivo nuevo
        res_nee = session2.aprobar()
        assert res_nee.path != res.path
        assert res_nee.path.exists()
        # El original no fue sobreescrito
        assert res.path.exists()


class TestProfesorRuralMultigrado:
    """Perfil 4: Profesor Rural en escuela multigrado."""

    def test_preparacion_material_para_fotocopia_offline(self, workspace: Workspace):
        """Docente rural sin internet solicita guía lista para imprimir y fotocopiar."""
        encargo = Encargo(
            curso="Multigrado 3° y 4° básico",
            asignatura="Lenguaje",
            duracion="90 min",
            tipo=ArtifactType.GUIA,
        )
        session = open_session(workspace, encargo=encargo)

        turn = session.start_turn(
            "Estoy en escuela rural sin internet. Prepara una guía de trabajo en papel "
            "sobre el texto local, que sea clara para fotocopiar y trabajar en el aula multigrado."
        )

        assert session.phase == "esperando_aprobacion"
        assert turn.propuesta is not None
        assert turn.propuesta.tipo == ArtifactType.GUIA

        # Vista previa estructurada y lista para usar
        vp = turn.propuesta.vista_previa
        assert "instrucciones" in vp.lower() or "actividad" in vp.lower() or "guía" in vp.lower()

        # Al aprobar, los originales permanecen inalterados
        antes = workspace.fingerprint_sources()
        session.aprobar()
        despues = workspace.fingerprint_sources()
        assert antes == despues
