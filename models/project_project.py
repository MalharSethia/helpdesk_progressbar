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
            try:
                tasks = project.task_ids.filtered(lambda t: t.active)
                total_tasks = len(tasks)
                project.total_tasks = total_tasks
                
                if total_tasks == 0:
                    project.task_progress_data = json.dumps({
                        'segments': [],
                        'total': 0
                    })
                    continue
                
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
                                'fold': stage.fold,
                                'sequence': stage.sequence or 0
                            }
                        stage_counts[stage_id] += 1
                    else:
                        if 'no_stage' not in stage_counts:
                            stage_counts['no_stage'] = 0
                            stage_info['no_stage'] = {
                                'name': 'No Stage',
                                'color': '#95a5a6',
                                'fold': False,
                                'sequence': 999
                            }
                        stage_counts['no_stage'] += 1
                
                segments = []
                for stage_id, count in stage_counts.items():
                    percentage = (count / total_tasks) * 100
                    info = stage_info[stage_id]
                    segments.append({
                        'stage_id': stage_id,
                        'name': info['name'],
                        'count': count,
                        'percentage': round(percentage, 1),
                        'color': info['color'],
                        'fold': info['fold'],
                        'sequence': info['sequence']
                    })
                
                segments.sort(key=lambda x: (x['sequence'], x['fold'], x['name']))
                
                project.task_progress_data = json.dumps({
                    'segments': segments,
                    'total': total_tasks
                })
                
            except Exception as e:
                project.total_tasks = 0
                project.task_progress_data = json.dumps({
                    'segments': [],
                    'total': 0
                })
    
    def _get_stage_color(self, stage):
        if hasattr(stage, 'color') and stage.color:
            color_map = {
                0: '#FFFFFF', 1: '#FF0000', 2: '#FF8000', 3: '#FFFF00',
                4: '#80FF00', 5: '#00FF00', 6: '#00FF80', 7: '#00FFFF',
                8: '#0080FF', 9: '#0000FF', 10: '#8000FF', 11: '#FF00FF'
            }
            return color_map.get(stage.color, '#95a5a6')
        
        stage_name_lower = stage.name.lower()
        
        if stage.fold:
            if any(keyword in stage_name_lower for keyword in ['done', 'complete', 'finish']):
                return '#2ecc71'
            elif any(keyword in stage_name_lower for keyword in ['cancel', 'reject']):
                return '#e74c3c'
            else:
                return '#95a5a6'
        else:
            sequence = stage.sequence or 0
            if sequence <= 1:
                return '#3498db'
            elif sequence <= 2:
                return '#f39c12'
            elif sequence <= 3:
                return '#9b59b6'
            else:
                return '#1abc9c'
