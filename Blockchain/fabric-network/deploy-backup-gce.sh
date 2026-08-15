#!/bin/bash
# ==============================================================================
#  deploy-backup-gce.sh - Levantar red de respaldo en Compute Engine (Docker Compose)
# ==============================================================================

# Detener el script ante cualquier fallo
set -e

# 1. Asegurar dependencias de Docker y Docker Compose
if ! command -v docker &> /dev/null; then
    echo "🐳 Instalando Docker..."
    sudo apt-get update
    sudo apt-get install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
fi

if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Instalando Docker Compose..."
    sudo apt-get update
    sudo apt-get install -y docker-compose
fi

# Agregar usuario al grupo docker si es necesario
if ! groups $USER | grep &>/dev/null '\bdocker\b'; then
    sudo usermod -aG docker $USER
    echo "⚠️ Usuario agregado al grupo docker. Se requiere volver a iniciar sesión para aplicar."
fi

# 2. Limpiar y crear la carpeta del bloque génesis en el host para evitar mounts erróneos de Docker
echo "🧹 Limpiando y creando carpeta del bloque génesis en el host..."
sudo rm -rf system-genesis-block
mkdir -p system-genesis-block
sudo rm -f autogestion-channel.tx autogestion-channel.block

# 3. Generar el bloque génesis de ordenamiento (system-channel) usando un contenedor temporal
echo "📦 Generando el bloque génesis de ordenamiento (system-channel)..."
sudo docker run --rm \
  -v "$(pwd)":/workspace \
  -w /workspace \
  -e FABRIC_CFG_PATH=/workspace \
  hyperledger/fabric-tools:2.4.0 \
  configtxgen -profile TwoOrgsOrdererGenesis -channelID system-channel -outputBlock ./system-genesis-block/genesis.block

echo "📦 Generando la transacción de creación del canal autogestion-channel..."
sudo docker run --rm \
  -v "$(pwd)":/workspace \
  -w /workspace \
  -e FABRIC_CFG_PATH=/workspace \
  hyperledger/fabric-tools:2.4.0 \
  configtxgen -profile TwoOrgsChannelProfile -channelID autogestion-channel -outputCreateChannelTx ./autogestion-channel.tx

# 4. Levantar la infraestructura base de Fabric en segundo plano
echo "🚀 Levantando nodos de Hyperledger Fabric..."
sudo docker-compose -f docker-compose-base.yaml down -v
sudo docker-compose -f docker-compose-base.yaml up -d

# Esperar unos segundos a que los contenedores arranquen
echo "⏳ Esperando 15 segundos a que los nodos inicien..."
sleep 15

# 5. Crear el canal
echo "🏗️ Creando el canal autogestion-channel..."
sudo docker exec -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto-config/peerOrganizations/org1.autogestion.com/users/Admin@org1.autogestion.com/msp \
            cli peer channel create -o orderer.autogestion.com:7050 -c autogestion-channel -f ./autogestion-channel.tx --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto-config/ordererOrganizations/autogestion.com/orderers/orderer.autogestion.com/msp/tlscacerts/tlsca.autogestion.com-cert.pem

# 5. Unir los peers al canal
echo "🔗 Uniendo Peer0 de Org1 al canal..."
sudo docker exec -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto-config/peerOrganizations/org1.autogestion.com/users/Admin@org1.autogestion.com/msp \
            cli peer channel join -b autogestion-channel.block

echo "🔗 Uniendo Peer0 de Org2 al canal..."
sudo docker exec -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto-config/peerOrganizations/org2.autogestion.com/users/Admin@org2.autogestion.com/msp \
            -e CORE_PEER_ADDRESS=peer0.org2.autogestion.com:9051 \
            -e CORE_PEER_LOCALMSPID="Org2MSP" \
            -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto-config/peerOrganizations/org2.autogestion.com/peers/peer0.org2.autogestion.com/tls/ca.crt \
            cli peer channel join -b autogestion-channel.block

# 6. Ejecutar despliegue de Chaincode (v5.0) en Docker Compose
echo "🚀 Desplegando el Smart Contract (Chaincode v5.0)..."
sudo docker exec -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto-config/peerOrganizations/org1.autogestion.com/users/Admin@org1.autogestion.com/msp \
            cli /bin/bash ./scripts/deploy-chaincode.sh

echo "✅ ¡Red Blockchain de Respaldo GCE lista y operativa!"

