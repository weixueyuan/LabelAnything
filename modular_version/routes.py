"""
路由配置：定义任务映射

目前只有一个任务，以后可以添加更多
"""

ROUTES = [
    {
        "url": "/annotation",
        "task": "annotation",
        "port": 7800,
        "description": "物体属性标注"
    },
    # 以后添加新任务：
    # {
    #     "url": "/review",
    #     "task": "review",
    #     "port": 7801,
    #     "description": "质量审核"
    # },
]

DEFAULT_PORT = 7800

