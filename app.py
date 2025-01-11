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

    # Verifica o ponto usando a função verificar_ponto()
    ponto_data = verificar_ponto().get_json()

    if ponto_data["status"] == "OUT":
        return jsonify({"message": "Ponto fora de todos os polígonos."})

    # Dados do ponto dentro de um polígono
    nome_poligono = ponto_data["poligono"]
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Caminho do arquivo na pasta mines
    mine_file = os.path.join('mines', f"{ponto_id}.csv")

    # Escreve ou adiciona no arquivo CSV
    file_exists = os.path.isfile(mine_file)
    with open(mine_file, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            # Escreve o cabeçalho do CSV
            writer.writerow(["nome", "coordenadas", "timestamp"])
        writer.writerow([nome_poligono, ponto_teste, timestamp])

    return jsonify({
        "message": "Ponto registrado na mina.",
        "file": mine_file,
        "data": {
            "nome": nome_poligono,
            "coordenadas": ponto_teste,
            "timestamp": timestamp
        }
    })


@app.route('/list-mines-by-id', methods=['POST'])
def list_mines_by_id():
    data = request.get_json()
    mine_id = data.get('ID')

    if not mine_id:
        return jsonify({"error": "ID is required."}), 400

    # Log the content of the /mines directory
    mines_dir = "mines"
    try:
        files = os.listdir(mines_dir)
        print(f"Contents of '/mines': {files}")
    except FileNotFoundError:
        print("The '/mines' directory does not exist.")
        return jsonify({"error": "Mines directory not found."}), 500

    file_path = f"{mines_dir}/mines_{mine_id}.csv"
    mines = []

    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                mines.append({
                    "nome": row["nome"],
                    "coordenadas": eval(row["coordenadas"]),
                    "timestamp": row["timestamp"]
                })
    except FileNotFoundError:
        return jsonify({"mines": []}), 200

    return jsonify({"mines": mines}), 200


if __name__ == '__main__':
    app.run(debug=True)
