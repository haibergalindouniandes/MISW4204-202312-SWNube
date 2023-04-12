from base import request, Resource, api, app, Task, jwt_required, tasks_schema, task_schema

# Clase que contiene la logica para consultar las tareas registradas
class TaskListResource(Resource):
    @jwt_required()
    def get(self):
        queryParams = request.args
        tasks = tasks_schema.dump(Task.query.all())
        try:
            if int(queryParams['order']) == 1:
                tasks = sorted(tasks, key=lambda d: d["id"], reverse=True)
            else:
                tasks = sorted(tasks, key=lambda d: d["id"], reverse=False)
            
            if 'max' in queryParams:
                tasks = tasks[: int(queryParams["max"])]
            
            return tasks                    
        except Exception as e:
            return {"msg": str(e)}, 500


class TaskIdResource(Resource):
    @jwt_required()
    def get(self, id_task):
        return task_schema.dump(Task.query.get_or_404(id_task))

# Agregamos los recursos
api.add_resource(TaskListResource, "/api/tasks")
api.add_resource(TaskIdResource, "/api/tasks/<int:id_task>")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
