# src/trello_to_slack/tts_features.py
from slack.slack_features import SlackFeatures
from assistant.ecommerce_assistant import EcommerceAssistant
from langchain.chat_models import ChatOpenAI
from typing import Union
import json
from datetime import datetime
from database.mongo_db import MongoDB

# Importación segura para callbacks (compatibilidad v1/v2)
try:
    from langchain_community.callbacks import get_openai_callback
except ImportError:
    from langchain.callbacks import get_openai_callback

# Importación segura del servicio de asignación
try:
    from services.assignment_service import AssignmentService, AssignmentResult
except ImportError:
    print("⚠️ AssignmentService no disponible, se usará lógica básica.")
    AssignmentService = None
    AssignmentResult = None

class TrelloToSlackFeatures(SlackFeatures, EcommerceAssistant):
    """
    Orquestador principal: Trello -> IA -> Asignación -> Slack/DB.
    Versión FINAL con asignación única por lote y persistencia completa de métricas.
    """
    def __init__(
        self,
        llm: ChatOpenAI = None,
        card_comment_history: list = [],
        recent_comment: str = "",
        card_id: str = "",
        card_title: str = "",
        shop_link: str = "",
        message: dict = {},
        slack_message_data: Union[None, dict] = None,
        event_type: str = "",
    ) -> None:
        SlackFeatures.__init__(self)
        EcommerceAssistant.__init__(
            self,
            llm=llm,
            trello_card_id=card_id,
            card_comment_history=card_comment_history,
            recent_comment=recent_comment,
        )
        self.card_id = card_id
        self.card_title = card_title
        self.shop_link = shop_link
        self.message = message
        self.slack_message_data = slack_message_data
        self.event_type = event_type
        
        # Inicializar servicio de asignación si está disponible
        if AssignmentService:
            self.assignment_service = AssignmentService()
        else:
            self.assignment_service = None

    def comment_on_slack(self) -> Union[None, str]:
        """
        Ejecuta el flujo completo:
        1. Obtiene respuesta de la IA (Traducción y tareas).
        2. Realiza la asignación inteligente (LOTE).
        3. Guarda métricas completas en MongoDB.
        4. Envía mensaje formateado a Slack.
        """
        try:
            cb = None
            try:
                with get_openai_callback() as callback:
                    self.message = self.get_answer(event_type=self.event_type)
                    cb = callback
                    print("\nOpenAI Usage Cost:\n", cb, "\n")
            except Exception as e:
                print(f"⚠️ Callback error (continuando): {e}")
                self.message = self.get_answer(event_type=self.event_type)

            # Asegurar formato diccionario
            if hasattr(self.message, 'dict'):
                self.message = self.message.dict()

            translation_data = {}
            if isinstance(self.message, dict):
                translation_data = self.message.get('translation', self.message)
            
            # --- PASO CLAVE: ASIGNACIÓN POR LOTE ---
            tasks = translation_data.get('translated_tasks', [])
            batch_assignment = None
            
            if tasks and self.assignment_service:
                print(f"🔄 Calculando asignación para lote de {len(tasks)} tareas...")
                # Asigna todo el grupo de tareas a la mejor persona disponible
                batch_assignment = self.assignment_service.assign_batch(tasks)
                if batch_assignment:
                    print(f"👤 Responsable seleccionado: {batch_assignment.member_name}")

            # 1. GUARDAR ANALYTICS (Pasamos la asignación de lote)
            # Esto guarda horas, riesgos, skills y el responsable en Mongo
            self._save_analytics_data(translation_data, cb, batch_assignment)

            if not tasks:
                return "No new task requests found"

            # 2. GENERAR MENSAJE SLACK (Formato limpio con un solo responsable)
            slack_message = self._convert_to_slack_format(translation_data, batch_assignment)
            
            print(f"📋 Enviando a Slack: {slack_message.get('title')}")

            # 3. ENVIAR A SLACK
            if self.slack_message_data is None:
                self.new_message(
                    request_id=self.card_id,
                    title=self.card_title,
                    message=slack_message,
                    shop_link=self.shop_link,
                )
            else:
                self.send_message_in_the_thread(
                    message=slack_message,
                    slack_message_data=self.slack_message_data,
                )

            return json.dumps(self.message, indent=2, default=str)
            
        except Exception as e:
            print(f"❌ Error in comment_on_slack: {e}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}"

    def _convert_to_slack_format(self, translation_data: dict, batch_assignment=None) -> dict:
        """
        Genera el mensaje de Slack.
        Muestra al 'Responsable del Proyecto' al inicio y luego lista las tareas.
        """
        try:
            tasks_markdown = ""
            sanitized_assigned_tasks = []
            
            # SECCIÓN 1: RESPONSABLE ÚNICO
            if batch_assignment:
                tasks_markdown += f"👑 *Responsable del Proyecto:* <@{batch_assignment.slack_id}> ({batch_assignment.member_name})\n"
                tasks_markdown += f"⏱️ *Carga Total Estimada:* {batch_assignment.estimated_completion_time}h\n"
                tasks_markdown += "──────────────────────\n"
                
                # Guardar para el JSON de retorno (sanitizado)
                if hasattr(batch_assignment, 'dict'):
                    sanitized_assigned_tasks.append(batch_assignment.dict())
                else:
                    sanitized_assigned_tasks.append(batch_assignment.__dict__)

            # SECCIÓN 2: LISTA DE TAREAS
            if 'translated_tasks' in translation_data:
                for task in translation_data['translated_tasks']:
                    # Descripción principal
                    task_text = f"• *{task.get('description', 'Tarea sin descripción')}*\n"
                    
                    # Detalles técnicos en una línea discreta
                    details = []
                    if 'priority' in task:
                        details.append(f"🚨 {task['priority']}")
                    if 'time_estimate' in task:
                        # Manejo robusto de float o dict
                        val = task['time_estimate']
                        if isinstance(val, dict): val = val.get('realistic', 4.0)
                        details.append(f"⏱️ {val}h")
                    if 'complexity' in task:
                        details.append(f"🧩 {task['complexity']}")
                    
                    if details:
                        task_text += f"  _({', '.join(details)})_\n"
                    
                    tasks_markdown += task_text + "\n"
            
            # SECCIÓN 3: ESTADO DEL EQUIPO (Pie de página)
            if self.assignment_service:
                try:
                    metrics = self.assignment_service.get_team_metrics()
                    tasks_markdown += f"\n*📊 Estado Equipo:* {metrics.available_members} disponibles | {metrics.completion_rate:.0f}% completado global"
                except Exception:
                    pass

            title = translation_data.get('summary', 'Nuevas Tareas Asignadas')
            
            return {
                'title': title,
                'tasks': tasks_markdown.strip(),
                'assigned_tasks': sanitized_assigned_tasks
            }
            
        except Exception as e:
            print(f"❌ Error formatting Slack message: {e}")
            return {
                'title': 'Error de Formato',
                'tasks': 'Ocurrió un error al generar el mensaje.',
                'assigned_tasks': []
            }

    def _save_analytics_data(self, translation_data: dict, openai_callback, batch_assignment=None) -> list:
        """
        Guarda todos los datos analíticos en MongoDB.
        Calcula métricas agregadas (riesgo, complejidad) para el dashboard.
        """
        try:
            tasks = translation_data.get('translated_tasks', [])
            if not tasks:
                return []

            # Calcular total de horas sumando las tareas individuales
            total_hours = 0
            for t in tasks:
                val = t.get('time_estimate', 4.0)
                if isinstance(val, dict):
                    val = val.get('realistic', 4.0)
                try:
                    total_hours += float(val)
                except:
                    total_hours += 4.0

            # Obtener solicitante
            requested_by = "unknown"
            original_comment = ""
            try:
                if hasattr(self, 'main_data') and self.main_data:
                    requested_by = getattr(self.main_data, 'username', 'unknown')
                    original_comment = getattr(self.main_data, 'comment', '')
                else:
                    recent_comment = getattr(self, 'recent_comment', '')
                    if 'author:' in recent_comment:
                        requested_by = recent_comment.split('author: ')[-1].split(' -')[0]
            except:
                pass

            # Preparar detalle de asignación para Mongo
            analytics_assignments = []
            if batch_assignment:
                assignment_dict = batch_assignment.dict() if hasattr(batch_assignment, 'dict') else batch_assignment.__dict__
                analytics_assignments.append(assignment_dict)

            # Construir documento completo
            analytics_data = {
                "project_id": f"proj_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(self.card_id)[-6:]}",
                "card_id": self.card_id,
                "card_title": self.card_title,
                "requested_by": requested_by,
                "original_comment": original_comment,
                "request_date": datetime.utcnow(),
                
                # Métricas cuantitativas
                "total_tasks": len(tasks),
                "total_estimated_hours": total_hours,
                "status": "pending",
                
                # Asignación (Líder único)
                "assigned_lead": batch_assignment.member_name if batch_assignment else "Unassigned",
                "assigned_lead_id": batch_assignment.slack_id if batch_assignment else None,
                
                # Métricas cualitativas (Calculadas con helpers)
                "average_complexity": self._calculate_average_complexity(tasks),
                "highest_priority": self._get_highest_priority(tasks),
                "risk_assessment": self._assess_overall_risk(tasks),
                
                # Distribuciones
                "category_distribution": self._calculate_distribution(tasks, 'category'),
                "priority_distribution": self._calculate_distribution(tasks, 'priority'),
                "required_skills": self._extract_skills(tasks),
                
                # Datos crudos
                "tasks": tasks,
                "assignment_details": analytics_assignments,
                
                # Metadata IA
                "ai_model_used": getattr(self.llm, 'model_name', 'unknown'),
                "created_at": datetime.utcnow()
            }

            # Guardar en Mongo
            db = MongoDB()
            if db.analytics_collection is not None:
                db.analytics_collection.insert_one(analytics_data)
                print(f"✅ Analytics SAVED: {analytics_data['project_id']} ({total_hours}h)")

            return analytics_assignments
            
        except Exception as e:
            print(f"❌ Error saving analytics: {e}")
            import traceback
            traceback.print_exc()
            return []

    # --- HELPERS PARA CÁLCULOS DE ANALYTICS ---

    def _calculate_average_complexity(self, tasks: list) -> str:
        """Promedia la complejidad numérica y devuelve etiqueta"""
        if not tasks: return "simple"
        mapping = {'simple': 1, 'moderada': 2, 'compleja': 3, 'muy_compleja': 4}
        
        total = 0
        for t in tasks:
            c = t.get('complexity', 'moderada')
            total += mapping.get(c, 2)
            
        avg = total / len(tasks)
        if avg <= 1.5: return "simple"
        if avg <= 2.5: return "moderada"
        if avg <= 3.5: return "compleja"
        return "muy_compleja"

    def _assess_overall_risk(self, tasks: list) -> str:
        """Calcula riesgo basado en tareas críticas/complejas"""
        if not tasks: return "bajo"
        high_pri = 0
        complex_tasks = 0
        
        for t in tasks:
            if t.get('priority') in ['alta', 'crítica']: high_pri += 1
            if t.get('complexity') in ['compleja', 'muy_compleja']: complex_tasks += 1
            
        ratio_high = high_pri / len(tasks)
        ratio_complex = complex_tasks / len(tasks)
        
        if ratio_high > 0.5 or ratio_complex > 0.5: return "alto"
        if ratio_high > 0.2 or ratio_complex > 0.2: return "medio"
        return "bajo"

    def _get_highest_priority(self, tasks: list) -> str:
        """Encuentra la prioridad máxima"""
        if not tasks: return "media"
        priority_map = {'baja': 1, 'media': 2, 'alta': 3, 'crítica': 4}
        max_p = 0
        max_label = "media"
        
        for t in tasks:
            p = t.get('priority', 'media')
            val = priority_map.get(p, 2)
            if val > max_p:
                max_p = val
                max_label = p
        return max_label

    def _calculate_distribution(self, tasks: list, field: str) -> dict:
        """Genera histograma para cualquier campo (categoría, prioridad)"""
        dist = {}
        for t in tasks:
            val = t.get(field, 'unknown')
            dist[val] = dist.get(val, 0) + 1
        return dist

    def _extract_skills(self, tasks: list) -> list:
        """Extrae lista única de habilidades de todas las tareas"""
        skills = set()
        for t in tasks:
            task_skills = t.get('required_skills', [])
            if isinstance(task_skills, list):
                skills.update(task_skills)
            elif isinstance(task_skills, str):
                skills.add(task_skills)
        return list(skills)