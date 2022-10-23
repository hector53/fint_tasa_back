from getpass import getuser
from flask import request, jsonify, abort, make_response, session, redirect
from app import app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta
from app.modules import register_user, getDataOne, updateData, getData, insert_data
from passlib.hash import pbkdf2_sha256
from datetime import datetime
from app.apis_exchanges.ftx.ftx import FtxClient
apiFtx = FtxClient("WAnh9bQ6PIb4MeugrhUZev9aaq0yZupStUVpY4Dq", "4ZY2Lpzsl2ulEmzqpGzjuvsbAaCszDSqhEM-d2tz")#nacho

@app.route('/api/', methods=["GET"])
def inicio_ruta():
    return jsonify("response")

@app.route('/api/register', methods=["POST"])
def registrar_user():
    body = request.get_json()
    print(body)
    username = body["username"]
    email = body["email"]
    password = body["password"]
    if username and email and password:
        passwordEncrypt = pbkdf2_sha256.hash(password)
        #busco el username q no exista 
        sql = f"""
        select * from fi_users where username = %s or email = %s
        """
        tupla = (username, email)
        getUsername = getDataOne(sql, tupla)
        if getUsername: 
            #si existe enviar error 
            abort(make_response(jsonify(message="username o email ya existe, intente con otro"), 400))
        else:
            sql = f"""
                    INSERT INTO fi_users ( username, email, pass, created, updated) 
                    VALUES
                    ( %s, %s, %s, %s,  %s)
                    """
            tupla = (username, email, passwordEncrypt,  datetime.now(), datetime.now())
            id_user = register_user(sql, tupla)
            if id_user["status"] == 0:
                abort(make_response(jsonify(message=id_user["error"]), 400))
            else:
                access_token = create_access_token(identity=id_user["id"])
                response = {
                    "name": username,
                    "email": email,
                    "token": access_token
                }
    else:
        abort(make_response(jsonify(message="faltan datos"), 400))
    return jsonify(response)

@app.route('/api/login', methods=['POST'])
def login():
    body = request.get_json()
    print(body)
    email = body["email"]
    password = body["password"]
    if email and password:
        sql = f"SELECT * FROM fi_users where email =  %s  "
        tupla = (email)
        getUser = getDataOne(sql, tupla)
        if getUser:
            passUserDb = getUser[3]
            verifyPass = pbkdf2_sha256.verify(password, passUserDb)
            if verifyPass:
                # el pass es correcto
                access_token = create_access_token(identity=getUser[0])
                response = {
                "name": getUser[1],
                "email": getUser[2],
                "token": access_token, 
                }
                return jsonify(response)
            else:
                abort(make_response(jsonify(message="password incorrect"), 401))
        else:
            abort(make_response(jsonify(message="username  not exist"), 401))
    else:
        abort(make_response(jsonify(message="faltan datos"), 400))

@app.route('/api/validateToken', methods=['POST'])
@jwt_required()
def validateToken():
    return jsonify({
            "status": 1
        })

@app.route('/api/add_api_derivative', methods=['POST'])
@jwt_required()
def add_api_derivative():
    current_user_id = get_jwt_identity()
    body = request.get_json()
    print(body)
    name = body["name"]
    app_key = body["app_key"]
    app_secret = body["app_secret"]
    derivative = body["derivative"]
    if name and app_key and app_secret:
        sql = f"""
        INSERT INTO fi_api_credentials ( id_derivative, name, id_user, api_key, api_secret, created, updated) 
        VALUES
        ( %s, %s, %s, %s, %s, %s, %s)
        """
        tupla = (derivative, name, current_user_id, app_key, app_secret,  datetime.now(), datetime.now() ) 
        id_api = updateData(sql, tupla)
        return jsonify({
            "status": 1, 
            "id_api": id_api
        })
    else:
        abort(make_response(jsonify(message="faltan datos"), 400))

