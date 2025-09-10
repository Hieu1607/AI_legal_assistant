#!/bin/bash
set -e # Stop if errors happen

echo 'Testing API'


response_1=$(curl -s -w "%{http_code}" -X POST http://localhost:8000/retrieve \
     -o temp_response.json\
     -H "Content-type:application/json"\
     -d '{"question":"Chương I điều 1 luật dân sự là gì?","top_k":5}')

http_code_1=$(tail -n1 <<< "$response_1")
if [ "$http_code_1" = "200" ]; then
    echo "API /retrieve thành công!"
    cat temp_response.json
else
    echo -e "\nLỗi API /retrieve, mã phản hồi: $http_code_1"
    exit 1
fi

response_2=$(curl -s -w "%{http_code}" -X POST http://localhost:8000/rag \
     -o temp_response.json\
     -H "Content-type:application/json"\
     -d '{"question":"Chương I điều 1 luật dân sự là gì?"}')

http_code_2=$(tail -n1 <<< "$response_2")
if [ "$http_code_2" = "200" ]; then
    echo -e "\nAPI /rag thành công!"
    cat temp_response.json
else
    echo -e "\nLỗi API /rag, mã phản hồi: $http_code_2"
    exit 2
fi

# Clean up temp file
rm -f temp_response.json

echo -e "\nTất cả smoke tests đã thành công!"
