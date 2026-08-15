# Guía de Despliegue: Red Blockchain Hyperledger Fabric Física 🔗

Esta carpeta contiene los blueprints y configuraciones listos para producción para desplegar una infraestructura física de **Hyperledger Fabric v2.4** y enlazarla con el middleware API Gateway en Node.js de la plataforma **Autogestión Inmobiliaria**.

---

## 🛠️ Requisitos Previos

Antes de levantar la red, asegúrate de tener instalado en tu sistema local/servidor:
1. **Docker y Docker Compose** (v2.0.0 o superior).
2. **Node.js** (v16 o v18) y **npm**.
3. **Binarios de Hyperledger Fabric v2.4.0** en tu PATH (especialmente `cryptogen` y `configtxgen`).
   * *Comando de descarga oficial:*
     ```bash
     curl -sSL https://bit.ly/2ysbOwt | bash -s -- 2.4.0 1.5.2
     ```

---

## 🚀 Paso a Paso para Iniciar la Red Física

### Paso 1: Generación de Credenciales Criptográficas (X.509)
Genera las carpetas MSP, claves privadas y certificados TLS para las organizaciones (`Org1` para Administración, `Org2` para Notaría/Reguladora y la entidad de ordenamiento `OrdererOrg`):
```bash
cryptogen generate --config=./crypto-config.yaml
```
*(Nota: Si no posees un `crypto-config.yaml` personalizado, puedes generarlo con plantillas estándar de Hyperledger o configurar la red usando Fabric CA).*

### Paso 2: Generar Bloque Génesis del Canal
Crea la carpeta para el bloque de inicio y compílalo usando el perfil definido en `configtx.yaml`:
```bash
mkdir system-genesis-block
configtxgen -profile TwoOrgsChannelProfile -channelID autogestion-channel -outputBlock ./system-genesis-block/genesis.block
```

### Paso 3: Levantar los Nodos de la Red en Docker
Inicia los Peer nodes de Org1 y Org2, el Orderer Raft, y el contenedor de administración CLI:
```bash
docker-compose -f docker-compose-base.yaml up -d
```
Verifica que todos estén corriendo con:
```bash
docker ps
```

### Paso 4: Crear y Unir el Canal
Entra al contenedor CLI para realizar la configuración inicial del canal:
```bash
docker exec -it cli bash
```
Una vez dentro, ejecuta para crear el canal y unir los peers:
```bash
# Crear Canal
peer channel create -o orderer.autogestion.com:7050 -c autogestion-channel -f ./system-genesis-block/genesis.block --tls --cafile $ORDERER_CA

# Unir Peer 0 de Org 1
peer channel join -b autogestion-channel.block

# (Opcional) Cambia las variables de entorno de MSP a Org2 para unir su respectivo peer.
```

### Paso 5: Instalar y Desplegar el Chaincode
Ejecuta el script de ciclo de vida del Smart Contract para empaquetar e instalar el Chaincode escrito en JavaScript (`chaincode.js`):
```bash
chmod +x scripts/deploy-chaincode.sh
./scripts/deploy-chaincode.sh
```

---

## 🔌 Conexión con la API Gateway (Modo Producción)

Una vez que la red física esté activa en Docker, puedes desactivar el **Modo Simulación** en la API Gateway para que empiece a interactuar con los nodos reales vía **gRPC seguro**.

### 1. Modificar el archivo `.env` de la carpeta principal `/Blockchain`:
Edita el archivo `d:\Gestion 1-2026\Software 1\Proyecto\Blockchain\.env` de la siguiente forma:
```env
PORT=4000
SIMULATE_BLOCKCHAIN=false
PEER_ENDPOINT=localhost:7051
PEER_MSPID=Org1MSP
CHANNEL_NAME=autogestion-channel
CHAINCODE_NAME=autogestion

# Rutas a las credenciales generadas en el Paso 1
CONNECTION_PROFILE_PATH=./fabric-network/connection-org1.json
WALLET_PATH=./wallet
```

### 2. Formato de Connection Profile (connection-org1.json)
Crea un perfil de conexión gRPC que describa cómo la API de Node.js debe enrutarse hacia el peer local:
```json
{
  "name": "autogestion-network-org1",
  "version": "1.0.0",
  "client": {
    "organization": "Org1"
  },
  "organizations": {
    "Org1": {
      "mspid": "Org1MSP",
      "peers": ["peer0.org1.autogestion.com"]
    }
  },
  "peers": {
    "peer0.org1.autogestion.com": {
      "url": "grpcs://localhost:7051",
      "tlsCACerts": {
        "path": "./fabric-network/crypto-config/peerOrganizations/org1.autogestion.com/peers/peer0.org1.autogestion.com/tls/ca.crt"
      }
    }
  }
}
```

### 3. Reiniciar la API Gateway
Detén e inicia nuevamente el servicio para que cargue la configuración real de Hyperledger:
```bash
npm run start
```
Si la conexión gRPC se establece exitosamente contra el puerto 7051 de Docker, verás en consola:
`📢 MODO DE OPERACIÓN: 🔗 PRODUCTION (Fabric peer)`

---

🔒 **¡Listo!** A partir de este momento, cada acción en el backend de Django gatillará firmas criptográficas X.509 de las partes y registrará bloques inmutables en la red física real de Hyperledger Fabric. Los usuarios visualizarán la traza inmutable en tiempo real en la interfaz de React.
