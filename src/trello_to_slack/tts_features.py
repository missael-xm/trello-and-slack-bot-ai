# src/trello_to_slack/tts_features.py - CORREGIDO
from slack.slack_features import SlackFeatures
from assistant.ecommerce_assistant import EcommerceAssistant
# CAMBIAR: from langchain_openai import ChatOpenAI
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from typing import Union
import json
from datetime import datetime
from database.mongo_db import MongoDB
from services.assignment_service import AssignmentService

# IMPORT CORREGIDO - usar la versión de community
try:
    from langchain_community.callbacks import get_openai_callback
except ImportError:
    # Fallback para versiones antiguas
    from langchain.callbacks import get_openai_callback

class TrelloToSlackFeatures(SlackFeatures, EcommerceAssistant):
    """
    Orquestador principal que conecta Trello → IA → Slack.
    Hereda de SlackFeatures y EcommerceAssistant para tener todas las funcionalidades.
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
        self.assignment_service = AssignmentService()

    def comment_on_slack(self) -> Union[None, str]:
        """
        Ejecuta la cadena completa de IA y envía el resultado a Slack.
        Monitorea el costo de OpenAI con get_openai_callback().
        """
        try:
            # Inicializar callback como None por si falla
            cb = None
            
            # Usar try/except para el callback ya que puede fallar en algunas versiones
            try:
                from langchain_community.callbacks import get_openai_callback
                with get_openai_callback() as callback:
                    self.message = self.get_answer(event_type=self.event_type)
                    cb = callback
                    print("\nOpenAI Usage Cost:\n", cb, "\n")
            except ImportError:
                try:
                    from langchain.callbacks import get_openai_callback
                    with get_openai_callback() as callback:
                        self.message = self.get_answer(event_type=self.event_type)
                        cb = callback
                        print("\nOpenAI Usage Cost:\n", cb, "\n")
                except Exception:
                    # Si falla el callback, ejecutar sin él
                    print("⚠️  No se pudo inicializar OpenAI callback, ejecutando sin tracking...")
                    self.message = self.get_answer(event_type=self.event_type)

            # Convertir Pydantic model a dict si es necesario
            if hasattr(self.message, 'dict'):
                self.message = self.message.dict()

            # Verificar la estructura del mensaje
            if isinstance(self.message, dict):
                # Si tiene la clave 'translation', usarla
                if 'translation' in self.message:
                    translation_data = self.message['translation']
                else:
                    # Si no tiene 'translation', usar el mensaje completo
                    translation_data = self.message
            else:
                print(f"❌ Invalid message format: {type(self.message)}")
                return f"Invalid message format: {type(self.message)}"

            # 🆕 GUARDAR DATOS DE ANALYTICS ANTES DE ENVIAR A SLACK
            self._save_analytics_data(translation_data, cb)

            # Validar si hay tasks para enviar
            if (
                isinstance(translation_data, dict) and
                'translated_tasks' in translation_data and
                not translation_data['translated_tasks']
            ):
                return "No new task requests found"

            # Convertir el formato del translator al formato que espera Slack
            slack_message = self._convert_to_slack_format(translation_data)
            
            print(f"📋 SLACK MESSAGE FORMAT: {slack_message}")

            # Enviar a Slack (nuevo mensaje o respuesta en hilo)
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

    def _convert_to_slack_format(self, translation_data: dict) -> dict:
        """Convierte el formato y asigna tareas inteligentemente"""
        try:
            tasks_markdown = ""
            assigned_tasks = []
            
            if 'translated_tasks' in translation_data and translation_data['translated_tasks']:
                for task in translation_data['translated_tasks']:
                    if isinstance(task, dict) and 'description' in task:
                        # ASIGNACIÓN INTELIGENTE
                        assignment = self._assign_task_to_member(task)
                        
                        task_text = f"• {task['description']}\n"
                        task_text += f"  👤 Asignado a: <@{assignment.slack_id}> ({assignment.member_name})\n"
                        task_text += f"  🎯 Confianza: {assignment.confidence_score:.0%}\n"
                        task_text += f"  ⏱️ Estimado: {assignment.estimated_completion_time}h\n"
                        task_text += f"  📋 Razón: {assignment.reason}\n"
                        
                        if 'category' in task:
                            task_text += f"  📁 Categoría: {task['category']}\n"
                        if 'priority' in task:
                            task_text += f"  🚨 Prioridad: {task['priority']}\n"
                        if 'complexity' in task:
                            task_text += f"  🧩 Complejidad: {task['complexity']}\n"
                        
                        tasks_markdown += task_text + "\n"
                        assigned_tasks.append(assignment)
            
            # Agregar resumen del equipo
            team_metrics = self.assignment_service.get_team_metrics()
            summary = f"*Resumen del Equipo:*\n"
            summary += f"• Miembros disponibles: {team_metrics.available_members}/{team_metrics.total_members}\n"
            summary += f"• Tareas asignadas: {team_metrics.total_tasks_assigned}\n"
            summary += f"• Tasa de completación: {team_metrics.completion_rate:.1f}%\n"
            
            if team_metrics.busy_members:
                summary += f"• Miembros muy ocupados: {len(team_metrics.busy_members)}\n"
            
            tasks_markdown = summary + "\n" + tasks_markdown
            
            # Usar el summary como título o crear uno por defecto
            title = translation_data.get('summary', 'Tareas de desarrollo asignadas')
            
            return {
                'title': title,
                'tasks': tasks_markdown.strip(),
                'assigned_tasks': assigned_tasks  # Para analytics
            }
            
        except Exception as e:
            print(f"❌ Error converting to Slack format: {e}")
            return {
                'title': 'Tareas de desarrollo',
                'tasks': 'Error procesando las tareas'
            }

    def _assign_task_to_member(self, task: dict) -> AssignmentResult:
        """Asignar tarea a miembro del equipo"""
        required_skills = task.get('required_skills', [])
        complexity = task.get('complexity', 'moderada')
        
        # Calcular horas estimadas
        estimated_hours = 4.0  # default
        if 'time_estimate' in task and isinstance(task['time_estimate'], dict):
            time_est = task['time_estimate']
            if 'realistic' in time_est:
                estimated_hours = time_est['realistic']
        
        return self.assignment_service.assign_task(
            task=task,
            required_skills=required_skills,
            complexity=complexity,
            estimated_hours=estimated_hours
        )

    def _save_analytics_data(self, translation_data: dict, openai_callback) -> None:
        """
        Guarda datos de analytics con métricas por persona
        """
        try:
            # Solo guardar si hay tareas válidas
            if not isinstance(translation_data, dict) or not translation_data.get('translated_tasks'):
                print("📊 No analytics data to save (no valid tasks)")
                return

            # Calcular métricas básicas
            tasks = translation_data.get('translated_tasks', [])
            total_tasks = len(tasks)
            
            # Calcular horas totales estimadas (usando realistic estimate si está disponible)
            total_estimated_hours = 0
            for task in tasks:
                if isinstance(task, dict) and 'time_estimate' in task:
                    time_est = task['time_estimate']
                    if isinstance(time_est, dict) and 'realistic' in time_est:
                        total_estimated_hours += time_est['realistic']
                    else:
                        # Estimación por defecto basada en complejidad
                        total_estimated_hours += 4.0  # 4 horas por defecto

            # Obtener información del solicitante CORREGIDA
            requested_by = "unknown"
            recent_comment_text = ""
            
            # CORREGIDO: Acceso correcto a atributos del objeto Pydantic
            if hasattr(self, 'main_data') and self.main_data:
                # main_data es un objeto TrelloActionMainData, no un dict
                requested_by = getattr(self.main_data, 'username', 'unknown')
                recent_comment_text = getattr(self.main_data, 'comment', '')
            else:
                # Fallback si no hay main_data
                requested_by = getattr(self, 'recent_comment', 'unknown').split('author: ')[-1].split(' -')[0] if 'author:' in getattr(self, 'recent_comment', '') else 'unknown'

            member_metrics = {}
            team_metrics = self.assignment_service.get_team_metrics()

            for member in self.assignment_service.team_members.values():
                member_metrics[member.slack_id] = {
                    "name": member.name,
                    "current_tasks": member.current_tasks,
                    "completed_tasks": member.completed_tasks,
                    "weekly_capacity": member.weekly_capacity,
                    "current_weekly_hours": member.current_weekly_hours,
                    "success_rate": member.success_rate,
                    "avg_completion_time": member.avg_completion_time,
                    "available": member.available,
                    "skills": member.skills,
                    "skill_level": member.skill_level.value
                }

            analytics_data.update({
                "team_metrics": team_metrics.dict(),
                "member_metrics": member_metrics,
                "assignment_details": [task.dict() for task in (assigned_tasks or [])],
                "workload_distribution": team_metrics.workload_distribution,
                "skill_coverage": team_metrics.skill_coverage
            })

            # Preparar datos para analytics
            analytics_data = {
                "project_id": f"proj_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{self.card_id[-6:]}",
                "card_id": self.card_id,
                "card_title": self.card_title,
                "requested_by": requested_by,
                "request_date": datetime.utcnow(),
                "original_comment": recent_comment_text,
                "total_tasks": total_tasks,
                "total_estimated_hours": total_estimated_hours,
                "average_complexity": self._calculate_average_complexity(tasks),
                "highest_priority": self._get_highest_priority(tasks),
                "risk_assessment": self._assess_overall_risk(tasks),
                "category_distribution": self._calculate_category_distribution(tasks),
                "priority_distribution": self._calculate_priority_distribution(tasks),
                "complexity_distribution": self._calculate_complexity_distribution(tasks),
                "tasks": tasks,
                "required_skills": self._extract_required_skills(tasks),
                "skill_frequency": self._calculate_skill_frequency(tasks),
                "status": "pending",
                "progress_percentage": 0.0,
                "ai_model_used": getattr(self.llm, 'model_name', 'unknown'),
                "processing_time": openai_callback.total_seconds if openai_callback and hasattr(openai_callback, 'total_seconds') else 0,
                "confidence_score": 0.8,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_analysis_update": datetime.utcnow()
            }

            # Guardar en MongoDB
            db = MongoDB()
            db.analytics_collection.insert_one(analytics_data)
            print(f"✅ Analytics data saved for project: {analytics_data['project_id']}")
            print(f"📊 Saved {total_tasks} tasks, {total_estimated_hours} estimated hours")
            
        except Exception as e:
            print(f"❌ Error saving analytics data: {e}")
            import traceback
            traceback.print_exc()

    # 🆕 MÉTODOS AUXILIARES PARA CÁLCULOS DE ANALYTICS
    def _calculate_average_complexity(self, tasks: list) -> str:
        """Calcula la complejidad promedio de las tareas"""
        if not tasks:
            return "simple"
        
        complexity_values = {
            "simple": 1,
            "moderada": 2, 
            "compleja": 3,
            "muy_compleja": 4
        }
        
        total = 0
        count = 0
        
        for task in tasks:
            if isinstance(task, dict) and 'complexity' in task:
                complexity = task['complexity']
                if complexity in complexity_values:
                    total += complexity_values[complexity]
                    count += 1
        
        if count == 0:
            return "simple"
        
        average = total / count
        
        if average < 1.5:
            return "simple"
        elif average < 2.5:
            return "moderada"
        elif average < 3.5:
            return "compleja"
        else:
            return "muy_compleja"

    def _get_highest_priority(self, tasks: list) -> str:
        """Obtiene la prioridad más alta entre las tareas"""
        if not tasks:
            return "media"
        
        priority_values = {
            "baja": 1,
            "media": 2,
            "alta": 3, 
            "crítica": 4
        }
        
        highest_priority = "media"
        highest_value = 0
        
        for task in tasks:
            if isinstance(task, dict) and 'priority' in task:
                priority = task['priority']
                if priority in priority_values and priority_values[priority] > highest_value:
                    highest_value = priority_values[priority]
                    highest_priority = priority
        
        return highest_priority

    def _assess_overall_risk(self, tasks: list) -> str:
        """Evalúa el riesgo general del proyecto"""
        if not tasks:
            return "bajo"
        
        high_priority_count = 0
        complex_count = 0
        
        for task in tasks:
            if isinstance(task, dict):
                if task.get('priority') in ['alta', 'crítica']:
                    high_priority_count += 1
                if task.get('complexity') in ['compleja', 'muy_compleja']:
                    complex_count += 1
        
        total_tasks = len(tasks)
        high_priority_ratio = high_priority_count / total_tasks
        complex_ratio = complex_count / total_tasks
        
        if high_priority_ratio > 0.5 or complex_ratio > 0.7:
            return "alto"
        elif high_priority_ratio > 0.3 or complex_ratio > 0.4:
            return "medio"
        else:
            return "bajo"

    def _calculate_category_distribution(self, tasks: list) -> dict:
        """Calcula la distribución de tareas por categoría"""
        distribution = {}
        
        for task in tasks:
            if isinstance(task, dict) and 'category' in task:
                category = task['category']
                distribution[category] = distribution.get(category, 0) + 1
        
        return distribution

    def _calculate_priority_distribution(self, tasks: list) -> dict:
        """Calcula la distribución de tareas por prioridad"""
        distribution = {}
        
        for task in tasks:
            if isinstance(task, dict) and 'priority' in task:
                priority = task['priority']
                distribution[priority] = distribution.get(priority, 0) + 1
        
        return distribution

    def _calculate_complexity_distribution(self, tasks: list) -> dict:
        """Calcula la distribución de tareas por complejidad"""
        distribution = {}
        
        for task in tasks:
            if isinstance(task, dict) and 'complexity' in task:
                complexity = task['complexity']
                distribution[complexity] = distribution.get(complexity, 0) + 1
        
        return distribution

    def _extract_required_skills(self, tasks: list) -> list:
        """Extrae la lista única de habilidades requeridas"""
        skills = set()
        
        for task in tasks:
            if isinstance(task, dict) and 'required_skills' in task:
                task_skills = task['required_skills']
                if isinstance(task_skills, list):
                    skills.update(task_skills)
        
        return list(skills)

    def _calculate_skill_frequency(self, tasks: list) -> dict:
        """Calcula la frecuencia de cada habilidad requerida"""
        skill_count = {}
        
        for task in tasks:
            if isinstance(task, dict) and 'required_skills' in task:
                task_skills = task['required_skills']
                if isinstance(task_skills, list):
                    for skill in task_skills:
                        skill_count[skill] = skill_count.get(skill, 0) + 1
        
        return skill_count