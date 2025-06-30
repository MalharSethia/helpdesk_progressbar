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
                            stage_info[stage_id] = {
                                'name': stage.name or 'Unnamed Stage',
                                'color': self._get_stage_color_by_name(stage.name),
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
                                'color': '#95a5a6',  # Default gray color
                                'fold': False,
                                'sequence': 999
                            }
                        stage_counts['no_stage'] += 1
                
                # Calculate percentages and create segments
                segments = []
                for stage_id, count in stage_counts.items():
                    if count > 0:  # Only add segments with tasks
                        percentage = (count / total_tasks) * 100
                        info = stage_info[stage_id]
                        segments.append({
                            'stage_id': str(stage_id),  # Ensure it's a string for JSON
                            'name': info['name'],
                            'count': count,
                            'percentage': round(percentage, 1),
                            'color': info['color'],
                            'fold': info['fold'],
                            'sequence': info['sequence']
                        })
                
                # Sort segments by sequence, then by folded status
                segments.sort(key=lambda x: (x['sequence'], x['fold'], x['name']))
                
                project.task_progress_data = json.dumps({
                    'segments': segments,
                    'total': total_tasks
                })
                
            except Exception as e:
                _logger.error("Error computing task progress data for project %s: %s", project.id, str(e))
                # Fallback in case of any error
                project.total_tasks = 0
                project.task_progress_data = json.dumps({
                    'segments': [],
                    'total': 0
                })
    
    def _get_stage_color_by_name(self, stage_name):
        """Get color for stage based on its name matching the 5 categories"""
        if not stage_name:
            return '#95a5a6'  # Default gray
            
        stage_name_lower = stage_name.lower()
        
        # Map the 5 specific stage categories to colors
        if 'in progress' in stage_name_lower or 'progress' in stage_name_lower:
            return '#95a5a6'  # Grey - In Progress
        elif 'changes requested' in stage_name_lower or 'changes' in stage_name_lower or 'requested' in stage_name_lower:
            return '#f39c12'  # Orange - Changes Requested  
        elif 'approved' in stage_name_lower or 'approve' in stage_name_lower:
            return '#2ecc71'  # Green - Approved
        elif 'cancel' in stage_name_lower or 'cancelled' in stage_name_lower:
            return '#e74c3c'  # Red - Cancelled
        elif 'done' in stage_name_lower or 'complete' in stage_name_lower or 'finished' in stage_name_lower:
            return '#27ae60'  # Dark Green - Done
        else:
            # Fallback: use sequence-based colors for other stages
            return '#9b59b6'  # Purple - Other stages
