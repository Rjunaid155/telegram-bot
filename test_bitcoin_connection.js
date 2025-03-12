const axios = require('axios');

const rpcUser = 'JunaidTahir1995';
const rpcPassword = 'R_junaid155';
const rpcPort = 8332;
const publicIp = '103.87.195.23'; // Tumhara public IP
const localIp = '127.0.0.1'; // Tumhara local IP

async function getBlockchainInfo(ip) {
  try {
    const response = await axios.post(
      "http://" + ip + ":" + rpcPort, // ✅ IP address ko dynamically use karo
      {
        jsonrpc: "1.0",
        id: "test",
        method: "getblockchaininfo",
        params: []
      },
      {
        auth: {
          username: rpcUser,
          password: rpcPassword
        },
        headers: { "Content-Type": "text/plain" }
      }
    );

    console.log("✅ Blockchain Info from " + ip + ":", response.data);
  } catch (error) {
    console.error("❌ Error from " + ip + ":", error.message || error);
  }
}

// Try both public and local IP addresses
getBlockchainInfo(publicIp);
getBlockchainInfo(localIp);