@app.route('/api/edit_api_derivative', methods=['PUT'])
@jwt_required()
def edit_api_derivative():
    id_api = request.args.get('id', '')
    current_user_id = get_jwt_identity()
    body = request.get_json()
    print(body)
    name = body["name"]
    app_key = body["app_key"]
    app_secret = body["app_secret"]
    derivative = body["derivative"]
    if name and app_key and app_secret:
        sql = f"""
        UPDATE fi_api_credentials set name = %s, api_key = %s, api_secret = %s, updated =%s
        where id = %s and id_user = %s
        """
        tupla = ( name, app_key, app_secret,  datetime.now(), id_api, current_user_id ) 
        editApi = updateData(sql, tupla)
        return jsonify({
            "status": 1, 
            "id_api": id_api
        })
    else:
        abort(make_response(jsonify(message="faltan datos"), 400))
@app.route('/api/delete_api_derivative', methods=['DELETE'])
@jwt_required()
def delete_api_derivative():
    id_api = request.args.get('id', '')
    current_user_id = get_jwt_identity()
    if id_api:
        sql = f"""
        DELETE FROM fi_api_credentials where id = %s and id_user = %s
        """
        tupla = ( id_api, current_user_id ) 
        deleteApi = updateData(sql, tupla)
        return jsonify({
            "status": 1, 
        })
    else:
        abort(make_response(jsonify(message="faltan datos"), 400))
        
def convert_text_api_key(text):
    texto = str(text)
    totalText = len(texto)
    letrasOcultas = totalText-3
    asteriscos = ""
    for i in range(letrasOcultas):
        asteriscos = asteriscos + "*"
    lastLetters = f"{asteriscos}{texto[letrasOcultas:totalText]}"
    return lastLetters


@app.route('/api/get_api_credentials', methods=['GET'])
@jwt_required()
def get_api_credentials():
    current_user_id = get_jwt_identity()
    derivative = request.args.get('derivative', '')
    sql = f"""
    select * from fi_api_credentials where id_derivative = %s and id_user = %s
    """
    tupla = (derivative, current_user_id)
    getCredentialsRows = getData(sql, tupla)
    arrayApis = []
    if getCredentialsRows:
        for x in getCredentialsRows:
            api_key = convert_text_api_key(x[4])
            app_secret = convert_text_api_key(x[5])
            arrayApis.append({
                "id": x[0], 
                "name": x[3], 
                "app_key": api_key,
                "app_secret": app_secret
            })
    print("derivative", derivative)
    return jsonify({
            "status": 1, 
            "arrayApis": arrayApis
        })



