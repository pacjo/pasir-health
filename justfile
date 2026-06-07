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
