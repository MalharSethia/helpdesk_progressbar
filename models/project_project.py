from odoo import models, fields, api
import json

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

    @api.depends('task_ids.stage_id', 'task_ids.active')
    def _compute_task_progress_data(self):
        for project in self:
            # Get all active tasks for this project
            tasks = project.task_ids.filtered(lambda t: t.active)
            total_tasks = len(tasks)
            
            project.total_tasks = total_tasks
            
            if total_tasks == 0:
                project.task_progress_data = json.dumps({
                    'segments': [],
                    'total': 0
                })
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
                            'name': stage.name,
                            'color': self._get_stage_color(stage),
                            'fold': stage.fold
                        }
                    stage_counts[stage_id] += 1
                else:
                    # Handle tasks without stage
                    if 'no_stage' not in stage_counts:
                        stage_counts['no_stage'] = 0
                        stage_info['no_stage'] = {
                            'name': 'No Stage',
                            'color': '#95a5a6',  # Default gray color
                            'fold': False
                        }
                    stage_counts['no_stage'] += 1
            
            # Calculate percentages and create segments
            segments = []
            for stage_id, count in stage_counts.items():
                percentage = (count / total_tasks) * 100
                segments.append({
                    'stage_id': stage_id,
                    'name': stage_info[stage_id]['name'],
                    'count': count,
                    'percentage': round(percentage, 1),
                    'color': stage_info[stage_id]['color'],
                    'fold': stage_info[stage_id]['fold']
                })
            
            # Sort segments by stage sequence or put folded stages at the end
            segments.sort(key=lambda x: (x['fold'], x['name']))
            
            project.task_progress_data = json.dumps({
                'segments': segments,
                'total': total_tasks
            })
    
    def _get_stage_color(self, stage):
        """Get color for stage based on its properties"""
        # Map stage properties to colors (similar to Odoo's default task colors)
        if stage.fold:
            # Folded stages (usually done/cancelled) - use completion colors
            if any(keyword in stage.name.lower() for keyword in ['done', 'complete', 'finish', 'close']):
                return '#2ecc71'  # Green for completed
            elif any(keyword in stage.name.lower() for keyword in ['cancel', 'reject', 'abort']):
                return '#e74c3c'  # Red for cancelled
            else:
                return '#95a5a6'  # Gray for other folded stages
        else:
            # Active stages - use progression colors
            stage_sequence = stage.sequence or 0
            colors = [
                '#3498db',  # Blue - new/to do
                '#f39c12',  # Orange - in progress
                '#9b59b6',  # Purple - review/testing
                '#1abc9c',  # Teal - ready to deploy
            ]
            return colors[min(stage_sequence, len(colors) - 1)]
