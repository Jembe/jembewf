import flask
import jembewf

def test_extension_initialisation():
    """Ensure JembeWF is loaded into Flask"""
    jwf = jembewf.JembeWF()
    app = flask.Flask(__name__)
    jwf.init_app(app)

    with app.test_request_context():
        assert jwf == jembewf.get_jembewf()
