import os
import csv
import json
from flask import Flask, request, jsonify, render_template
from shapely.geometry import Polygon, Point
from datetime import datetime

app = Flask(__name__)

# Diretório para armazenar os arquivos de minas
os.makedirs('mines', exist_ok=True)

# Carregar os polígonos de um arquivo CSV
poligonos = []
with open('poligonos.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        poligonos.append({
            "nome": row["nome"],
            "coordenadas": eval(row["coordenadas"]),
            "cor": row["cor"]
        })

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/map', methods=['GET'])
def map_page():
    return render_template('map.html')

@app.route('/create-mine-page', methods=['GET'])
def create_mine_page():
    return render_template('create-mine.html')

@app.route('/criador-de-poligono', methods=['GET'])
def criador_de_poligono():
    return render_template('criador-de-poligono.html')

@app.route('/get-poligonos', methods=['GET'])
def get_poligonos():
    return jsonify(poligonos)

@app.route('/verificar-ponto', methods=['POST'])
def verificar_ponto():
    data = request.get_json()
    ponto_teste = data.get('ponto_teste')
    ponto_id = data.get('ID')

    if not ponto_teste or not ponto_id:
        return jsonify({"error": "ID e ponto_teste são obrigatórios."}), 400

    ponto = Point(ponto_teste)

    for poligono in poligonos:
        poligono_obj = Polygon(poligono["coordenadas"])
        if poligono_obj.contains(ponto):
            return jsonify({
                "ID": ponto_id,
                "ponto_teste": ponto_teste,
                "status": "IN",
                "poligono": poligono["nome"]
            })

    return jsonify({
        "ID": ponto_id,
        "ponto_teste": ponto_teste,
        "status": "OUT",
        "poligono": None
    })

@app.route('/create-mine', methods=['POST'])
def create_mine():
    data = request.get_json()
    ponto_teste = data.get('ponto_teste')
    ponto_id = data.get('ID')

    if not ponto_teste or not ponto_id:
        return jsonify({"error": "ID e ponto_teste são obrigatórios."}), 400

    ponto = Point(ponto_teste)

    for poligono in poligonos:
        poligono_obj = Polygon(poligono["coordenadas"])
        if poligono_obj.contains(ponto):
            # Nome do arquivo com prefixo 'mine_'
            mines_dir = "mines"
            os.makedirs(mines_dir, exist_ok=True)  # Cria o diretório se não existir
            file_path = os.path.join(mines_dir, f"mine_{ponto_id}.csv")

            # Dados a serem salvos
            row = {
                "nome": poligono["nome"],
                "coordenadas": str(ponto_teste),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # Criar ou adicionar ao arquivo CSV
            file_exists = os.path.isfile(file_path)
            with open(file_path, 'a', newline='') as csvfile:
                fieldnames = ["nome", "coordenadas", "timestamp"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()  # Escreve cabeçalho se o arquivo não existir
                writer.writerow(row)

            return jsonify({
                "message": "Ponto registrado na mina.",
                "file": file_path,
                "data": row
            }), 201

    return jsonify({
        "message": "Ponto fora de qualquer polígono.",
        "status": "OUT"
    }), 200


@app.route('/list-mines-by-id', methods=['POST'])
def list_mines_by_id():
    data = request.get_json()
    mine_id = data.get('ID')

    if not mine_id:
        return jsonify({"error": "ID is required."}), 400

    # Caminho do diretório de mines
    mines_dir = "mines"
    file_name = f"mine_{mine_id}.csv"  # Adiciona o prefixo "mine_" ao ID
    file_path = os.path.join(mines_dir, file_name)

    # Log para depuração: Conteúdo da pasta mines
    try:
        files = os.listdir(mines_dir)
        print(f"Contents of '/mines': {files}")
    except FileNotFoundError:
        print("The '/mines' directory does not exist.")
        return jsonify({"error": "Mines directory not found."}), 500

    # Inicializa a lista para armazenar as minas
    mines = []

    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Validação para garantir que as colunas necessárias estejam presentes
                try:
                    nome = row["nome"]
                    coordenadas = eval(row["coordenadas"])  # Conversão segura para lista
                    timestamp = row["timestamp"]
                    mines.append({
                        "nome": nome,
                        "coordenadas": coordenadas,
                        "timestamp": timestamp
                    })
                except KeyError as e:
                    print(f"Error reading file {file_name}: Missing column {e}")
                    return jsonify({"error": f"Invalid CSV format in {file_name}."}), 500

    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return jsonify({"mines": []}), 200  # Retorna uma lista vazia se o arquivo não for encontrado
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return jsonify({"error": f"Error reading file {file_name}."}), 500

    # Retorna as minas encontradas no arquivo CSV
    return jsonify({"mines": mines}), 200


if __name__ == '__main__':
    app.run(debug=True)
