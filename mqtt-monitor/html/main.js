// var host = "broker"; // use docker dns
var host = "192.168.122.97"; // TODO: for testing, remove
var port = 9001;

var mqtt;
var connected = false;
var reconnectTimeout = 2000;
var maxLogRows = 200;

function connect() {
  // TODO: understand
  var clientId = "monitor_" + Math.random().toString(16).substring(2, 10);

  mqtt = new Paho.MQTT.Client(host, port, clientId);
  mqtt.onConnectionLost = onConnectionLost;
  mqtt.onMessageArrived = onMessageArrived;

  var options = {
    timeout: 5,
    keepAliveInterval: 30,
    cleanSession: true,
    onSuccess: onConnect,
    onFailure: onConnectFailure,
  };

  console.log("connecting to " + host + ":" + port);
  mqtt.connect(options);
}

// callbacks
function onConnect() {
  connected = true;
  console.log("connected");

  // subscribe to all $SYS topics
  mqtt.subscribe("$SYS/#", { qos: 0 });
}

function onConnectFailure(response) {
  connected = false;
  console.log("connection failed: " + response.errorMessage);
}

function onConnectionLost(response) {
  connected = false;
  console.log("connection lost: " + response.errorMessage);
  console.log("reconnecting...");
  setTimeout(function () {
    if (!connected) {
      connect();
    }
  }, reconnectTimeout);
}

function onMessageArrived(message) {
  var topic = message.destinationName;
  var payload = message.payloadString;

  updateLogs(topic, payload);
  updateMetrics(topic, payload);
}

// mertics
var metrics = {};
function updateMetrics(topic, payload) {
  metrics[topic] = payload;

  // based on: https://mosquitto.org/man/mosquitto-8.html
  switch (topic) {
    // broker info
    case "$SYS/broker/version":
      $("#brokerVersion").text(payload);
      break;

    case "$SYS/broker/uptime":
      $("#uptimeValue").text(formatUptime(payload));
      break;

    // clients
    case "$SYS/broker/clients/connected":
    case "$SYS/broker/clients/active":
      $("#clientsConnected").text(payload);
      break;
    case "$SYS/broker/clients/maximum":
      $("#clientsMax").text(payload);
      break;
    case "$SYS/broker/clients/total":
      $("#clientsTotal").text(payload);
      break;

    // messages
    case "$SYS/broker/messages/received":
      $("#msgsReceived").text(formatNumber(payload));
      break;
    case "$SYS/broker/messages/sent":
      $("#msgsSent").text(formatNumber(payload));
      break;
    case "$SYS/broker/messages/stored":
      $("#msgsStored").text(formatNumber(payload));
      break;

    // subscriptions
    case "$SYS/broker/subscriptions/count":
      $("#subsCount").text(payload);
      break;

    // bytes
    case "$SYS/broker/bytes/received":
      $("#bytesReceived").text(formatBytes(payload));
      break;
    case "$SYS/broker/bytes/sent":
      $("#bytesSent").text(formatBytes(payload));
      break;

    // heap mem
    case "$SYS/broker/heap/current":
      $("#heapCurrent").text(formatBytes(payload));
      break;
    case "$SYS/broker/heap/maximum":
      $("#heapMax").text(formatBytes(payload));
      break;

    // load/*
    // TODO: add a dropdown with time interval selection
    case "$SYS/broker/load/messages/received/1min":
      $("#loadMsgsRecv").text(payload);
      break;
    case "$SYS/broker/load/messages/sent/1min":
      $("#loadMsgsSent").text(payload);
      break;
    case "$SYS/broker/load/bytes/received/1min":
      $("#loadBytesRecv").text(payload);
      break;
    case "$SYS/broker/load/bytes/sent/1min":
      $("#loadBytesSent").text(payload);
      break;
    case "$SYS/broker/load/publish/received/1min":
      $("#loadPubRecv").text(payload);
      break;
    case "$SYS/broker/load/publish/sent/1min":
      $("#loadPubSent").text(payload);
      break;
    case "$SYS/broker/load/publish/dropped/1min":
      $("#loadPubDrop").text(payload);
      break;
    case "$SYS/broker/load/connections/1min":
      $("#loadConns").text(payload);
      break;
    case "$SYS/broker/load/sockets/1min":
      $("#loadSocks").text(payload);
      break;
  }
}

// logs
function updateLogs(topic, payload) {
  // if we're updating, then we have something
  // hide the empty state and show the table
  $("#logEmpty").hide();
  $("#logTable").show();

  var now = new Date();
  var ts =
    now.toTimeString().split(" ")[0] +
    "." +
    String(now.getMilliseconds()).padStart(3, "0");

  // this beauty is the fault of the formatter
  // I'm blaming Prettier.
  var row =
    "<tr>" +
    "<td>" +
    ts +
    "</td>" +
    "<td class='topic-cell' title='" +
    topic +
    "'>" +
    topic +
    "</td>" +
    "<td class='payload-cell'>" +
    payload +
    "</td>" +
    "</tr>";

  $("#logBody").prepend(row);

  // remove old messages
  var rows = $("#logBody tr");
  while (rows.length > maxLogRows) {
    rows.last().remove();
    rows = $("#logBody tr");
  }
}

// utils
function formatUptime(seconds) {
  var s = parseInt(seconds, 10);
  if (isNaN(s)) return seconds;

  var days = Math.floor(s / 86400);
  var hours = Math.floor((s % 86400) / 3600);
  var mins = Math.floor((s % 3600) / 60);
  var secs = s % 60;

  var parts = [];
  if (days > 0) parts.push(days + "d");
  if (hours > 0) parts.push(hours + "h");
  if (mins > 0) parts.push(mins + "m");
  parts.push(secs + "s");
  return parts.join(" ");
}

function formatNumber(n) {
  var num = parseInt(n, 10);
  if (isNaN(num)) return n;
  if (num >= 1e6) return (num / 1e6).toFixed(1) + "M";
  if (num >= 1e3) return (num / 1e3).toFixed(1) + "K";
  return num.toString();
}

function formatBytes(n) {
  var num = parseInt(n, 10);
  if (isNaN(num)) return n;
  if (num >= 1e9) return (num / 1e9).toFixed(2) + " GB";
  if (num >= 1e6) return (num / 1e6).toFixed(2) + " MB";
  if (num >= 1e3) return (num / 1e3).toFixed(1) + " KB";
  return num + " B";
}

// auto-connect on page load
$(document).ready(function () {
  connect();
});
