from flask import Blueprint, jsonify


api = Blueprint("api_v1", __name__, template_folder="templates")
METHODS = ["GET", "POST", "PUT", "DELETE"]

@api.route("/", defaults={"path": ""}, methods=METHODS)
@api.route("/<path:path>", methods=METHODS)
def deprecated_warning(path):
    """Catch all routes and return a deprecated warning message."""
    message = "Warning: This API version is deprecated. Please use /api/v3/ instead."
    return jsonify({"message": message}), 400
