default:
    just --list

clean:
    #!/usr/bin/env bash
    # TODO: make clean_gateway/cloud/... and then clean_all
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
    # generate random that will fit in randomSeed(unsigned long)
    RANDOM=$(shuf -i 0-4294967295 -n 1)
    cat << EOF > $IDENTITY_FILE
    #ifndef SENSOR_ID
    #define SENSOR_ID {{ sensor_id }}
    #define RANDOM_SEED $RANDOM
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

    # link sensor_id specific infile
    infile="../infiles/{{ sensor_id }}.txt"
    if [ -f "$infile" ]; then
        ln -s "$infile" infile.txt
    else
        echo "Warning: no infile found for sensor_id {{ sensor_id }}"
    fi

    # run emulino
    EBSimUnoEthCurses -ip 127.0.0.1 ../../.pio/build/uno/firmware.hex

    # destroy env
    cd ..
    rm -r {{ sensor_id }}

run_docker:
    docker compose up -d

run num_sensors: run_docker
    #!/usr/bin/env bash
    # everything else was started by just
    # finally we can run sensors
    for i in $(seq 1 {{ num_sensors }}); do
        just compile_sensor $i
        just run_sensor $i
    done