@app.route('/api/fs_estrategies', methods=['GET'])
@jwt_required()
def fs_estrategies():
    meses=['Jan',
    'Feb',
    'Mar',
    'Apr',
    'May',
    'Jun',
    'Jul',
    'Aug',
    'Sep',
    'Oct',
    'Nov',
    'Dec']
    current_user_id = get_jwt_identity()
    derivative = request.args.get('derivative', '')
    currency = request.args.get('currency', '')
    arrayCurrency = []
    try:
        data = apiFtx.get_single_market(f"{currency}/USD")
        print("data", data)
        arrayCurrency.append({
        "name": data["name"], 
        "mark": data["price"],
        "bid": data["bid"],
        "ask": data["ask"],   
        "expiry": ""
        })
    except Exception as e:
        abort(make_response(jsonify(message=e), 400))
    try:
        data = apiFtx.get_all_futures()
        for i in range(len(data)):
            if currency in data[i]["name"] and data[i]["underlying"]==currency and (data[i]["type"]=='perpetual' or data[i]["type"]=='future'  ):
                print("asdasdasdasddsa", data[i]["expiry"])
                dateExpiry = ""
                if data[i]["expiry"]!=None:
                    dateExpiry = str(data[i]["expiry"])
                    dateExpiry = datetime.strptime(dateExpiry[0:10], '%Y-%m-%d')
                    dateExpiry = f"{dateExpiry.day} {meses[dateExpiry.month-1]} {dateExpiry.year}"
                arrayCurrency.append({
                "name": data[i]["name"], 
                "mark": data[i]["mark"],
                "bid": data[i]["bid"],
                "ask": data[i]["ask"],  
                "expiry": dateExpiry
                })
    except Exception as e:
        abort(make_response(jsonify(message="e"), 400))
    arraySidebar = arrayCurrency[0:len(arrayCurrency)-1]
    arrayHeader = arrayCurrency[1:len(arrayCurrency)]
    gridColumns = f"[header]128px"
    gridRows = f"[header]50px"
    gridCells = []

    for i in range(len(arraySidebar)):
        nameUsd = str(arraySidebar[i]['name']).replace('/','-')
        gridColumns = gridColumns + f"[{arrayHeader[i]['name']}]250px"
        gridRows = gridRows + f"[{nameUsd}]107px"
        init = 0
        if i>0:
            init = init+i
        expirySidebar = arraySidebar[i]['expiry']
        if expirySidebar == "":
            if "PERP" in arraySidebar[i]['name']: 
                expirySidebar = "PERP"
        
        
        for e in range(init, len(arrayHeader)):
            expiryHeader = arrayHeader[i]['expiry']
            if expiryHeader == "":
                if "PERP" in arrayHeader[i]['name']: 
                    expiryHeader = "PERP"
          
            bidCell = arraySidebar[i]["ask"] / arrayHeader[e]["bid"]
            askCell = arraySidebar[i]["bid"] / arrayHeader[e]["ask"]
            
            gridCells.append({
            "rowNameOriginal": arraySidebar[i]['name'],
            "colNameOriginal": arrayHeader[e]["name"],
            "dataRow": nameUsd, 
            "dataCol": arrayHeader[e]["name"], 
            "title": f"{arraySidebar[i]['name']} - {arrayHeader[e]['name']}", 
            "rowBid": arraySidebar[i]["bid"], 
            "rowAsk": arraySidebar[i]["ask"],
            "colBid": arrayHeader[e]["bid"], 
            "colAsk": arrayHeader[e]["ask"], 
            "rowAskSize": 0,
            "rowBidSize": 0,
            "colAskSize":0,
            "colBidSize": 0,
            "bid": round(bidCell,5), 
            "ask": round(askCell,5), 
            "markSidebar": arraySidebar[i]['mark'],
            "markHeader": arrayHeader[e]['mark'], 
            "expirySidebar": expirySidebar,
            "expiryHeader": expiryHeader, 
            })

    return jsonify({
        "arrayCurrency": arrayCurrency,
            "arraySidebar": arraySidebar, 
            "arrayHeader": arrayHeader, 
            "gridColumns": gridColumns, 
            "gridRows": gridRows, 
            "gridCells": gridCells
        })

