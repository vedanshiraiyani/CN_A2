configurations=(
  "--nagle --delayed_ack"
  "--nagle"
  "--delayed_ack"
  ""
)

for config in "${configurations[@]}"; do
  echo "Running configuration: $config"
  python Q3_server.py $config &
  server_pid=$!
  sleep 1
  python Q3_client.py $config
  wait $server_pid
  echo "Configuration finished."
  echo "-------------------------"
done

echo "All configurations finished."