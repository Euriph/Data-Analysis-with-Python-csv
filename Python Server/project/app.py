from flask import Flask
from flask_cors import CORS
from models import Base, engine
from routes.data_routes import data_bp

app = Flask(__name__)
CORS(app)

# Initialize the database
Base.metadata.create_all(engine)

# Register blueprints
app.register_blueprint(data_bp)

if __name__ == '__main__':
    app.run(debug=True)