def crear_tasa(type_tasa, currency,  typeLimitMarket, future, typeO, size, price, future2 ): 
    #type_tasa: 1=spot/future, 2= future/future
    #typeO = "buy or sell"
    #size = size of currency
    #price = price of currency only in limit 2
    if type_tasa == 1: 
        #tasa spot / algun futuro 
        if typeLimitMarket == 1: #limit 1 #comprar spot en market 
            try:    
                comprarSpot = apiFtx.place_order(f"{currency}/USD", "buy", 0, size, "market")
            except Exception as e:
                return {"status": "error", "msg": e}
            try:    
                operarFuture = apiFtx.place_order(f"{currency}-{future}", typeO, price, size, "limit")
            except Exception as e:
                return {"status": "error", "msg": e}
            
        if typeLimitMarket == 2: #limit 2 #operar directamente en future
            try:    
                operarFuture = apiFtx.place_order(f"{currency}-{future}", typeO, price, size, "limit")
            except Exception as e:
                return {"status": "error", "msg": e}
            
        if typeLimitMarket == 3: #market
            try:    
                comprarSpot = apiFtx.place_order(f"{currency}/USD", "buy", 0, size, "market")
            except Exception as e:
                return {"status": "error", "msg": e}
            try:    
                operarFuture = apiFtx.place_order(f"{currency}-{future}", typeO, 0, size, "market")
            except Exception as e:
                return {"status": "error", "msg": e}
            
    if type_tasa == 2: 
        #tasa futuro / futuro 
        if typeLimitMarket == 1: #limit 1 #comprar spot en market 
            try:    
                comprarSpot = apiFtx.place_order(f"{currency}/USD", "buy", 0, size, "market")
            except Exception as e:
                return {"status": "error", "msg": e}
            if typeO == "sell": 
                #hago un buy en future y un sell en future2
                try:    
                    operarFuture = apiFtx.place_order(f"{currency}-{future}", "buy", price, size, "limit")
                except Exception as e:
                    return {"status": "error", "msg": e}
                try:    
                    operarFuture2 = apiFtx.place_order(f"{currency}-{future2}", "sell", price, size, "limit")
                except Exception as e:
                    return {"status": "error", "msg": e}
            if typeO == "buy": 
                #hago un buy en future y un sell en future2
                try:    
                    operarFuture = apiFtx.place_order(f"{currency}-{future}", "sell", price, size, "limit")
                except Exception as e:
                    return {"status": "error", "msg": e}
                try:    
                    operarFuture2 = apiFtx.place_order(f"{currency}-{future2}", "buy", price, size, "limit")
                except Exception as e:
                    return {"status": "error", "msg": e}
  
        if typeLimitMarket == 2: #limit 2
            if typeO == "sell": 
                #hago un buy en future y un sell en future2
                try:    
                    operarFuture = apiFtx.place_order(f"{currency}-{future}", "buy", price, size, "limit")
                except Exception as e:
                    return {"status": "error", "msg": e}
                try:    
                    operarFuture2 = apiFtx.place_order(f"{currency}-{future2}", "sell", price, size, "limit")
                except Exception as e:
                    return {"status": "error", "msg": e}
            if typeO == "buy": 
                #hago un buy en future y un sell en future2
                try:    
                    operarFuture = apiFtx.place_order(f"{currency}-{future}", "sell", price, size, "limit")
                except Exception as e:
                    return {"status": "error", "msg": e}
                try:    
                    operarFuture2 = apiFtx.place_order(f"{currency}-{future2}", "buy", price, size, "limit")
                except Exception as e:
                    return {"status": "error", "msg": e}
        if typeLimitMarket == 3: # market 
            try:    
                comprarSpot = apiFtx.place_order(f"{currency}/USD", "buy", 0, size, "market")
            except Exception as e:
                return {"status": "error", "msg": e}
            if typeO == "sell": 
                #hago un buy en future y un sell en future2
                try:    
                    operarFuture = apiFtx.place_order(f"{currency}-{future}", "buy", 0, size, "market")
                except Exception as e:
                    return {"status": "error", "msg": e}
                try:    
                    operarFuture2 = apiFtx.place_order(f"{currency}-{future2}", "sell", 0, size, "market")
                except Exception as e:
                    return {"status": "error", "msg": e}
            if typeO == "buy": 
                #hago un buy en future y un sell en future2
                try:    
                    operarFuture = apiFtx.place_order(f"{currency}-{future}", "sell", 0, size, "market")
                except Exception as e:
                    return {"status": "error", "msg": e}
                try:    
                    operarFuture2 = apiFtx.place_order(f"{currency}-{future2}", "buy", 0, size, "market")
                except Exception as e:
                    return {"status": "error", "msg": e}
    return {"status": "ok", "msg": "ordenes ejecutadas correctamente"}
        
        
