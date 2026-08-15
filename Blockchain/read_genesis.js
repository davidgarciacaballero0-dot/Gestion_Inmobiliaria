const fs = require('fs');

try {
  const fileContent = fs.readFileSync('d:/HDD/DOCS/docs/Universidad/ING SOFTWARE 1/PROYECTO INMOBILIARIO/Blockchain/genesis.json', 'utf8');
  const data = JSON.parse(fileContent);

  const consortiums = data.data.data[0].payload.data.config.channel_group.groups.Consortiums;
  const org1 = consortiums.groups.SampleConsortium.groups.Org1MSP.policies;
  console.log("Genesis Org1MSP Policies:");
  console.log(JSON.stringify(org1, null, 2));
} catch (e) {
  console.error("Error reading policies:", e);
}
