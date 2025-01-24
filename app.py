from flask import Flask, render_template,jsonify, request
from flask_socketio import SocketIO, emit
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_secreto_aqui'
socketio = SocketIO(app, cors_allowed_origins="*")  # Habilitar CORS si es necesario


# Conexión al servidor MongoDB
client = MongoClient("mongodb://localhost:27017/") 

# Seleccionar una base de datos
db = client["labuena"]

# Seleccionar una colección
collection = db["usaurios"]

print("Conexión exitosa a MongoDB!")

# Convertir ObjectId a string
def serialize_mongo_document(doc):
    doc['_id'] = str(doc['_id'])  # Convertir ObjectId a string
    return doc

# Ruta básica para servir la página web
@app.route('/')
def index():
    # Seleccionar la tabla que se va a usar 
    collection = db["usaurios"]
    # Obtener y serializar documentos
    usuarios = [serialize_mongo_document(doc) for doc in collection.find()]
    return jsonify(usuarios)  # Devolver la lista como JSON

@app.route('/create', methods=['POST'])
def create_document():
    collection = db["usaurios"]
    try:
        # Obtenemos los datos del cuerpo de la solicitud
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se enviaron datos'}), 400

        existing_document = collection.find_one({'nombre': data.get('nombre')})
        if existing_document:
            return jsonify({'error': 'El registro ya existe'}), 409

        #Convertir cualquier campo que deba ser ObjectId
        if 'edad' in data and isinstance(data['edad'], list):
            try:
                data['edad'] = [ObjectId(oid) for oid in data['edad']]
            except Exception:
                return jsonify({'error': 'Uno o más IDs en el campo "edad" no son válidos'}), 400
                
        # Insertamos el documento en la colección
        result = collection.insert_one(data)
        
        return jsonify({
            'message': 'Documento creado con éxito',
            'id': str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update/<id>', methods=['PUT'])
def update_document(id):
    collection = db["usaurios"]
    try:
        # Validar si el ID proporcionado es válido
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'ID inválido'}), 400

        # Obtenemos los datos del cuerpo de la solicitud
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se enviaron datos para actualizar'}), 400

        # Convertimos el ID a ObjectId
        object_id = ObjectId(id)

        #Convertir cualquier campo que deba ser ObjectId
        if 'edad' in data and isinstance(data['edad'], list):
            try:
                data['edad'] = [ObjectId(oid) for oid in data['edad']]
            except Exception:
                return jsonify({'error': 'Uno o más IDs en el campo "edad" no son válidos'}), 400

        # Realizamos la actualización
        result = collection.update_one({'_id': object_id}, {'$set': data})

        # Verificamos si se actualizó algún documento
        if result.matched_count == 0:
            return jsonify({'error': 'Documento no encontrado'}), 404

        return jsonify({
            'message': 'Documento actualizado con éxito',
            'modified_count': result.modified_count
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete/<id>', methods=['DELETE'])
def delete_document(id):
    try:
        # Validar si el ID proporcionado es válido
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'ID inválido'}), 400

        # Convertimos el ID a ObjectId
        object_id = ObjectId(id)

        # Realizamos la eliminación
        result = collection.delete_one({'_id': object_id})

        # Verificamos si se eliminó algún documento
        if result.deleted_count == 0:
            return jsonify({'error': 'Documento no encontrado'}), 404

        return jsonify({'message': 'Documento eliminado con éxito'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Manejar conexión de cliente
@socketio.on('connect')
def handle_connect():
    print("Cliente conectado")
    emit('server_message', {'message': 'Bienvenido al servidor!'})

# Manejar mensajes del cliente
@socketio.on('client_message')
def handle_message(data):
    print(f"Mensaje del cliente: {data}")
    emit('server_message', {'message': f"Recibí tu mensaje: {data['message']}"}, broadcast=True)

# Manejar desconexión
@socketio.on('disconnect')
def handle_disconnect():
    print("Cliente desconectado")

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000)
 