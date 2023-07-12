const WebSocket = require('ws');
const MongoClient = require('mongodb').MongoClient;

const url = 'ws://36.138.2.41:9873/api/websocket/connectServer/sim-gicc';
const mongoUrl = 'mongodb://localhost:27017/RSM';

const client = new MongoClient(mongoUrl);
client.connect(function(err) {
  if (err) {
    console.log(err);
    return;
  }
  console.log('Connected to MongoDB');

  const socket = new WebSocket(url);

  socket.on('message', function (data) {
    let rawData = JSON.parse(data);
    if (rawData.type !== 14) {
      return;
    }

    let collection = client.db().collection('data');
    collection.createIndex({ timestamp: 1 }, function(err, res) {
      if (err) {
        console.log(err);
        return;
      }
      console.log(`Created index for collection ${collection.collectionName}`);

      collection.insertOne(rawData.data, function(err, res) {
        if (err) {
          console.log(err);
          return;
        }
        console.log(`Inserted data ${rawData.data.timestamp}`);
      });
    });
  });

  socket.on('open', function () {
    console.log(`WebSocket连接成功 ${url}`);
  });

  socket.on('error', function (err) {
    console.log(`WebSocket发生错误 ${err.message}`);
  });

  socket.on('close', function () {
    console.log('WebSocket关闭');
  });
});