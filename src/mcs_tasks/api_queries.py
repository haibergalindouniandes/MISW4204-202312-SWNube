from base import request, Resource, db, api, app, Task, jwt_required, task_schema


class TaskListResource(Resource):
    @jwt_required()
    def get(self):
        task = task_schema.dump(Task.query.all())
        try:
            if request.json["order"] == 1:
                result_temp = sorted(task, key=lambda d: d["id"], reverse=True)
            else:
                result_temp = sorted(task, key=lambda d: d["id"], reverse=False)
        except KeyError:
            result_temp = sorted(task, key=lambda d: d["id"], reverse=False)

        try:
            result = result_temp[: request.json["max"]]
        except KeyError:
            result = result_temp
        return result


api.add_resource(TaskListResource, "/api/tasks")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
