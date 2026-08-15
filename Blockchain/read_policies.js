const fs = require('fs');

try {
  const fileContent = fs.readFileSync('d:/HDD/DOCS/docs/Universidad/ING SOFTWARE 1/PROYECTO INMOBILIARIO/Blockchain/config_block.json', 'utf8');
  const data = JSON.parse(fileContent);

  const org1 = data.data.data[0].payload.data.config.channel_group.groups.Application.groups.Org1MSP.policies;
  console.log("Org1MSP Policies:");
  console.log(JSON.stringify(org1, null, 2));

  const org2 = data.data.data[0].payload.data.config.channel_group.groups.Application.groups.Org2MSP.policies;
  console.log("\nOrg2MSP Policies:");
  console.log(JSON.stringify(org2, null, 2));
} catch (e) {
  console.error("Error reading policies:", e);
}
