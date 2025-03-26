import logging
from airflow.models import TaskInstance
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

from dags.utils.data_enrichment import (
    get_open_corporates_data, check_sanctions, 
    query_wikidata, check_pep_list, check_adverse_news
)

logger = logging.getLogger(__name__)

class EntityTaskGroup:
    """
    Creates a group of tasks for processing entities (organizations or people).
    """
    
    @staticmethod
    def create_org_tasks(dag, parent_task, entity_list):
        """
        Create organization processing tasks within a task group.
        
        Args:
            dag: The parent DAG
            parent_task: The parent task these tasks should follow
            entity_list: List of organizations to process
            
        Returns:
            task_group: The task group containing all organization tasks
            task_ids: List of task IDs created
        """
        with TaskGroup(group_id='org_enrichment', dag=dag) as task_group:
            task_ids = []
            
            for org in entity_list:
                org_name = org.get('name', '')
                if not org_name:
                    continue
                    
                org_key = org_name.replace(' ', '_')
                logger.info(f"Creating enrichment tasks for organization: {org_name}")
                
                # OpenCorporates task
                opencorporates_task = PythonOperator(
                    task_id=f'opencorporates_{org_key}',
                    python_callable=get_open_corporates_data,
                    op_args=[org],
                    provide_context=True,
                    dag=dag,
                )
                
                # Sanctions task for organization
                sanctions_task = PythonOperator(
                    task_id=f'sanctions_org_{org_key}',
                    python_callable=check_sanctions,
                    op_args=['Company', org_name],
                    provide_context=True,
                    dag=dag,
                )
                
                # Wikidata task for organization
                wikidata_task = PythonOperator(
                    task_id=f'wikidata_{org_key}',
                    python_callable=query_wikidata,
                    op_args=[org_name],
                    provide_context=True,
                    dag=dag,
                )
                
                # Adverse news task for organization
                news_task = PythonOperator(
                    task_id=f'news_org_{org_key}',
                    python_callable=check_adverse_news,
                    op_args=[org_name],
                    provide_context=True,
                    dag=dag,
                )
                
                parent_task >> opencorporates_task
                parent_task >> sanctions_task
                parent_task >> wikidata_task
                parent_task >> news_task
                
                task_ids.extend([
                    f'opencorporates_{org_key}',
                    f'sanctions_org_{org_key}',
                    f'wikidata_{org_key}',
                    f'news_org_{org_key}'
                ])
                
            return task_group, task_ids
    
    @staticmethod
    def create_people_tasks(dag, parent_task, person_list, prefix=''):
        """
        Create person processing tasks within a task group.
        
        Args:
            dag: The parent DAG
            parent_task: The parent task these tasks should follow
            person_list: List of people to process
            prefix: Optional prefix for task IDs (e.g., 'wiki_' for Wikidata-discovered people)
            
        Returns:
            task_group: The task group containing all person tasks
            task_ids: List of task IDs created
        """
        group_id = f'{prefix}people_enrichment' if prefix else 'people_enrichment'
        
        with TaskGroup(group_id=group_id, dag=dag) as task_group:
            task_ids = []
            
            for person in person_list:
                person_name = person.get('name', '')
                if not person_name:
                    continue
                    
                person_key = person_name.replace(' ', '_')
                logger.info(f"Creating enrichment tasks for person: {person_name}")
                
                # Task ID prefix based on source
                id_prefix = f"{prefix}" if prefix else ""
                
                # PEP task for person
                pep_task = PythonOperator(
                    task_id=f'{id_prefix}pep_{person_key}',
                    python_callable=check_pep_list,
                    op_args=[person_name],
                    provide_context=True,
                    dag=dag,
                )
                
                # Sanctions task for person
                sanctions_task = PythonOperator(
                    task_id=f'{id_prefix}sanctions_person_{person_key}',
                    python_callable=check_sanctions,
                    op_args=['Person', person_name],
                    provide_context=True,
                    dag=dag,
                )
                
                # Adverse news task for person
                news_task = PythonOperator(
                    task_id=f'{id_prefix}news_person_{person_key}',
                    python_callable=check_adverse_news,
                    op_args=[person_name],
                    provide_context=True,
                    dag=dag,
                )
                
                parent_task >> pep_task
                parent_task >> sanctions_task
                parent_task >> news_task
                
                task_ids.extend([
                    f'{id_prefix}pep_{person_key}',
                    f'{id_prefix}sanctions_person_{person_key}',
                    f'{id_prefix}news_person_{person_key}'
                ])
                
            return task_group, task_ids