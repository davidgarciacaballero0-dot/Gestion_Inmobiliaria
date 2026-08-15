import json

with open("d:/HDD/DOCS/docs/Universidad/ING SOFTWARE 1/PROYECTO INMOBILIARIO/Blockchain/config_block.json") as f:
    data = json.load(f)

try:
    org1_policies = data['data']['data'][0]['payload']['data']['config']['channel_group']['groups']['Application']['groups']['Org1MSP']['policies']
    print("Org1MSP Policies:")
    print(json.dumps(org1_policies, indent=2))
except Exception as e:
    print("Error reading Org1MSP policies:", e)

try:
    org2_policies = data['data']['data'][0]['payload']['data']['config']['channel_group']['groups']['Application']['groups']['Org2MSP']['policies']
    print("\nOrg2MSP Policies:")
    print(json.dumps(org2_policies, indent=2))
except Exception as e:
    print("Error reading Org2MSP policies:", e)
