from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
import os

app = Flask(__name__)

app.config["MONGO_URI"] = "mongodb+srv://restapi:3pPoqTkaaxumwa62@cluster0.a93lz.mongodb.net/your_database?retryWrites=true&w=majority"
mongo = PyMongo(app)

app.config["JWT_SECRET_KEY"] = "secretkey"
jwt = JWTManager(app)

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if mongo.db.users.find_one({"email": data["email"]}):
        return jsonify({"message": "User already exists"}), 400
    hashed_password = generate_password_hash(data["password"])
    mongo.db.users.insert_one({
        "first_name": data["first_name"],
        "last_name": data["last_name"],
        "email": data["email"],
        "password": hashed_password
    })
    return jsonify({"message": "User registered successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = mongo.db.users.find_one({"email": data["email"]})
    if user and check_password_hash(user["password"], data["password"]):
        access_token = create_access_token(identity=str(user["_id"]))
        return jsonify({"access_token": access_token}), 200
    return jsonify({"message": "Invalid credentials"}), 401

@app.route("/template", methods=["POST"])
@jwt_required()
def add_template():
    user_id = get_jwt_identity()
    data = request.get_json()
    template_id = mongo.db.templates.insert_one({"user_id": user_id, **data}).inserted_id
    return jsonify({"message": "Template added", "template_id": str(template_id)}), 201

@app.route("/template", methods=["GET"])
@jwt_required()
def get_templates():
    user_id = get_jwt_identity()
    templates = list(mongo.db.templates.find({"user_id": user_id}, {"user_id": 0}))
    for template in templates:
        template["_id"] = str(template["_id"])
    return jsonify(templates), 200

@app.route("/template/<template_id>", methods=["GET"])
@jwt_required()
def get_template(template_id):
    user_id = get_jwt_identity()
    template = mongo.db.templates.find_one({"_id": ObjectId(template_id), "user_id": user_id}, {"user_id": 0})
    if not template:
        return jsonify({"message": "Template not found"}), 404
    template["_id"] = str(template["_id"])
    return jsonify(template), 200

@app.route("/template/<template_id>", methods=["PUT"])
@jwt_required()
def update_template(template_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    result = mongo.db.templates.update_one({"_id": ObjectId(template_id), "user_id": user_id}, {"$set": data})
    if result.matched_count == 0:
        return jsonify({"message": "Template not found or unauthorized"}), 404
    return jsonify({"message": "Template updated successfully"}), 200

@app.route("/template/<template_id>", methods=["DELETE"])
@jwt_required()
def delete_template(template_id):
    user_id = get_jwt_identity()
    result = mongo.db.templates.delete_one({"_id": ObjectId(template_id), "user_id": user_id})
    if result.deleted_count == 0:
        return jsonify({"message": "Template not found or unauthorized"}), 404
    return jsonify({"message": "Template deleted successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True)
