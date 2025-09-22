# Prometheus Dockerfile
FROM prom/prometheus:v2.45.0

# Copy configuration file
COPY prometheus.yml /etc/prometheus/prometheus.yml

# Expose port 9090
EXPOSE 9090

# Set user to prometheus
USER nobody

# Command to run Prometheus
CMD ["--config.file=/etc/prometheus/prometheus.yml", \
     "--storage.tsdb.path=/prometheus", \
     "--web.console.libraries=/etc/prometheus/console_libraries", \
     "--web.console.templates=/etc/prometheus/consoles", \
     "--storage.tsdb.retention.time=200h", \
     "--web.enable-lifecycle", \
     "--web.enable-admin-api"]