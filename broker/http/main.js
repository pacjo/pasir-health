var host = "localhost"; //MQTT broker hostname or IP address
var port = 9001; //MQTT WebSocket TCP port
var topic = "#"; //Temat subskrybowanych wiadomości
var reconnectTimeout = 2000;
var mqtt;

function MQTTconnect() {
  if (typeof path == "undefined") {
    path = "/mqtt"; //obiekt zdefionowany niedbale (bez var czy let)
  }
  mqtt = new Paho.MQTT.Client(
    host,
    port,
    path,
    "web_" + parseInt(Math.random() * 100, 10),
  );
  var options = {
    timeout: 3,
    userName: "webuser",
    password: "webpassword",
    onSuccess: onConnect,
  };
  mqtt.onConnectionLost = onConnectionLost;
  mqtt.onMessageArrived = onMessageArrived;
  mqtt.connect(options);
}

function onConnect() {
  $("#status").val("Connected to " + host + ":" + port + path);
  mqtt.subscribe(topic, { qos: 0 });
  $("#topic").val(topic);
}

function onConnectionLost(response) {
  setTimeout(MQTTconnect, reconnectTimeout);
  $("#status").val(
    "connection lost: " + response.errorMessage + ". Reconnecting",
  );
}
function onMessageArrived(message) {
  var topic = message.destinationName;
  var payload = message.payloadString;
  $("#ws").prepend("<li>" + topic + " = " + payload + "</li>");
}

alarm = document.getElementById("alarm");
pause = document.getElementById("pause");

var control_topic = "web/control";

alarm.addEventListener("click", function () {
  mqtt.send(control_topic, "alarm");
  console.log("alarm");
  alarm.textContent = "Alarm";
  alarm.style.opacity = 1;
});

pause.addEventListener("click", function () {
  mqtt.send(control_topic, "nevermind");
  console.log("nevermind");
  pause.textContent = "Pause";
  pause.style.opacity = 1;
});

MQTTconnect();
