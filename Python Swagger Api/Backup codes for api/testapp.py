from flask import Flask, request
from flask_restx import Api, Resource, fields

app = Flask(__name__)
api = Api(app, version='1.0', title='Sample API',
          description='A simple example API')

# Namespace definition
ns = api.namespace('myapi', description='My operations')

# Model definition for the input data for POST requests
todo = api.model('Todo', {
    'task': fields.String(required=True, description='The task details')
})

# In-memory storage
todos = {}


@ns.route('/todo')
class TodoList(Resource):
    """Shows a list of all todos, and lets you POST to add new tasks"""

    @ns.doc('list_todos')
    @ns.marshal_list_with(todo)
    def get(self):
        """List all tasks"""
        return [todos[key] for key in sorted(todos.keys())]

    @ns.doc('create_todo')
    @ns.expect(todo)
    @ns.marshal_with(todo, code=201)
    def post(self):
        """Create a new task"""
        idx = len(todos) + 1
        todos[idx] = {'task': request.json['task']}
        return todos[idx], 201


if __name__ == '__main__':
    app.run(debug=True)
