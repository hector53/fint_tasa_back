from modulos.client import FtxWebsocketClient
from app.modules import register_user, getDataOne, updateData, getData, insert_data
"""
aqui vamos a mantener una conexion activa a los websockets de xrp spot y future 
vamos a consultar en la base de datos las ordenes limit activas 
esa orden limit debe existir en ftx en este caso 
esa orden limit se va ejecutar a una distancia en especifica 
tenemos q ir actualizando esa orden referente a la distancia 
esta es la formula para sacar el limit futuro 
entonces seria. 
distancia actual = 0.99517 
bid future actual = 0.4542
ask spot actual  = 0.4564 
distancia requerida = 0.99817
distancia = 0.99817 - 0.99517 = 0.003
precio limit para distancia requerida = fut bid (0.4542) * (1+distancia(0.003)) = 0.45556
entonces la orden limit la hago con 0.45556

"""
ins = FtxWebsocketClient()
ins._api_key = "wCwAFYoRVc6RX8TnkleJz7f4p_fBQachaM1EmPNL"
ins._secret_key = "nn8ad37ZNzP79GF9EEYG7gkT9rGV9"
ticker1 = "XRP/USD"
ticker2 = "XRP-PERP"
ticker3 = "XRP-1230"
ins.get_ticker(ticker1)
ins.get_ticker(ticker2)
ins.get_ticker(ticker3)

#buscar en la db ordenes activas 
while True: 
    sql = f"""
    select * from fi_orders where status = %s
    """
    tupla = (0)
    getOrders = getData(sql, tupla)
    if getOrders: 
        print("si hay ordenes ")
        for x in getOrders:
            print("order: ",x)
 #   while True: 
     #   if len(ins._tickers[ticker2])>0 and len(ins._tickers[ticker1])>0 and len(ins._tickers[ticker3])>0:
       #     print(ticker1, ins._tickers[ticker1])
         #   print(ticker2, ins._tickers[ticker2])
            #print(ticker3, ins._tickers[ticker3])
