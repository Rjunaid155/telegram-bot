const axios = require('axios');

const rpcUser = 'JunaidTahir1995';
const rpcPassword = 'R_junaid155';
const rpcPort = 8332;

async function getBlockchainInfo() {
  try {
    const response = await axios.post(
      "http://127.0.0.1:" + rpcPort, // ✅ Fixed: Concatenation without backticks
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

    console.log("✅ Blockchain Info:", response.data);
  } catch (error) {
    console.error("❌ Error:", error.message || error);
  }
}

getBlockchainInfo();