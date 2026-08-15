#!/bin/bash
# ==============================================================================
#  deploy-chaincode.sh - Fabric chaincode lifecycle management script (V2)
# ==============================================================================

export CC_NAME="autogestion"
export CC_VERSION="5.0"
export CC_SEQUENCE="1"
export CHANNEL_NAME="autogestion-channel"
export ORDERER_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto-config/ordererOrganizations/autogestion.com/orderers/orderer.autogestion.com/msp/tlscacerts/tlsca.autogestion.com-cert.pem

echo "========================================="
echo "📦 Packaging smart contract (Node.js)..."
echo "========================================="
peer lifecycle chaincode package ${CC_NAME}.tar.gz \
  --path /opt/gopath/src/github.com/chaincode/ \
  --lang node \
  --label ${CC_NAME}_${CC_VERSION}

echo "========================================="
echo "📥 Installing chaincode on Peer 0 - Org 1..."
echo "========================================="
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto-config/peerOrganizations/org1.autogestion.com/peers/peer0.org1.autogestion.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto-config/peerOrganizations/org1.autogestion.com/users/Admin@org1.autogestion.com/msp
export CORE_PEER_ADDRESS=peer0.org1.autogestion.com:7051
peer lifecycle chaincode install ${CC_NAME}.tar.gz

# Extract package ID for approvals
export CC_PACKAGE_ID=$(peer lifecycle chaincode calculatepackageid ${CC_NAME}.tar.gz)
echo "Chaincode Package ID: ${CC_PACKAGE_ID}"

echo "========================================="
echo "✍️ Approving chaincode definition for Org 1..."
echo "========================================="
peer lifecycle chaincode approveformyorg -o orderer.autogestion.com:7050 \
  --ordererTLSHostnameOverride orderer.autogestion.com \
  --channelID ${CHANNEL_NAME} \
  --name ${CC_NAME} \
  --version ${CC_VERSION} \
  --package-id ${CC_PACKAGE_ID} \
  --sequence ${CC_SEQUENCE} \
  --tls \
  --cafile ${ORDERER_CA}

echo "========================================="
echo "📥 Installing chaincode on Peer 0 - Org 2..."
echo "========================================="
export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto-config/peerOrganizations/org2.autogestion.com/peers/peer0.org2.autogestion.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto-config/peerOrganizations/org2.autogestion.com/users/Admin@org2.autogestion.com/msp
export CORE_PEER_ADDRESS=peer0.org2.autogestion.com:9051
peer lifecycle chaincode install ${CC_NAME}.tar.gz

echo "========================================="
echo "✍️ Approving chaincode definition for Org 2..."
echo "========================================="
peer lifecycle chaincode approveformyorg -o orderer.autogestion.com:7050 \
  --ordererTLSHostnameOverride orderer.autogestion.com \
  --channelID ${CHANNEL_NAME} \
  --name ${CC_NAME} \
  --version ${CC_VERSION} \
  --package-id ${CC_PACKAGE_ID} \
  --sequence ${CC_SEQUENCE} \
  --tls \
  --cafile ${ORDERER_CA}

echo "========================================="
echo "🚀 Committing chaincode to channel: ${CHANNEL_NAME}..."
echo "========================================="
peer lifecycle chaincode commit -o orderer.autogestion.com:7050 \
  --ordererTLSHostnameOverride orderer.autogestion.com \
  --channelID ${CHANNEL_NAME} \
  --name ${CC_NAME} \
  --version ${CC_VERSION} \
  --sequence ${CC_SEQUENCE} \
  --tls \
  --cafile ${ORDERER_CA} \
  --peerAddresses peer0.org1.autogestion.com:7051 \
  --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto-config/peerOrganizations/org1.autogestion.com/peers/peer0.org1.autogestion.com/tls/ca.crt \
  --peerAddresses peer0.org2.autogestion.com:9051 \
  --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto-config/peerOrganizations/org2.autogestion.com/peers/peer0.org2.autogestion.com/tls/ca.crt

echo "✅ Smart Contract desplegado con éxito!"