def cerrar_tasa(type_tasa, currency,  typeLimitMarket, future, typeO, size, price, future2 ): 
    #type_tasa: 1=spot/future, 2= future/future
    #typeO = "buy or sell"
    #size = size of currency
    #price = price of currency only in limit 2
    if type_tasa == 1: 
        #tasa spot / algun futuro 
        if typeLimitMarket == 1: #limit 1 #comprar spot en market 
            try:    
                operarFuture = apiFtx.place_order(f"{currency}-{future}", typeO, 0, size, "market")
            except Exception as e:
                return {"status": "error", "msg": e}
            try:    
                venderSpot = apiFtx.place_order(f"{currency}/USD", "sell", 0, size, "market")
            except Exception as e:
                return {"status": "error", "msg": e}
            
        if typeLimitMarket == 2: #limit 2 #operar directamente en future
            try:    
                operarFuture = apiFtx.place_order(f"{currency}-{future}", typeO, 0, size, "market")
            except Exception as e:
                return {"status": "error", "msg": e}
            
        if typeLimitMarket == 3: #market
            #primero cierro la del futuro y luego vendo en spot 
            try:    
                operarFuture = apiFtx.place_order(f"{currency}-{future}", typeO, 0, size, "market")
            except Exception as e:
                return {"status": "error", "msg": e}
            try:    
                venderSpot = apiFtx.place_order(f"{currency}/USD", "sell", 0, size, "market")
            except Exception as e:
                return {"status": "error", "msg": e}
            
            
    if type_tasa == 2: 
        #tasa futuro / futuro 
        if typeLimitMarket == 1: #limit 1 #comprar spot en market 
            
            if typeO == "sell": 
                #hago un buy en future y un sell en future2
                try:    
                    operarFuture = apiFtx.place_order(f"{currency}-{future}", "buy", 0, size, "market")
                except Exception as e:
                    return {"status": "error", "msg": e}
                try:    
                    operarFuture2 = apiFtx.place_order(f"{currency}-{future2}", "sell", 0, size, "market")
                except Exception as e:
                    return {"status": "error", "msg": e}
            if typeO == "buy": 
                #hago un buy en future y un sell en future2
                try:    
                    operarFuture = apiFtx.place_order(f"{currency}-{future}", "sell", 0, size, "market")
                except Exception as e:
                    return {"status": "error", "msg": e}
                try:    
                    operarFuture2 = apiFtx.place_order(f"{currency}-{future2}", "buy", 0, size, "market")
                except Exception as e:
                    return {"status": "error", "msg": e}
            try:    
                venderSpot = apiFtx.place_order(f"{currency}/USD", "sell", 0, size, "market")
            except Exception as e:
                return {"status": "error", "msg": e}
  
        if typeLimitMarket == 2: #limit 2
            if typeO == "sell": 
                #hago un buy en future y un sell en future2
                try:    
                    operarFuture = apiFtx.place_order(f"{currency}-{future}", "buy", 0, size, "market")
                except Exception as e:
                    return {"status": "error", "msg": e}
                try:    
                    operarFuture2 = apiFtx.place_order(f"{currency}-{future2}", "sell", 0, size, "market")
                except Exception as e:
                    return {"status": "error", "msg": e}
            if typeO == "buy": 
                #hago un buy en future y un sell en future2
                try:    
                    operarFuture = apiFtx.place_order(f"{currency}-{future}", "sell", 0, size, "market")
                except Exception as e:
                    return {"status": "error", "msg": e}
                try:    
                    operarFuture2 = apiFtx.place_order(f"{currency}-{future2}", "buy", 0, size, "market")
                except Exception as e:
                    return {"status": "error", "msg": e}
        if typeLimitMarket == 3: # market 
            
            if typeO == "sell": 
                #hago un buy en future y un sell en future2
                try:    
                    operarFuture = apiFtx.place_order(f"{currency}-{future}", "buy", 0, size, "market")
                except Exception as e:
                    return {"status": "error", "msg": e}
                try:    
                    operarFuture2 = apiFtx.place_order(f"{currency}-{future2}", "sell", 0, size, "market")
                except Exception as e:
                    return {"status": "error", "msg": e}
            if typeO == "buy": 
                #hago un buy en future y un sell en future2
                try:    
                    operarFuture = apiFtx.place_order(f"{currency}-{future}", "sell", 0, size, "market")
                except Exception as e:
                    return {"status": "error", "msg": e}
                try:    
                    operarFuture2 = apiFtx.place_order(f"{currency}-{future2}", "buy", 0, size, "market")
                except Exception as e:
                    return {"status": "error", "msg": e}
            try:    
                venderSpot = apiFtx.place_order(f"{currency}/USD", "sell", 0, size, "market")
            except Exception as e:
                return {"status": "error", "msg": e}
    return {"status": "ok", "msg": "ordenes ejecutadas correctamente"}

