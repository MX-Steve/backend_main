#!/bin/bash
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
function check_python() {  
    mkdir -p ${ROOT_DIR}/build/python
    python3 -m venv ${ROOT_DIR}/build/python
    source ${ROOT_DIR}/build/python/bin/activate
    pip3 install -e '.[dev]'
    mkdir -p ${ROOT_DIR}/backend/proto
    python setup.py gen_grpc -o ${ROOT_DIR}/backend/proto
	output=$(pylint --rcfile=${ROOT_DIR}/.pylintrc --persistent=n $(git ls-files '*.py'))
    if [ $? -ne 0 ]; then
        echo "pylint error:" >> $ROOT_DIR/.code-comment
        printf "%s\n" "${output}" >> $ROOT_DIR/.code-comment
        exit 1
    fi
}
cd ${ROOT_DIR}
check_python