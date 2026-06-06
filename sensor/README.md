# Sensor/IoT Node

Simple sensor written in c++. It sends data from analogpins in an interval that depends on the message type. To complie it, use the following command:
``` sh
arduino-cli compile -b arduino:avr:uno --build-property "build.extra_flags=-DUSER_ID=9876" --output-dir sensor/build sensor/sensor.ino
```
Where -DUSER_ID is a variable that can be changed, to show the users identity.
