from config import create_app
import routes  # Ensure this import remains here to register routes

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