def save_order(exchange,currency,nameRow, nameCol, market, size,  distance, type, side, status,  id_user, id_order, priceLimit, distanciaActual, typeTasa ):
    print("entrando a guardar orden")
    sql = f"""
    INSERT INTO fi_orders ( exchange, currency, nameRow	,nameCol,	market	,size	,distance,	type,	side	,status,	created,	updated,	id_user, id_order, price, typeTasa, distanciaInicial) 
    VALUES
    ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    tupla = (exchange,currency,nameRow, nameCol, market, size,  distance, type, side, status,  datetime.now(), datetime.now(), id_user, id_order, priceLimit , typeTasa, distanciaActual) 
    id_order = updateData(sql, tupla)
    return id_order



def armar_tasa_future(datosTasa, current_user_id, distanciaActual, nameRow, nameCol, type_tasa, currency,  typeLimitMarket, future, typeO, size, price, future2, clasicaInversa ):
    if type_tasa == 1: 
        if typeLimitMarket == 3:
            try:    
                operarFuture = apiFtx.place_order(f"{currency}-{future}", typeO, 0, size, "market")
                statusOrder = apiFtx.get_status_orden(str(operarFuture["id"]))
                print("statusOrder ", statusOrder)
                priceOrder = statusOrder["avgFillPrice"]
                save_order("ftx",currency,nameRow, nameCol, f"{currency}-{future}", size,  price, "market", typeO, 1,  current_user_id , operarFuture["id"], priceOrder, distanciaActual, clasicaInversa)
            except Exception as e:
                return {"status": "error", "msg": e}
        else:
            try:    
                print("entrando a ejecutar orden limit")
                #operarFuture = apiFtx.place_order(f"{currency}-{future}", typeO, price, size, "limit")
                #calcular limit future y hacer orden 
                distanciaRequerida = float(price) 
                priceLimit = 0
                if typeO == "sell":#es tasa clasica 
                    print("es type sell")
                    restaDistancias = distanciaRequerida - float(distanciaActual)
                    print("restaDistancias ", restaDistancias)
                    priceLimit = datosTasa["bidFuture"] * (1+restaDistancias)
                    print("priceLimit", priceLimit)
                else: 
                    restaDistancias = float(distanciaActual) - distanciaRequerida
                    priceLimit = datosTasa["askFuture"] * (1+restaDistancias)
                    priceLimit = priceLimit - datosTasa["askFuture"] 
                    priceLimit = datosTasa["askFuture"]  - priceLimit
                print("vamos a operar future")
                operarFuture = apiFtx.place_order(f"{currency}-{future}", typeO, priceLimit, size, "limit")
                print("operar future", operarFuture)
                save_order("ftx",currency,nameRow, nameCol, f"{currency}-{future}", size,  distanciaRequerida, "limit", typeO, 0,  current_user_id, operarFuture["id"],priceLimit , distanciaActual, clasicaInversa)
            except Exception as e:
                return {"status": "error", "msg": e}
    if type_tasa == 2: 
        if typeLimitMarket == 3: # market 
            if typeO == "sell": 
                #hago un buy en future y un sell en future2
                try:    
                    operarFuture = apiFtx.place_order(f"{currency}-{future}", "buy", 0, size, "market")
                except Exception as e:
                    return {"status": "error", "msg": e}
                try:    
                    operarFuture2 = apiFtx.place_order(f"{currency}-{future2}", "sell", 0, size, "market")
                    save_order("ftx",currency,nameRow, nameCol, f"{currency}-{future2}", size,  distanciaActual, "market", typeO, 1,  current_user_id, operarFuture2["id"] )
          
                except Exception as e:
                    return {"status": "error", "msg": e}
            if typeO == "buy": 
                #hago un buy en future y un sell en future2
                try:    
                    operarFuture = apiFtx.place_order(f"{currency}-{future}", "sell", 0, size, "market")
                except Exception as e:
                    return {"status": "error", "msg": e}
                try:    
                    operarFuture2 = apiFtx.place_order(f"{currency}-{future2}", "buy", 0, size, "market")
                    save_order("ftx",currency,nameRow, nameCol, f"{currency}-{future2}", size,  distanciaActual, "market", typeO, 1,  current_user_id , operarFuture2["id"])
                except Exception as e:
                    return {"status": "error", "msg": e}
        else:
            if typeO == "sell": 
                #hago un buy en future y un sell en future2
               # try:    
              #      operarFuture = apiFtx.place_order(f"{currency}-{future}", "buy", price, size, "limit")
              #  except Exception as e:
              #      return {"status": "error", "msg": e}
                try:    
                  #  operarFuture2 = apiFtx.place_order(f"{currency}-{future2}", "sell", price, size, "limit")
                    save_order("ftx",currency,nameRow, nameCol, f"{currency}-{future2}", size,  distanciaActual, "limit", typeO, 0,  current_user_id, 0 )
                except Exception as e:
                    return {"status": "error", "msg": e}
            if typeO == "buy": 
                #hago un buy en future y un sell en future2
              #  try:    
               #     operarFuture = apiFtx.place_order(f"{currency}-{future}", "sell", price, size, "limit")
               # except Exception as e:
               #     return {"status": "error", "msg": e}
                try:    
                 #   operarFuture2 = apiFtx.place_order(f"{currency}-{future2}", "buy", price, size, "limit")
                    save_order("ftx",currency,nameRow, nameCol, f"{currency}-{future2}", size,  distanciaActual, "limit", typeO, 0,  current_user_id, 0 )

                except Exception as e:
                    return {"status": "error", "msg": e}
                
    return {"status": "ok", "msg": "ordenes ejecutadas correctamente"}
    
@app.route('/api/make_order', methods=['POST'])
@jwt_required()
def make_order():
    current_user_id = get_jwt_identity()
    body = request.get_json()
    print("body", body)
    cierreApertura = 0 #apertura
    currency = body["currency"]
    datosTasa = {
        "bidFuture":  body["bidFuture"],
        "askFuture" : body["askFuture"],
        "bidSpot" : body["bidSpot"],
        "askSpot" : body["askSpot"]
    }
    nameFuture = body["future"]
    typeO = "sell"
    if body["type"]==0:
        typeO = "buy"
    posicionesAbiertas = apiFtx.get_position(nameFuture)
    if posicionesAbiertas and posicionesAbiertas["size"]>0:
        print("si hubo posiciones", posicionesAbiertas)
        #si hay posiciones verificar si voy a hacer un cierre o otra apertura 
        if typeO==posicionesAbiertas["side"]:
            print("es otra apertura")
        else:
            print("es un cierre")
            cierreApertura = 1
          
    else:
        print("no hubo posiciones")
    #verificar que sea spot o future
    type_tasa = 2
    nameRow = ""
    future = ""
    future2 = ""
    nameCol = str(body["future"])
    nameCol = nameCol.split("-")
    nameCol = nameCol[1]
    if "USD" in body["nameRow"]: 
        type_tasa = 1
        nameRow = str(body["nameRow"])
        nameRow = nameRow.split("/")
        nameRow = nameRow[1]
        future = nameCol
    else:
        nameRow = str(body["nameRow"])
        nameRow = nameRow.split("-")
        nameRow = nameRow[1]
        future = nameRow
        future2 = nameCol

    #crear tasa
    orden = []
    if type_tasa ==1:
        #lleva spot 
        print("es tasa con spot")
        if cierreApertura==0:
            print("es armado completo")
            #comprar spot 
            if body["limitMarket"]==3:
                comprar_spot =  apiFtx.place_order(f"{body['currency']}/USD", "buy", 0, body["size"],"market")
                print("comprar_spot ", comprar_spot)
                print("id order ", comprar_spot["id"])
                #recien se ejecuta no me dice el precio con el q se ejecutó asi q lo consulto 
                statusOrder = apiFtx.get_status_orden(str(comprar_spot["id"]))
                print("statusOrder ", statusOrder)
                priceOrder = statusOrder["avgFillPrice"]
                print("priceOrder spot ", priceOrder)
                save_order("ftx",currency,"", "", f"{body['currency']}/USD", body["size"],0, "market", "buy", 1,  current_user_id, comprar_spot["id"], priceOrder, body["distanciaActual"], 0)
            orden = armar_tasa_future(datosTasa, current_user_id, body["distanciaActual"], nameRow, nameCol, type_tasa, body["currency"], body["limitMarket"], future, typeO,body["size"], body["price"], future2, 0)
        else:
            print("es desarmado completo")
            #es cierre 
            orden = armar_tasa_future(datosTasa, current_user_id, body["distanciaActual"], nameRow, nameCol,type_tasa, body["currency"], body["limitMarket"], future, typeO,body["size"], body["price"], future2,1)
            if body["limitMarket"]==3:
                vender_spot =  apiFtx.place_order(f"{body['currency']}/USD", "sell", 0, body["size"],"market")
                #recien se ejecuta no me dice el precio con el q se ejecutó asi q lo consulto 
                statusOrder = apiFtx.get_status_orden(str(vender_spot["id"]))
                print("statusOrder ", statusOrder)
                priceOrder = statusOrder["avgFillPrice"]
                print("priceOrder spot ", priceOrder)
                save_order("ftx",currency,"", "", f"{body['currency']}/USD", body["size"],0, "market", "sell", 1,  current_user_id, vender_spot["id"], priceOrder, body["distanciaActual"], 1)
    else:
        print("es tasa futura")

      #  orden = armar_tasa_future(type_tasa, body["currency"], body["limitMarket"], future, typeO,body["size"], body["price"], future2)

    #print(body)
    return jsonify(orden)


@app.route('/api/history_orders', methods=['GET'])
@jwt_required()
def get_history_orders():
    current_user_id = get_jwt_identity()
    type = request.args.get('type', '')
    if type == "history":
        sql = f"""
        select * from fi_orders where id_user = %s and (status = 1  or status = 2) order by id desc
        """
        tupla = (current_user_id)
        orders = getData(sql, tupla)
        arrayHistory = []
        if orders:
            for x in orders:
                currency = x[2]
                row = ""
                col = x[5]
                description = ""
                if x[3]=="":
                    row = f"{currency} Spot"
                    description = row
                else: 
                    description = col
                
                #status 0=open 1=filled 2=canceled
                status = x[10]
                typeOrder = x[8]
                arrayHistory.append({
                    "id": x[0], 
                    "exchange": x[1],
                    "description": description, 
                    "status": status, 
                    "type": typeOrder, 
                    "size": x[6], 
                    "distance": x[7], 
                    "side": x[9],
                    "price": x[15],
                    "time": str(x[11])
                })

        return jsonify(arrayHistory)
    if type == "trade":
        sql = f"""
        select * from fi_orders where id_user = %s and status = 1 order by id desc
        """
        tupla = (current_user_id)
        orders = getData(sql, tupla)
        arrayHistory = []
        if orders:
            for x in orders:
                currency = x[2]
                row = ""
                col = x[5]
                description = ""
                if x[3]=="":
                    row = f"{currency} Spot"
                    description = row
                else: 
                    description = col
                #status 0=open 1=filled 2=canceled
                status = x[10]
                typeOrder = x[8]
                distancia = 0
                if typeOrder == "limit":
                    distancia = x[7]
                else: 
                    distancia = x[17]
                arrayHistory.append({
                    "id": x[0], 
                    "exchange": x[1],
                    "description": description, 
                    "status": status, 
                    "type": typeOrder, 
                    "size": x[6], 
                    "distance": distancia, 
                    "side": x[9], 
                    "price": x[15],
                    "time": str(x[11])
                })

        return jsonify(arrayHistory)
    if type == "open":
        sql = f"""
        select * from fi_orders where id_user = %s and status = 0
        """
        tupla = (current_user_id)
        orders = getData(sql, tupla)
        arrayHistory = []
        if orders:
            for x in orders:
                currency = x[2]
                row = ""
                col = x[5]
                if x[3]=="USD":
                    row = f"{currency} Spot"
                else: 
                    row = f"{currency}-{x[3]}"
                description = f"{row} / {col}"
                #status 0=open 1=filled 2=canceled
                status = x[10]
                typeOrder = x[8]
                arrayHistory.append({
                    "id": x[0], 
                    "exchange": x[1],
                    "description": description, 
                    "status": status, 
                    "type": typeOrder, 
                    "size": x[6], 
                    "distance": x[7], 
                    "side": x[9], 
                    "time": str(x[11])
                })

        return jsonify(arrayHistory)
    return 0