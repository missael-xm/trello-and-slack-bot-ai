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

    def comment_on_slack(self) -> Union[None, str]:
        """
        Ejecuta la cadena completa de IA y envía el resultado a Slack.
        Monitorea el costo de OpenAI con get_openai_callback().
        """
        try:
            with get_openai_callback() as cb:
                self.message = self.get_answer(event_type=self.event_type)
                print("\nOpenAI Usage Cost:\n", cb, "\n")

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
        """Convierte el formato del translator al formato que espera Slack"""
        try:
            # Extraer las tareas y convertirlas a formato markdown
            tasks_markdown = ""
            if 'translated_tasks' in translation_data and translation_data['translated_tasks']:
                for task in translation_data['translated_tasks']:
                    if isinstance(task, dict) and 'description' in task:
                        tasks_markdown += f"• {task['description']}\n"
            
            # Usar el summary como título o crear uno por defecto
            title = translation_data.get('summary', 'Tareas de desarrollo')
            
            # Crear el formato que espera Slack
            slack_format = {
                'title': title,
                'tasks': tasks_markdown.strip()
            }
            
            return slack_format
            
        except Exception as e:
            print(f"❌ Error converting to Slack format: {e}")
            # Fallback: devolver formato básico
            return {
                'title': 'Tareas de desarrollo',
                'tasks': 'Error procesando las tareas'
            }

    def _save_analytics_data(self, translation_data: dict, openai_callback) -> None:
        """
        🆕 NUEVO MÉTODO: Guarda datos de analytics en MongoDB
        para el dashboard
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

            # Preparar datos para analytics
            analytics_data = {
                "project_id": f"proj_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{self.card_id[-6:]}",
                "card_id": self.card_id,
                "card_title": self.card_title,
                "requested_by": getattr(self, 'main_data', {}).get('username', 'unknown'),
                "request_date": datetime.utcnow(),
                "original_comment": getattr(self, 'recent_comment', ''),
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
                "ai_model_used": getattr(self.llm, 'model_name', 'gpt-4'),
                "processing_time": openai_callback.total_seconds if hasattr(openai_callback, 'total_seconds') else 0,
                "confidence_score": 0.8,  # Podría calcularse basado en la respuesta
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