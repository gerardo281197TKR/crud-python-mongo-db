from flask import jsonify

class UserController:
    def serialize_mongo_document(self, doc):
        #Me falta serializar el array de edades dentro de los usuarios
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
            print(doc)
        return doc

    def list(self, db):
        collection = db["usaurios"]
        usuarios = [self.serialize_mongo_document(doc) for doc in collection.find()]
        return jsonify(usuarios)
