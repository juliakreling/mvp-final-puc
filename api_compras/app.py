from flask import Flask, request, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_restx import Api, Resource, fields
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

api = Api(
    app,
    version='1.0',
    title='API de Lista de Compras',
    description='API para gerenciar lista de compras',
    doc='/swagger',
    mask=False
)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql://root:root@localhost:3306/shopping_list')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

API_PRINCIPAL_HOST = os.getenv('API_PRINCIPAL_HOST', 'localhost')
API_PRINCIPAL_URL = f'http://{API_PRINCIPAL_HOST}:5001/api'

db = SQLAlchemy(app)

class ShoppingItem(db.Model):
    id_product = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {
            'id_product': self.id_product,
            'title': self.title,
            'price': self.price,
            'category': self.category,
            'quantity': self.quantity
        }

with app.app_context():
    db.create_all()

shopping_item_model = api.model('ShoppingItem', {
    'id_product': fields.Integer(description='ID do produto'),
    'title': fields.String(description='Título do produto'),
    'price': fields.Float(description='Preço do produto'),
    'category': fields.String(description='Categoria do produto'),
    'quantity': fields.Integer(description='Quantidade do item')
})

ns = api.namespace('api', description='Operações da API')


@ns.route('/')
class Index(Resource):
    def get(self):
        """Redireciona para a página de documentação Swagger"""
        return redirect('/swagger')


@ns.route('/list-products-store')
class Products(Resource):
    @ns.doc('list-products-store')
    def get(self):
        """Retorna todos os produtos disponíveis no banco de dados"""
        try:
            response = requests.get(f'{API_PRINCIPAL_URL}/list-local-products')
            if response.status_code == 200:
                return response.json()
            return {'error': 'Erro ao buscar produtos'}, response.status_code
        except Exception as e:
            return {'error': str(e)}, 500


@ns.route('/product-detail/<int:id>')
class ProductDetail(Resource):
    @ns.doc('product-detail')
    def get(self, id):
        """Retorna um produto existente na lista de compras pelo ID"""
        try:
            item = ShoppingItem.query.get(id)
            if not item:
                return {'error': 'Produto ID:' + str(id) + ' não encontrado na lista de compras'}, 404
            return item.to_dict()
        except Exception as e:
            return {'error': str(e)}, 500


@ns.route('/list-products-shopping-list')
class ShoppingListItems(Resource):
    @ns.doc('list-products-shopping-list')
    def get(self):
        """Retorna todos os itens existentes na lista de compras"""
        try:
            items = ShoppingItem.query.all()
            return [item.to_dict() for item in items]
        except Exception as e:
            return {'error': str(e)}, 500


@ns.route('/add-product-shopping-list')
class ShoppingList(Resource):
    @ns.doc('add-product-shopping-list')
    @ns.expect(api.model('ShoppingItemInput', {
        'id_product': fields.Integer(required=True, description='ID do produto'),
        'quantity': fields.Integer(required=False, description='Quantidade do item', default=1)
    }))
    def post(self):
        """Adiciona um item à lista de compras"""
        try:
            data = request.json
            id_product = data['id_product']
            quantity = data.get('quantity', 1)

            response = requests.get(f'{API_PRINCIPAL_URL}/get-product/{id_product}')
            if response.status_code != 200:
                return {'error': 'Produto não encontrado'}, 404

            product = response.json()
            
            existing_item = ShoppingItem.query.filter_by(id_product=id_product).first()
            if existing_item:
                existing_item.quantity += quantity
                db.session.commit()
                return existing_item.to_dict(), 200

            new_item = ShoppingItem(
                id_product=id_product,
                title=product['title'],
                price=product['price'],
                quantity=quantity,
                category=product['category']
            )
            db.session.add(new_item)
            db.session.commit()
            return new_item.to_dict(), 200
        except Exception as e:
            return {'error': str(e)}, 500


@ns.route('/delete-product-shopping-list/<int:id_product>')
class ShoppingItemResource(Resource):
    @ns.doc('delete-product-shopping-list')
    def delete(self, id_product):
        """Remove um item existente da lista de compras"""
        try:
            item = ShoppingItem.query.get(id_product)
            if not item:
                return {'error': 'Produto ID:' + str(id_product) + ' não encontrado na lista de compras'}, 404
            db.session.delete(item)
            db.session.commit()
            return {'message': 'Item ID:' + str(id_product) + ' removido com sucesso'}
        except Exception as e:
            return {'error': str(e)}, 500


@ns.route('/total-value-shopping-list')
class TotalValue(Resource):
    @ns.doc('total-value-shopping-list')
    def get(self):
        """Calcula o valor total da lista de compras"""
        try:
            items = ShoppingItem.query.all()
            total_value = sum(item.price * item.quantity for item in items)
            return {'valor total da lista de compras': total_value}
        except Exception as e:
            return {'error': str(e)}, 500


@ns.route('/clear-shopping-list')
class ClearShoppingList(Resource):
    @ns.doc('clear-shopping-list')
    def delete(self):
        """Remove todos os itens existentes na lista de compras"""
        try:
            ShoppingItem.query.delete()
            db.session.commit()
            return {'message': 'Lista de compras limpa com sucesso'}
        except Exception as e:
            return {'error': str(e)}, 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002) 