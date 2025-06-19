from flask import Flask
from flask_session import Session
from flask_migrate import Migrate
from configs import config
import redis

from extensions.ext_db import db
from controllers.auth.auth import auth_bp


session = Session()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    app.config.from_mapping(config.model_dump())

    db.init_app(app)

    app.config["SESSION_TYPE"] = "redis"
    app.config["SESSION_REDIS"] = redis.from_url(app.config["REDIS_URL"])
    session.init_app(app)

    migrate.init_app(app, db)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    return app

app = create_app()


@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(debug=True)