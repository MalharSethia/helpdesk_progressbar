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
                                'color': self._get_stage_color(stage),
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
    
    def _get_stage_color(self, stage):
        """Get color for stage based on its properties"""
        try:
            # Use stage color if available
            if hasattr(stage, 'color') and stage.color is not False:
                # Convert Odoo color index to actual color
                color_map = {
                    0: '#FFFFFF', 1: '#FF0000', 2: '#FF8000', 3: '#FFFF00',
                    4: '#80FF00', 5: '#00FF00', 6: '#00FF80', 7: '#00FFFF',
                    8: '#0080FF', 9: '#0000FF', 10: '#8000FF', 11: '#FF00FF'
                }
                return color_map.get(stage.color, '#95a5a6')
            
            # Fallback: Map stage properties to colors
            stage_name_lower = (stage.name or '').lower()
            
            if stage.fold:
                # Folded stages (usually done/cancelled)
                if any(keyword in stage_name_lower for keyword in ['done', 'complete', 'finish', 'close', 'resolved']):
                    return '#2ecc71'  # Green for completed
                elif any(keyword in stage_name_lower for keyword in ['cancel', 'reject', 'abort', 'fail']):
                    return '#e74c3c'  # Red for cancelled
                else:
                    return '#95a5a6'  # Gray for other folded stages
            else:
                # Active stages - use progression colors based on sequence
                sequence = stage.sequence or 0
                if sequence <= 1:
                    return '#3498db'  # Blue - new/to do
                elif sequence <= 2:
                    return '#f39c12'  # Orange - in progress  
                elif sequence <= 3:
                    return '#9b59b6'  # Purple - review/testing
                else:
                    return '#1abc9c'  # Teal - ready to deploy
        except Exception as e:
            _logger.warning("Error getting stage color for stage %s: %s", stage.id if stage else 'None', str(e))
            return '#95a5a6'  # Default gray color
