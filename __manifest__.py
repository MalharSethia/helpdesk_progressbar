{
    'name': 'project_progress_bar',
    'version': '17.0.1.0.0',
    'category': 'Project',
    'summary': 'Visual progress bar for project kanban view showing task completion status',
    'description': """
        This module adds a visual progress bar to the project kanban view that shows:
        - Task completion status by stage
        - Color-coded segments matching task stage colors
        - Real-time updates when tasks change status
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['project'],
    'data': [
        'views/project_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'project_progress_bar/static/src/css/project_progress_bar.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
