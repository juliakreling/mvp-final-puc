from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from flask_restx import Api, Resource, fields
from flask_sqlalchemy import SQLAlchemy
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql://root:root@localhost:3306/fake_store')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Product(db.Model):
    id_product = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {
            'id_product': self.id_product,
            'title': self.title,
            'price': self.price,
            'category': self.category,
        }

with app.app_context():
    db.create_all()

api = Api(
    app,
    version='1.0',
    title='API Produtos Disponíveis',
    description='API que retorna uma lista de produtos disponíveis',
    doc='/swagger',
    mask=False  
)

product_model = api.model('Product', {
    'id_product': fields.Integer(description='ID do produto', readonly=True),
    'title': fields.String(description='Título do produto'),
    'price': fields.Float(description='Preço do produto'),
    'category': fields.String(description='Categoria do produto'),
})

product_input_model = api.model('ProductInput', {
    'title': fields.String(description='Título do produto'),
    'price': fields.Float(description='Preço do produto'),
    'category': fields.String(description='Categoria do produto'),
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
        """Salva no banco de dados os produtos da API externa"""
        try:
            response = requests.get('https://fakestoreapi.com/products')
            if response.status_code != 200:
                return {'error': 'Falha ao acessar a API externa'}, 500
                
            products = response.json()
            print("Produtos recebidos da API externa: ", products)
            
            for product in products:
                existing_product = Product.query.get(product['id'])
                if not existing_product:
                    new_product = Product(
                        id_product=product['id'],
                        title=product['title'],
                        price=product['price'],
                        category=product['category'],
                    )
                    db.session.add(new_product)
            
            db.session.commit()
            return products
        except requests.exceptions.RequestException as e:
            return {'error': f'Erro ao conectar com a API externa: {str(e)}'}, 500
        except Exception as e:
            return {'error': str(e)}, 500


@ns.route('/list-local-products')
class ListProducts(Resource):
    @ns.doc('list-local-products')
    def get(self):
        """Retorna todos os produtos existentes no banco de dados"""
        try:
            products = Product.query.all()
            return [product.to_dict() for product in products]
        except Exception as e:
            return {'error': str(e)}, 500


@ns.route('/create-product')
class CreateProduct(Resource):
    @ns.doc('create-product')
    @ns.expect(product_input_model)
    def post(self):
        """Cria um novo produto no banco de dados"""
        try:
            data = request.json
            new_product = Product(
                title=data['title'],
                price=data['price'],
                category=data['category'],
            )
            db.session.add(new_product)
            db.session.commit()
            return {'message': f'Produto ID:{new_product.id_product} criado com sucesso'}, 200
        except Exception as e:
            return {'error': str(e)}, 500


@ns.route('/get-product/<int:id>')
class GetProduct(Resource):
    @ns.doc('get-product')
    def get(self, id):
        """Retorna um produto existente no banco de dados"""
        try:
            product = Product.query.get(id)
            if not product:
                return {'error': f'Produto com ID:{id} não encontrado'}, 404
            return product.to_dict()
        except Exception as e:
            return {'error': str(e)}, 500


@ns.route('/update-product/<int:id>')
class UpdateProduct(Resource):
    @ns.doc('update-product')
    @ns.expect(product_input_model)
    def put(self, id):
        """Atualiza um produto existente no banco de dados"""
        try:
            product = Product.query.get(id)
            if not product:
                return {'error': f'Produto com ID:{id} não encontrado'}, 404
                
            data = request.json
            product.title = data.get('title', product.title)
            product.price = data.get('price', product.price)
            product.category = data.get('category', product.category)
            
            db.session.commit()
            return {'message': f'Produto ID:{id} atualizado com sucesso'}, 200
        except Exception as e:
            return {'error': str(e)}, 500


@ns.route('/delete-product/<int:id>')
class DeleteProduct(Resource):
    @ns.doc('delete-product')
    def delete(self, id):
        """Remove um produto existente no banco de dados"""
        try:
            product = Product.query.get(id)
            if not product:
                return {'error': f'Produto com ID:{id} não encontrado'}, 404
                
            db.session.delete(product)
            db.session.commit()
            return {'message': f'Produto ID:{id} deletado com sucesso'}, 200
        except Exception as e:
            return {'error': str(e)}, 500


@ns.route('/delete-all-products')
class DeleteAllProducts(Resource):
    @ns.doc('delete-all-products')
    def delete(self):
        """Remove todos os produtos existentes no banco de dados"""
        try:
            Product.query.delete()
            db.session.commit()
            return {'message': 'Todos os produtos foram deletados com sucesso'}, 200
        except Exception as e:
            return {'error': str(e)}, 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001) 