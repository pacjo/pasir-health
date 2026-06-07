default:
    just --list

clean:
    rm -rf gateway/src/generated

generate_protobuf:
    #!/usr/bin/env bash
    if [ ! -d gateway/src/generated ]; then
        mkdir -p gateway/src/generated
    fi

    for file in $(find shared/protobuf -name "*.proto")
    do
        protoc --proto_path=shared/protobuf --python_out=gateway/src/generated $file
    done

    # ensure the generated directory is a proper Python package
    touch gateway/src/generated/__init__.py

[working-directory('./sensor')]
compile_sensor sensor_id:
    #!/usr/bin/env bash
    IDENTITY_FILE=src/identity.h
    cat << EOF > $IDENTITY_FILE
    #ifndef SENSOR_ID
    #define SENSOR_ID {{ sensor_id }}
    #endif
    EOF
    pio run
    rm $IDENTITY_FILE

[working-directory('./sensor')]
run_sensor sensor_id:
    #!/usr/bin/env bash
    # create execution env
    cd ./misc
    mkdir {{ sensor_id }}
    cd {{ sensor_id }}
    for file in ../*; do
        [ -f "$file" ] && ln -s "$file" .
    done

    # run emulino
    EBSimUnoEthCurses -ip 127.0.0.1 ../../.pio/build/uno/firmware.hex

    # destroy env
    cd ..
    rm -r {{ sensor_id }}
