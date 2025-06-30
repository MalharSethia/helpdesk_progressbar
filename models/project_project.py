from odoo import models, fields, api
import json
import logging

_logger = logging.getLogger(__name__)

class ProjectProject(models.Model):
    _inherit = 'project.project'

    task_progress_data = fields.Text(
        string='Task Progress Data',
        compute='_compute_task_progress_data',
        store=False,
        help='JSON data containing task progress information for visualization'
    )
    
    total_tasks = fields.Integer(
        string='Total Tasks',
        compute='_compute_task_progress_data',
        store=False
    )

    @api.depends('task_ids', 'task_ids.stage_id', 'task_ids.active')
    def _compute_task_progress_data(self):
        for project in self:
            try:
                # Initialize default values
                project.total_tasks = 0
                project.task_progress_data = json.dumps({
                    'segments': [],
                    'total': 0
                })
                
                # Get all active tasks for this project
                if not project.task_ids:
                    continue
                    
                tasks = project.task_ids.filtered(lambda t: t.active)
                total_tasks = len(tasks)
                
                project.total_tasks = total_tasks
                
                if total_tasks == 0:
                    continue
                
                # Group tasks by stage
                stage_counts = {}
                stage_info = {}
                
                for task in tasks:
                    stage = task.stage_id
                    if stage:
                        stage_id = stage.id
                        if stage_id not in stage_counts:
                            stage_counts[stage_id] = 0
                            # Get proper color for this specific stage
                            stage_color = self._get_correct_stage_color(stage.name)
                            stage_info[stage_id] = {
                                'name': stage.name or 'Unnamed Stage',
                                'color': stage_color,
                                'fold': bool(stage.fold),
                                'sequence': stage.sequence or 0
                            }
                        stage_counts[stage_id] += 1
                    else:
                        # Handle tasks without stage
                        if 'no_stage' not in stage_counts:
                            stage_counts['no_stage'] = 0
                            stage_info['no_stage'] = {
                                'name': 'No Stage',
                                'color': '#95a5a6',
                                'fold': False,
                                'sequence': 999
                            }
                        stage_counts['no_stage'] += 1
                
                # Calculate percentages and create segments
                segments = []
                for stage_id, count in stage_counts.items():
                    if count > 0:
                        percentage = (count / total_tasks) * 100
                        info = stage_info[stage_id]
                        segments.append({
                            'stage_id': str(stage_id),
                            'name': info['name'],
                            'count': count,
                            'percentage': round(percentage, 1),
                            'color': info['color'],
                            'fold': info['fold'],
                            'sequence': info['sequence']
                        })
                
                # Sort segments by sequence
                segments.sort(key=lambda x: (x['sequence'], x['name']))
                
                project.task_progress_data = json.dumps({
                    'segments': segments,
                    'total': total_tasks
                })
                
            except Exception as e:
                _logger.error("Error computing task progress data for project %s: %s", project.id, str(e))
                project.total_tasks = 0
                project.task_progress_data = json.dumps({
                    'segments': [],
                    'total': 0
                })
    
    def _get_correct_stage_color(self, stage_name):
        """Get the correct color for the 5 specific stage categories"""
        if not stage_name:
            return '#95a5a6'
            
        stage_name_clean = stage_name.lower().strip()
        
        # Exact matches for your 5 categories
        if stage_name_clean == 'in progress':
            return '#95a5a6'  # Grey
        elif stage_name_clean == 'changes requested':
            return '#f39c12'  # Orange
        elif stage_name_clean == 'approved':
            return '#2ecc71'  # Green
        elif stage_name_clean == 'canceled' or stage_name_clean == 'cancelled':
            return '#e74c3c'  # Red
        elif stage_name_clean == 'done':
            return '#27ae60'  # Dark Green
        
        # Partial matches as fallback
        elif 'progress' in stage_name_clean:
            return '#95a5a6'  # Grey
        elif 'change' in stage_name_clean or 'request' in stage_name_clean:
            return '#f39c12'  # Orange
        elif 'approv' in stage_name_clean:
            return '#2ecc71'  # Green
        elif 'cancel' in stage_name_clean:
            return '#e74c3c'  # Red
        elif 'done' in stage_name_clean or 'complete' in stage_name_clean:
            return '#27ae60'  # Dark Green
        else:
            return '#9b59b6'  # Purple for unrecognized stages
