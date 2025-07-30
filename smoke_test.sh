#!/bin/bash
set -e # Stop if errors happen
trap 'echo "An error happened: "' ERR

echo 'Testing API'


response_1=$(curl -w "%{http_code}" -X POST http://localhost:8000/retrieve \
     -o temp_response.json\
     -H "Content-type:application/json"\
     -d '{"question":"Chương I điều 1 luật dân sự là gì?","top_k":5}')

http_code_1=$(tail -n1 <<< "$response_1")
if [ "$http_code_1" = "200" ]; then
    echo "API /retrieve thành công!"
    cat temp_response.json
else
    echo "Lỗi API /retrieve, mã phản hồi: $http_code_1"
    exit 1

response_2=$(curl -w "%{http_code}" -X POST http://localhost:8000/rag \
     -o temp_response.json\
     -H "Content-type:application/json"\
     -d '{"question":"Chương I điều 1 luật dân sự là gì?"}')
fi

http_code_2=$(tail -n1 <<< "$response_2")
if [ "$http_code_2" = "201" ]; then
    echo "API /rag thành công!"
    cat temp_response.json
else
    echo "Lỗi API /rag, mã phản hồi: $http_code_2"
    exit 2
fi
